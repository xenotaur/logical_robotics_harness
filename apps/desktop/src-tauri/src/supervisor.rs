//! Owned-backend supervisor for the LRH desktop server protocol (version 1).
//!
//! This is the native parent side of `docs/reference/desktop-server-protocol.md`,
//! following the same rules as the Python reference supervisor
//! (`src/lrh/desktop_supervisor.py`):
//!
//! - spawn one child from an explicitly configured program and hold its
//!   stdin/stdout pipes privately;
//! - send one `start` request with a fresh launch ID and an explicit workspace;
//! - accept only a verified `ready` handshake as proof of a usable server;
//! - stop by `shutdown` message, escalating only against the owned child
//!   handle, never by process name, port, or HTTP route.
//!
//! [`Supervisor`] serializes Start, Stop, and Restart for at most one owned
//! child. [`OwnedServer`] is one launch. There is no UI here; the desktop shell
//! drives this module.

use std::collections::VecDeque;
use std::ffi::OsString;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use serde_json::{json, Value};

/// Protocol name carried in every message envelope.
pub const PROTOCOL_NAME: &str = "lrh-desktop-server";
/// The single protocol version this supervisor speaks.
pub const PROTOCOL_VERSION: u64 = 1;
/// Maximum message size in bytes, including the trailing newline.
pub const MAX_MESSAGE_BYTES: usize = 65_536;
/// Spawn → `ready`/`failed` budget.
pub const DEFAULT_STARTUP_TIMEOUT: Duration = Duration::from_secs(20);
/// `shutdown` → process exit budget before terminating.
pub const DEFAULT_SHUTDOWN_TIMEOUT: Duration = Duration::from_secs(10);
/// Terminate → process exit budget before killing.
pub const DEFAULT_TERMINATE_TIMEOUT: Duration = Duration::from_secs(5);
/// Bytes of child stderr kept for diagnostics.
pub const STDERR_TAIL_BYTES: usize = 64 * 1024;

const EXIT_POLL_INTERVAL: Duration = Duration::from_millis(20);
const HANDSHAKE_POLL_INTERVAL: Duration = Duration::from_millis(100);
const LOOPBACK_HOSTS: [&str; 2] = ["127.0.0.1", "::1"];

/// Lifecycle state of the one supervised server.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum State {
    Stopped,
    Starting,
    Running,
    Stopping,
    Failed,
}

/// Stable machine-readable failure categories.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorKind {
    /// The configured program could not be started.
    SpawnFailed,
    /// No handshake arrived within the startup budget.
    StartupTimeout,
    /// The child exited, or closed stdout, before a handshake.
    ExitedBeforeReady,
    /// The child exited on its own while running.
    ExitedUnexpectedly,
    /// The child reported `failed`; see [`SupervisorError::backend_error`].
    BackendFailed,
    /// Wrong protocol name or version; show an incompatible backend.
    IncompatibleBackend,
    /// The child answered for a different launch.
    LaunchIdMismatch,
    /// The reported workspace is not the one requested.
    WorkspaceMismatch,
    /// The reported endpoint is not a loopback address.
    NonLoopbackEndpoint,
    /// The child wrote something that is not a valid protocol message.
    MalformedHandshake,
    /// This launch was already used; create a new one.
    AlreadyLaunched,
    /// The private channel failed after `ready`.
    ChannelFailed,
}

impl ErrorKind {
    /// The snake_case code used in logs and the reference supervisor.
    pub fn code(self) -> &'static str {
        match self {
            ErrorKind::SpawnFailed => "spawn_failed",
            ErrorKind::StartupTimeout => "startup_timeout",
            ErrorKind::ExitedBeforeReady => "exited_before_ready",
            ErrorKind::ExitedUnexpectedly => "exited_unexpectedly",
            ErrorKind::BackendFailed => "backend_failed",
            ErrorKind::IncompatibleBackend => "incompatible_backend",
            ErrorKind::LaunchIdMismatch => "launch_id_mismatch",
            ErrorKind::WorkspaceMismatch => "workspace_mismatch",
            ErrorKind::NonLoopbackEndpoint => "non_loopback_endpoint",
            ErrorKind::MalformedHandshake => "malformed_handshake",
            ErrorKind::AlreadyLaunched => "already_launched",
            ErrorKind::ChannelFailed => "channel_failed",
        }
    }
}

/// A supervisor-side failure. It never carries environment variables.
#[derive(Debug, Clone, PartialEq)]
pub struct SupervisorError {
    pub kind: ErrorKind,
    pub message: String,
    /// The backend's `error` object, for [`ErrorKind::BackendFailed`] and
    /// incompatible-version failures reported by the child.
    pub backend_error: Option<Value>,
    pub exit_code: Option<i32>,
    /// Bounded tail of the child's stderr (it may contain local paths).
    pub stderr_tail: String,
}

impl SupervisorError {
    fn new(kind: ErrorKind, message: impl Into<String>) -> Self {
        SupervisorError {
            kind,
            message: message.into(),
            backend_error: None,
            exit_code: None,
            stderr_tail: String::new(),
        }
    }
}

impl std::fmt::Display for SupervisorError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.kind.code(), self.message)
    }
}

impl std::error::Error for SupervisorError {}

/// A verified `ready` handshake.
#[derive(Debug, Clone, PartialEq)]
pub struct Handshake {
    pub launch_id: String,
    /// Increments per launch of one [`Supervisor`]; compare with
    /// [`Supervisor::is_current`] to reject callbacks from an earlier launch.
    pub generation: u64,
    pub protocol_version: u64,
    pub backend: Value,
    pub pid: Option<i64>,
    pub workspace: Value,
    pub host: String,
    pub port: u16,
    pub url: String,
}

/// How an owned child was stopped.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Escalation {
    /// It exited after `shutdown` or stdin closure.
    None,
    /// It needed SIGTERM (or the platform equivalent).
    Terminate,
    /// It needed a kill.
    Kill,
}

/// How an owned child ended.
#[derive(Debug, Clone, PartialEq)]
pub struct StopResult {
    pub exit_code: Option<i32>,
    pub escalation: Escalation,
    /// The `reason` from the child's `stopped` message, if it sent one.
    pub reason: Option<String>,
}

/// What to launch and how long to wait. Every path is explicit; nothing is
/// looked up through a shell.
#[derive(Debug, Clone)]
pub struct LaunchConfig {
    /// Absolute path to the `lrh` executable, or to a Python interpreter.
    pub program: PathBuf,
    /// Arguments before `serve --desktop-protocol`, such as
    /// `["-m", "lrh.cli.main"]` for an interpreter.
    pub program_args: Vec<OsString>,
    /// The workspace to serve, sent as `workspace.project_root`.
    pub project_root: PathBuf,
    /// Extra environment for the child, on top of the inherited environment.
    pub env: Vec<(OsString, OsString)>,
    pub startup_timeout: Duration,
    pub shutdown_timeout: Duration,
    pub terminate_timeout: Duration,
}

impl LaunchConfig {
    /// A config with the protocol's default deadlines.
    pub fn new(program: impl Into<PathBuf>, project_root: impl Into<PathBuf>) -> Self {
        LaunchConfig {
            program: program.into(),
            program_args: Vec::new(),
            project_root: project_root.into(),
            env: Vec::new(),
            startup_timeout: DEFAULT_STARTUP_TIMEOUT,
            shutdown_timeout: DEFAULT_SHUTDOWN_TIMEOUT,
            terminate_timeout: DEFAULT_TERMINATE_TIMEOUT,
        }
    }
}

/// Returns a fresh launch ID. It correlates messages; it is not a secret.
pub fn new_launch_id() -> String {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|elapsed| elapsed.as_nanos())
        .unwrap_or(0);
    let count = COUNTER.fetch_add(1, Ordering::Relaxed);
    format!("{:x}-{nanos:x}-{count:x}", std::process::id())
}

/// Builds the `start` request for one launch.
pub fn start_request(launch_id: &str, project_root: &Path) -> Value {
    json!({
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "type": "start",
        "launch_id": launch_id,
        "workspace": {"project_root": project_root.to_string_lossy()},
    })
}

/// Builds a control message (`shutdown`, `ping`) for the current launch.
pub fn control_message(message_type: &str, launch_id: &str, request_id: Option<&str>) -> Value {
    let mut message = json!({
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "type": message_type,
        "launch_id": launch_id,
    });
    if let Some(request_id) = request_id {
        message["request_id"] = json!(request_id);
    }
    message
}

/// Accepts a `ready` message only if every identity check passes.
///
/// `sent_project_root` is exactly the `workspace.project_root` this supervisor
/// sent. The backend must echo it, and its canonical form must be the reported
/// repository root or control directory.
pub fn verify_ready(
    message: &Value,
    launch_id: &str,
    sent_project_root: &Path,
    generation: u64,
) -> Result<Handshake, SupervisorError> {
    if message.get("protocol").and_then(Value::as_str) != Some(PROTOCOL_NAME) {
        return Err(SupervisorError::new(
            ErrorKind::IncompatibleBackend,
            "unexpected protocol name",
        ));
    }
    // A JSON `true` or `1.0` is not version 1: require an unsigned integer.
    let version = message.get("protocol_version").and_then(Value::as_u64);
    if version != Some(PROTOCOL_VERSION) {
        let mut error = SupervisorError::new(
            ErrorKind::IncompatibleBackend,
            format!(
                "unsupported protocol_version {}",
                message.get("protocol_version").unwrap_or(&Value::Null)
            ),
        );
        error.backend_error = message.get("backend").cloned();
        return Err(error);
    }
    if message.get("launch_id").and_then(Value::as_str) != Some(launch_id) {
        return Err(SupervisorError::new(
            ErrorKind::LaunchIdMismatch,
            "ready is for another launch",
        ));
    }
    let workspace = message
        .get("workspace")
        .filter(|value| value.is_object())
        .ok_or_else(|| {
            SupervisorError::new(ErrorKind::MalformedHandshake, "ready lacks workspace")
        })?;
    let sent = sent_project_root.to_string_lossy();
    if workspace
        .get("requested_project_root")
        .and_then(Value::as_str)
        != Some(sent.as_ref())
    {
        return Err(SupervisorError::new(
            ErrorKind::WorkspaceMismatch,
            format!("backend did not echo the requested workspace {sent}"),
        ));
    }
    let expected = std::fs::canonicalize(sent_project_root)
        .unwrap_or_else(|_| sent_project_root.to_path_buf());
    if !workspace_matches(&expected, workspace) {
        return Err(SupervisorError::new(
            ErrorKind::WorkspaceMismatch,
            format!(
                "backend reports a different effective workspace than {}",
                expected.display()
            ),
        ));
    }
    let endpoint = message
        .get("endpoint")
        .filter(|value| value.is_object())
        .ok_or_else(|| {
            SupervisorError::new(ErrorKind::MalformedHandshake, "ready lacks endpoint")
        })?;
    let host = endpoint.get("host").and_then(Value::as_str).unwrap_or("");
    if !LOOPBACK_HOSTS.contains(&host) {
        return Err(SupervisorError::new(
            ErrorKind::NonLoopbackEndpoint,
            format!("endpoint host {host:?} is not loopback"),
        ));
    }
    let port = endpoint
        .get("port")
        .and_then(Value::as_u64)
        .and_then(|port| u16::try_from(port).ok())
        .filter(|port| *port > 0)
        .ok_or_else(|| {
            SupervisorError::new(ErrorKind::MalformedHandshake, "invalid endpoint port")
        })?;
    let url_host = if host.contains(':') {
        format!("[{host}]")
    } else {
        host.to_string()
    };
    Ok(Handshake {
        launch_id: launch_id.to_string(),
        generation,
        protocol_version: PROTOCOL_VERSION,
        backend: message.get("backend").cloned().unwrap_or(Value::Null),
        pid: message.get("pid").and_then(Value::as_i64),
        workspace: workspace.clone(),
        host: host.to_string(),
        port,
        url: format!("http://{url_host}:{port}/"),
    })
}

/// Requires the reported root and control directory to agree with `expected`,
/// the canonical configured path: a repository root (whose control directory
/// is `<root>/project` or the root itself) or a `project/` control directory
/// (whose repository root is its parent).
fn workspace_matches(expected: &Path, workspace: &Value) -> bool {
    let (Some(root), Some(project_dir)) = (
        workspace.get("project_root").and_then(Value::as_str),
        workspace.get("project_dir").and_then(Value::as_str),
    ) else {
        return false;
    };
    let (root, project_dir) = (Path::new(root), Path::new(project_dir));
    if root == expected {
        return project_dir == expected.join("project") || project_dir == expected;
    }
    expected.file_name().is_some_and(|name| name == "project")
        && project_dir == expected
        && Some(root) == expected.parent()
}

/// An item from one child's stdout reader.
enum Item {
    Message(Value),
    Malformed(String),
    Eof,
}

/// One owned child launch. Create a new instance for each launch.
pub struct OwnedServer {
    config: LaunchConfig,
    sent_project_root: PathBuf,
    launch_id: String,
    generation: u64,
    state: State,
    handshake: Option<Handshake>,
    child: Option<Child>,
    stdin: Option<ChildStdin>,
    /// This handle's own stdout reader; messages from any other child can
    /// never arrive here.
    messages: Option<Receiver<Item>>,
    events: Vec<Value>,
    stale_events: Vec<Value>,
    stderr_tail: Arc<Mutex<VecDeque<u8>>>,
    readers: Vec<JoinHandle<()>>,
    exit_code: Option<i32>,
    exited: bool,
}

impl OwnedServer {
    /// Prepares one launch. Nothing is spawned until [`OwnedServer::start`].
    pub fn new(config: LaunchConfig, generation: u64) -> Self {
        // Send the canonical path when it resolves, like the reference
        // supervisor; otherwise let the backend report the invalid workspace.
        let sent_project_root = std::fs::canonicalize(&config.project_root)
            .unwrap_or_else(|_| config.project_root.clone());
        OwnedServer {
            config,
            sent_project_root,
            launch_id: new_launch_id(),
            generation,
            state: State::Stopped,
            handshake: None,
            child: None,
            stdin: None,
            messages: None,
            events: Vec::new(),
            stale_events: Vec::new(),
            stderr_tail: Arc::new(Mutex::new(VecDeque::new())),
            readers: Vec::new(),
            exit_code: None,
            exited: false,
        }
    }

    pub fn launch_id(&self) -> &str {
        &self.launch_id
    }

    pub fn state(&self) -> State {
        self.state
    }

    pub fn handshake(&self) -> Option<&Handshake> {
        self.handshake.as_ref()
    }

    /// The OS process ID of the owned child, while it has one.
    pub fn child_pid(&self) -> Option<u32> {
        self.child.as_ref().map(Child::id)
    }

    /// Current-launch messages received so far (for example `stopped`).
    pub fn events(&self) -> &[Value] {
        &self.events
    }

    /// Messages that carried another launch's ID and were discarded.
    pub fn stale_events(&self) -> &[Value] {
        &self.stale_events
    }

    /// The bounded stderr tail, decoded lossily.
    pub fn stderr_tail(&self) -> String {
        let tail = lock(&self.stderr_tail);
        let (front, back) = tail.as_slices();
        let mut bytes = Vec::with_capacity(tail.len());
        bytes.extend_from_slice(front);
        bytes.extend_from_slice(back);
        String::from_utf8_lossy(&bytes).into_owned()
    }

    /// Spawns the child and waits (bounded) for a verified handshake.
    ///
    /// A failed start never leaves a running child behind.
    pub fn start(&mut self) -> Result<Handshake, SupervisorError> {
        if self.state != State::Stopped || self.child.is_some() {
            return Err(SupervisorError::new(
                ErrorKind::AlreadyLaunched,
                "create a new OwnedServer for each launch",
            ));
        }
        self.state = State::Starting;
        if let Err(error) = self.spawn() {
            self.state = State::Failed;
            return Err(error);
        }
        let request = start_request(&self.launch_id, &self.sent_project_root);
        // A write failure shows up as EOF or exit while awaiting the handshake.
        self.send(&request);
        match self.await_handshake() {
            Ok(handshake) => {
                self.state = State::Running;
                self.handshake = Some(handshake.clone());
                Ok(handshake)
            }
            Err(mut error) => {
                self.close_stdin();
                if !self.wait_for_exit(Duration::ZERO) {
                    self.escalate();
                }
                self.release();
                error.exit_code = error.exit_code.or(self.exit_code);
                error.stderr_tail = self.stderr_tail();
                self.state = State::Failed;
                Err(error)
            }
        }
    }

    /// True only while the handshake holds and the child is still alive.
    pub fn is_running(&mut self) -> bool {
        if self.state != State::Running {
            return false;
        }
        if self.wait_for_exit(Duration::ZERO) {
            self.state = State::Failed;
            return false;
        }
        true
    }

    /// The exit code once the child has exited, if it exited normally.
    pub fn exit_code(&self) -> Option<i32> {
        self.exit_code
    }

    /// Round-trips a `ping` over the private channel.
    pub fn ping(&mut self, timeout: Duration) -> Result<Value, SupervisorError> {
        let request_id = new_launch_id();
        let message = control_message("ping", &self.launch_id, Some(&request_id));
        if !self.send(&message) {
            return Err(SupervisorError::new(
                ErrorKind::ChannelFailed,
                "could not write ping",
            ));
        }
        let deadline = Instant::now() + timeout;
        loop {
            match self.next_item(deadline) {
                Some(Item::Message(reply))
                    if reply.get("type").and_then(Value::as_str) == Some("pong")
                        && reply.get("request_id").and_then(Value::as_str)
                            == Some(request_id.as_str()) =>
                {
                    return Ok(reply);
                }
                Some(Item::Message(_)) => continue,
                _ => {
                    return Err(SupervisorError::new(
                        ErrorKind::ChannelFailed,
                        "no pong received",
                    ))
                }
            }
        }
    }

    /// Graceful stop, then terminate/kill of the owned child only.
    pub fn stop(&mut self) -> StopResult {
        self.finish(true)
    }

    /// Closes stdin without a message, as a crashed parent would.
    pub fn close_channel(&mut self) -> StopResult {
        self.finish(false)
    }

    fn spawn(&mut self) -> Result<(), SupervisorError> {
        let mut command = Command::new(&self.config.program);
        command
            .args(&self.config.program_args)
            .args(["serve", "--desktop-protocol"])
            .envs(self.config.env.iter().map(|(key, value)| (key, value)))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let mut child = command.spawn().map_err(|error| {
            SupervisorError::new(
                ErrorKind::SpawnFailed,
                format!("could not start {}: {error}", self.config.program.display()),
            )
        })?;
        self.stdin = child.stdin.take();
        let stdout = child.stdout.take();
        let stderr = child.stderr.take();
        self.child = Some(child);

        let (sender, receiver) = mpsc::channel();
        self.messages = Some(receiver);
        if let Some(stdout) = stdout {
            self.readers
                .push(spawn_reader("lrh-supervisor-stdout", move || {
                    read_stdout(stdout, &sender)
                }));
        }
        if let Some(stderr) = stderr {
            let tail = Arc::clone(&self.stderr_tail);
            self.readers
                .push(spawn_reader("lrh-supervisor-stderr", move || {
                    drain_stderr(stderr, &tail)
                }));
        }
        Ok(())
    }

    fn await_handshake(&mut self) -> Result<Handshake, SupervisorError> {
        let deadline = Instant::now() + self.config.startup_timeout;
        loop {
            // Wait in short slices so an exit is noticed even if a leaked
            // descriptor keeps the child's stdout open after it dies.
            let slice = (Instant::now() + HANDSHAKE_POLL_INTERVAL).min(deadline);
            if let Some(item) = self.next_item(slice) {
                return self.handshake_item(item);
            }
            if self.wait_for_exit(Duration::ZERO) {
                // Take a message the child wrote just before exiting.
                let grace = Instant::now() + EXIT_POLL_INTERVAL;
                return match self.next_item(grace) {
                    Some(item) => self.handshake_item(item),
                    None => Err(self.exited_before_ready()),
                };
            }
            if Instant::now() >= deadline {
                return Err(SupervisorError::new(
                    ErrorKind::StartupTimeout,
                    format!(
                        "no handshake within {:.1} seconds",
                        self.config.startup_timeout.as_secs_f64()
                    ),
                ));
            }
        }
    }

    fn exited_before_ready(&mut self) -> SupervisorError {
        let mut error = SupervisorError::new(
            ErrorKind::ExitedBeforeReady,
            "backend exited or closed its channel without a handshake",
        );
        self.wait_for_exit(self.config.terminate_timeout);
        error.exit_code = self.exit_code;
        error
    }

    fn handshake_item(&mut self, item: Item) -> Result<Handshake, SupervisorError> {
        match item {
            Item::Eof => Err(self.exited_before_ready()),
            Item::Malformed(detail) => {
                Err(SupervisorError::new(ErrorKind::MalformedHandshake, detail))
            }
            Item::Message(message) => self.handshake_from(message),
        }
    }

    fn handshake_from(&mut self, message: Value) -> Result<Handshake, SupervisorError> {
        let launch_id = message.get("launch_id");
        if launch_id.is_some_and(|id| !id.is_null() && id.as_str() != Some(&self.launch_id)) {
            // This handle's own child answered for another launch: that is a
            // failed launch, not a stale event to wait past.
            return Err(SupervisorError::new(
                ErrorKind::LaunchIdMismatch,
                "handshake is for another launch",
            ));
        }
        match message.get("type").and_then(Value::as_str) {
            Some("failed") => {
                let backend_error = message.get("error").cloned();
                let code = backend_error
                    .as_ref()
                    .and_then(|error| error.get("code"))
                    .and_then(Value::as_str)
                    .unwrap_or("");
                let kind =
                    if code == "unsupported_protocol" || code == "unsupported_protocol_version" {
                        ErrorKind::IncompatibleBackend
                    } else {
                        ErrorKind::BackendFailed
                    };
                let mut error = SupervisorError::new(
                    kind,
                    format!("backend reported a startup failure: {code}"),
                );
                error.backend_error = backend_error;
                self.wait_for_exit(self.config.terminate_timeout);
                error.exit_code = self.exit_code;
                Err(error)
            }
            Some("ready") => verify_ready(
                &message,
                &self.launch_id,
                &self.sent_project_root,
                self.generation,
            ),
            other => Err(SupervisorError::new(
                ErrorKind::MalformedHandshake,
                format!("expected ready or failed, got {other:?}"),
            )),
        }
    }

    fn finish(&mut self, send_shutdown: bool) -> StopResult {
        if self.child.is_none() {
            return StopResult {
                exit_code: self.exit_code,
                escalation: Escalation::None,
                reason: None,
            };
        }
        self.state = State::Stopping;
        if send_shutdown && !self.exited {
            let message = control_message("shutdown", &self.launch_id, None);
            self.send(&message);
        }
        self.close_stdin();
        let mut escalation = Escalation::None;
        if !self.wait_for_exit(self.config.shutdown_timeout) {
            escalation = self.escalate();
        }
        self.release();
        self.state = State::Stopped;
        let reason = self
            .events
            .iter()
            .rev()
            .find(|event| event.get("type").and_then(Value::as_str) == Some("stopped"))
            .and_then(|event| event.get("reason"))
            .and_then(Value::as_str)
            .map(str::to_string);
        StopResult {
            exit_code: self.exit_code,
            escalation,
            reason,
        }
    }

    /// Terminates, then kills, the owned child handle. Never by name or port.
    ///
    /// Signals are sent only while the child is unreaped, so its PID cannot
    /// belong to another process. After a kill it waits for the exit, so a
    /// restart never spawns before the previous child is gone.
    fn escalate(&mut self) -> Escalation {
        if self.exited {
            return Escalation::None;
        }
        if let Some(child) = self.child.as_mut() {
            terminate(child);
        }
        if self.wait_for_exit(self.config.terminate_timeout) {
            return Escalation::Terminate;
        }
        if let Some(child) = self.child.as_mut() {
            let _ = child.kill();
            // SIGKILL cannot be ignored, so this wait terminates.
            if let Ok(status) = child.wait() {
                self.exited = true;
                self.exit_code = status.code();
            }
        }
        Escalation::Kill
    }

    /// Polls the owned child until it exits or `timeout` passes. Returns true
    /// once it has exited (and been reaped), including death by signal.
    fn wait_for_exit(&mut self, timeout: Duration) -> bool {
        if self.exited {
            return true;
        }
        let Some(child) = self.child.as_mut() else {
            return false;
        };
        let deadline = Instant::now() + timeout;
        loop {
            match child.try_wait() {
                Ok(Some(status)) => {
                    self.exited = true;
                    self.exit_code = status.code();
                    return true;
                }
                Ok(None) if Instant::now() < deadline => thread::sleep(EXIT_POLL_INTERVAL),
                _ => return false,
            }
        }
    }

    fn send(&mut self, message: &Value) -> bool {
        let Some(stdin) = self.stdin.as_mut() else {
            return false;
        };
        let mut line = message.to_string().into_bytes();
        line.push(b'\n');
        stdin.write_all(&line).and_then(|()| stdin.flush()).is_ok()
    }

    fn close_stdin(&mut self) {
        self.stdin = None;
    }

    /// After exit: collect remaining output and release the pipes.
    fn release(&mut self) {
        self.close_stdin();
        let deadline = Instant::now() + self.config.terminate_timeout;
        for reader in self.readers.drain(..) {
            // The readers end at EOF, which follows the child's exit. Never
            // block past the bound if a leaked descriptor keeps a pipe open.
            while !reader.is_finished() && Instant::now() < deadline {
                thread::sleep(EXIT_POLL_INTERVAL);
            }
            if reader.is_finished() {
                let _ = reader.join();
            }
        }
        if let Some(messages) = self.messages.take() {
            while let Ok(item) = messages.try_recv() {
                if let Item::Message(message) = item {
                    self.record(message);
                }
            }
        }
    }

    /// Returns the next item before `deadline`, recording messages and
    /// discarding (after `starting`) messages from another launch.
    fn next_item(&mut self, deadline: Instant) -> Option<Item> {
        loop {
            let remaining = deadline.checked_duration_since(Instant::now())?;
            let item = match self.messages.as_ref()?.recv_timeout(remaining) {
                Ok(item) => item,
                Err(RecvTimeoutError::Timeout) => return None,
                Err(RecvTimeoutError::Disconnected) => return Some(Item::Eof),
            };
            if let Item::Message(message) = &item {
                if self.is_stale(message) {
                    if self.state != State::Starting {
                        self.stale_events.push(message.clone());
                        continue;
                    }
                } else {
                    self.events.push(message.clone());
                }
            }
            return Some(item);
        }
    }

    fn record(&mut self, message: Value) {
        if self.is_stale(&message) {
            self.stale_events.push(message);
        } else {
            self.events.push(message);
        }
    }

    fn is_stale(&self, message: &Value) -> bool {
        match message.get("launch_id") {
            None | Some(Value::Null) => false,
            Some(id) => id.as_str() != Some(self.launch_id.as_str()),
        }
    }
}

impl Drop for OwnedServer {
    /// Safety net: a dropped launch never leaves its child running.
    fn drop(&mut self) {
        if self.child.is_some() && !self.exited {
            self.close_stdin();
            if !self.wait_for_exit(self.config.terminate_timeout) {
                self.escalate();
            }
        }
    }
}

/// Sends SIGTERM to the owned child, or kills it where signals don't exist.
///
/// The child has not been reaped yet (we still hold its handle and have not
/// observed its exit), so its PID cannot have been reused by another process.
fn terminate(child: &mut Child) {
    #[cfg(unix)]
    {
        if let Ok(pid) = libc::pid_t::try_from(child.id()) {
            // SAFETY: kill(2) takes no pointers; `pid` is our unreaped child.
            unsafe {
                libc::kill(pid, libc::SIGTERM);
            }
            return;
        }
    }
    let _ = child.kill();
}

fn spawn_reader(name: &str, body: impl FnOnce() + Send + 'static) -> JoinHandle<()> {
    thread::Builder::new()
        .name(name.to_string())
        .spawn(body)
        .expect("failed to spawn supervisor reader thread")
}

fn read_stdout(stdout: impl Read, sender: &Sender<Item>) {
    let mut reader = BufReader::new(stdout);
    let mut line = Vec::new();
    loop {
        line.clear();
        let limit = u64::try_from(MAX_MESSAGE_BYTES).unwrap_or(u64::MAX) + 1;
        let read = reader
            .by_ref()
            .take(limit)
            .read_until(b'\n', &mut line)
            .unwrap_or(0);
        if read == 0 {
            let _ = sender.send(Item::Eof);
            return;
        }
        if line.len() > MAX_MESSAGE_BYTES {
            let _ = sender.send(Item::Malformed("oversized message".into()));
            return;
        }
        let frame = trim_line(&line);
        if frame.iter().all(u8::is_ascii_whitespace) {
            continue;
        }
        let item = match serde_json::from_slice::<Value>(frame) {
            Ok(value) if value.is_object() => Item::Message(value),
            _ => Item::Malformed("backend wrote a non-protocol line".into()),
        };
        if sender.send(item).is_err() {
            return;
        }
    }
}

fn trim_line(line: &[u8]) -> &[u8] {
    let mut end = line.len();
    while end > 0 && matches!(line[end - 1], b'\n' | b'\r') {
        end -= 1;
    }
    &line[..end]
}

fn drain_stderr(mut stderr: impl Read, tail: &Mutex<VecDeque<u8>>) {
    let mut chunk = [0_u8; 8192];
    loop {
        let read = match stderr.read(&mut chunk) {
            Ok(0) | Err(_) => return,
            Ok(read) => read,
        };
        let mut tail = lock(tail);
        tail.extend(&chunk[..read]);
        let excess = tail.len().saturating_sub(STDERR_TAIL_BYTES);
        tail.drain(..excess);
    }
}

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    mutex
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

/// A snapshot of the supervised server, cheap to read while an operation runs.
#[derive(Debug, Clone, PartialEq)]
pub struct Status {
    pub state: State,
    pub handshake: Option<Handshake>,
    pub last_error: Option<SupervisorError>,
    /// Exit code of the last child that stopped or crashed.
    pub last_exit_code: Option<i32>,
}

/// Serializes Start, Stop, and Restart for at most one owned child.
pub struct Supervisor {
    config: LaunchConfig,
    /// Held for the whole of each operation, so operations never interleave.
    current: Mutex<Option<OwnedServer>>,
    /// Updated at each transition; readable without waiting for an operation.
    status: Mutex<Status>,
    generation: AtomicU64,
}

impl Supervisor {
    pub fn new(config: LaunchConfig) -> Self {
        Supervisor {
            config,
            current: Mutex::new(None),
            status: Mutex::new(Status {
                state: State::Stopped,
                handshake: None,
                last_error: None,
                last_exit_code: None,
            }),
            generation: AtomicU64::new(0),
        }
    }

    /// The current state, refreshed if a running child has exited.
    ///
    /// While another operation holds the supervisor (a start, stop, restart,
    /// or ping), this returns the last recorded status without waiting, so a
    /// child that died during that operation shows as `Running` until the
    /// operation ends. Treat `Running` as "was running at the last check".
    pub fn status(&self) -> Status {
        if let Ok(mut current) = self.current.try_lock() {
            self.refresh(&mut current);
        }
        lock(&self.status).clone()
    }

    pub fn state(&self) -> State {
        self.status().state
    }

    /// True if `generation` is the running launch; a callback carrying any
    /// other generation is stale and must not change state or endpoint.
    pub fn is_current(&self, generation: u64) -> bool {
        let status = self.status();
        status.state == State::Running
            && status
                .handshake
                .is_some_and(|handshake| handshake.generation == generation)
    }

    /// Idempotent: returns the running handshake instead of relaunching.
    pub fn start(&self) -> Result<Handshake, SupervisorError> {
        let mut current = lock(&self.current);
        self.refresh(&mut current);
        if let Some(server) = current.as_mut() {
            if server.is_running() {
                if let Some(handshake) = server.handshake() {
                    return Ok(handshake.clone());
                }
            }
        }
        // Reap a child that exited on its own before relaunching.
        self.stop_locked(&mut current);
        self.launch_locked(&mut current)
    }

    /// Stops the owned child, if any. Returns how it ended.
    pub fn stop(&self) -> Option<StopResult> {
        let mut current = lock(&self.current);
        let result = self.stop_locked(&mut current);
        self.set_status(State::Stopped, None, None, result.as_ref());
        result
    }

    /// Waits for the previous owned child to exit, then launches a new one
    /// with a new launch ID.
    pub fn restart(&self) -> Result<Handshake, SupervisorError> {
        let mut current = lock(&self.current);
        self.stop_locked(&mut current);
        self.launch_locked(&mut current)
    }

    /// Round-trips a `ping` to the running child.
    pub fn ping(&self, timeout: Duration) -> Result<Value, SupervisorError> {
        let mut current = lock(&self.current);
        match current.as_mut() {
            Some(server) => {
                if server.is_running() {
                    server.ping(timeout)
                } else {
                    Err(SupervisorError::new(
                        ErrorKind::ChannelFailed,
                        "no running backend",
                    ))
                }
            }
            None => Err(SupervisorError::new(
                ErrorKind::ChannelFailed,
                "no running backend",
            )),
        }
    }

    /// The bounded stderr tail of the current or last child.
    pub fn stderr_tail(&self) -> String {
        lock(&self.current)
            .as_ref()
            .map(OwnedServer::stderr_tail)
            .unwrap_or_default()
    }

    /// The OS process ID of the owned child, while it has one.
    pub fn child_pid(&self) -> Option<u32> {
        lock(&self.current)
            .as_ref()
            .and_then(OwnedServer::child_pid)
    }

    fn launch_locked(
        &self,
        current: &mut Option<OwnedServer>,
    ) -> Result<Handshake, SupervisorError> {
        let generation = self.generation.fetch_add(1, Ordering::SeqCst) + 1;
        self.set_status(State::Starting, None, None, None);
        let mut server = OwnedServer::new(self.config.clone(), generation);
        let result = server.start();
        match &result {
            Ok(handshake) => self.set_status(State::Running, Some(handshake.clone()), None, None),
            Err(error) => {
                let mut status = lock(&self.status);
                status.state = State::Failed;
                status.handshake = None;
                status.last_error = Some(error.clone());
                status.last_exit_code = error.exit_code;
            }
        }
        *current = Some(server);
        result
    }

    fn stop_locked(&self, current: &mut Option<OwnedServer>) -> Option<StopResult> {
        let mut server = current.take()?;
        // A launch that never spawned has nothing to stop.
        server.child_pid()?;
        let state = lock(&self.status).state;
        if state != State::Failed {
            self.set_status(State::Stopping, None, None, None);
        }
        Some(server.stop())
    }

    /// Marks an unexpected exit of a running child as failed.
    fn refresh(&self, current: &mut Option<OwnedServer>) {
        let Some(server) = current.as_mut() else {
            return;
        };
        if server.state() == State::Running && !server.is_running() {
            let mut error = SupervisorError::new(
                ErrorKind::ExitedUnexpectedly,
                "backend exited unexpectedly while running",
            );
            error.exit_code = server.exit_code();
            error.stderr_tail = server.stderr_tail();
            let mut status = lock(&self.status);
            status.state = State::Failed;
            status.handshake = None;
            status.last_exit_code = server.exit_code();
            status.last_error = Some(error);
        }
    }

    fn set_status(
        &self,
        state: State,
        handshake: Option<Handshake>,
        error: Option<SupervisorError>,
        stopped: Option<&StopResult>,
    ) {
        let mut status = lock(&self.status);
        status.state = state;
        status.handshake = handshake;
        if error.is_some() || state == State::Starting {
            status.last_error = error;
        }
        if let Some(stopped) = stopped {
            status.last_exit_code = stopped.exit_code;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ready_for(launch_id: &str, root: &Path) -> Value {
        let root = root.to_string_lossy();
        json!({
            "protocol": PROTOCOL_NAME,
            "protocol_version": 1,
            "type": "ready",
            "launch_id": launch_id,
            "backend": {"name": "lrh"},
            "pid": 42,
            "workspace": {
                "requested_project_root": root,
                "project_root": root,
                "project_dir": format!("{root}/project"),
                "name": "lrh",
            },
            "endpoint": {"scheme": "http", "host": "127.0.0.1", "port": 50543,
                         "url": "http://127.0.0.1:50543/"},
        })
    }

    fn temp_root() -> PathBuf {
        std::fs::canonicalize(std::env::temp_dir()).unwrap()
    }

    #[test]
    fn verify_ready_accepts_a_matching_handshake() {
        let root = temp_root();
        let handshake = verify_ready(&ready_for("L1", &root), "L1", &root, 3).unwrap();
        assert_eq!(handshake.url, "http://127.0.0.1:50543/");
        assert_eq!(handshake.generation, 3);
        assert_eq!(handshake.pid, Some(42));
    }

    #[test]
    fn verify_ready_rejects_boolean_or_other_versions() {
        let root = temp_root();
        for version in [json!(true), json!(2), json!(1.5), json!("1")] {
            let mut message = ready_for("L1", &root);
            message["protocol_version"] = version;
            let error = verify_ready(&message, "L1", &root, 1).unwrap_err();
            assert_eq!(error.kind, ErrorKind::IncompatibleBackend);
        }
    }

    #[test]
    fn verify_ready_rejects_wrong_launch_workspace_and_endpoint() {
        let root = temp_root();
        let error = verify_ready(&ready_for("other", &root), "L1", &root, 1).unwrap_err();
        assert_eq!(error.kind, ErrorKind::LaunchIdMismatch);

        let mut message = ready_for("L1", &root);
        message["workspace"]["project_root"] = json!("/somewhere/else");
        let error = verify_ready(&message, "L1", &root, 1).unwrap_err();
        assert_eq!(error.kind, ErrorKind::WorkspaceMismatch);

        let mut message = ready_for("L1", &root);
        message["workspace"]["requested_project_root"] = json!("/not/what/we/sent");
        let error = verify_ready(&message, "L1", &root, 1).unwrap_err();
        assert_eq!(error.kind, ErrorKind::WorkspaceMismatch);

        let mut message = ready_for("L1", &root);
        message["endpoint"]["host"] = json!("0.0.0.0");
        let error = verify_ready(&message, "L1", &root, 1).unwrap_err();
        assert_eq!(error.kind, ErrorKind::NonLoopbackEndpoint);

        let mut message = ready_for("L1", &root);
        message["endpoint"]["port"] = json!(70000);
        let error = verify_ready(&message, "L1", &root, 1).unwrap_err();
        assert_eq!(error.kind, ErrorKind::MalformedHandshake);
    }

    #[test]
    fn verify_ready_accepts_a_control_directory_workspace() {
        let root = temp_root();
        let control = root.join("project");
        let mut message = ready_for("L1", &control);
        message["workspace"]["project_root"] = json!(root.to_string_lossy());
        message["workspace"]["project_dir"] = json!(control.to_string_lossy());
        // canonicalize() of a missing path falls back to the path itself.
        assert!(verify_ready(&message, "L1", &control, 1).is_ok());
    }

    #[test]
    fn launch_ids_are_unique_and_within_the_protocol_alphabet() {
        let first = new_launch_id();
        let second = new_launch_id();
        assert_ne!(first, second);
        for id in [first, second] {
            assert!(id.len() <= 128);
            assert!(id
                .chars()
                .all(|c| c.is_ascii_alphanumeric() || "._:-".contains(c)));
        }
    }

    #[test]
    fn read_stdout_frames_messages_and_flags_bad_lines() {
        let input = b"{\"type\":\"ready\"}\r\n\n  \nnot json\n".to_vec();
        let (sender, receiver) = mpsc::channel();
        read_stdout(&input[..], &sender);
        let items: Vec<Item> = receiver.try_iter().collect();
        assert!(matches!(&items[0], Item::Message(value) if value["type"] == "ready"));
        assert!(matches!(&items[1], Item::Malformed(_)));
        assert!(matches!(&items[2], Item::Eof));
    }

    #[test]
    fn read_stdout_rejects_oversized_messages() {
        let mut input = vec![b'x'; MAX_MESSAGE_BYTES + 10];
        input.push(b'\n');
        let (sender, receiver) = mpsc::channel();
        read_stdout(&input[..], &sender);
        assert!(matches!(receiver.try_recv(), Ok(Item::Malformed(_))));
    }

    #[test]
    fn stderr_tail_is_bounded() {
        let input = vec![b'e'; STDERR_TAIL_BYTES + 5000];
        let tail = Mutex::new(VecDeque::new());
        drain_stderr(&input[..], &tail);
        assert_eq!(lock(&tail).len(), STDERR_TAIL_BYTES);
    }
}
