//! Integration tests for the owned-backend supervisor.
//!
//! They drive real child processes: `lrh serve --desktop-protocol` from this
//! repository's `src/`, plus small Python fakes for failure paths a real
//! backend cannot be made to produce. Every wait is bounded.
//!
//! The Python interpreter comes from `LRH_DESKTOP_TEST_PYTHON`, which
//! `apps/desktop/scripts/run test` sets; it is never looked up on PATH here.

use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

use lrh_console_lib::supervisor::{
    ErrorKind, Escalation, LaunchConfig, State, Supervisor, SupervisorError,
};

const HELPER_ENV: &str = "LRH_SUPERVISOR_TEST_PARENT_LOSS_HELPER";
const HELPER_PID_PREFIX: &str = "HELPER_CHILD_PID=";

fn repo_root() -> PathBuf {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    std::fs::canonicalize(root).expect("repository root")
}

fn python() -> PathBuf {
    let python = std::env::var_os("LRH_DESKTOP_TEST_PYTHON").expect(
        "set LRH_DESKTOP_TEST_PYTHON to a Python interpreter (run the tests via \
         `scripts/test --desktop` or `apps/desktop/scripts/run test`)",
    );
    PathBuf::from(python)
}

fn pythonpath() -> (std::ffi::OsString, std::ffi::OsString) {
    (
        "PYTHONPATH".into(),
        repo_root().join("src").into_os_string(),
    )
}

/// Supervises the real backend from this checkout.
fn lrh_config() -> LaunchConfig {
    let mut config = LaunchConfig::new(python(), repo_root());
    config.program_args = vec!["-m".into(), "lrh.cli.main".into()];
    config.env = vec![pythonpath()];
    config
}

/// Supervises a Python fake. The fake reads `start`, then runs `body`.
fn fake_config(body: &str) -> LaunchConfig {
    let script = format!("{FAKE_PREAMBLE}\n{body}\n");
    let mut config = LaunchConfig::new(python(), repo_root());
    config.program_args = vec!["-c".into(), script.into()];
    config.startup_timeout = Duration::from_secs(10);
    config.shutdown_timeout = Duration::from_secs(2);
    config.terminate_timeout = Duration::from_secs(2);
    config
}

const FAKE_PREAMBLE: &str = r#"
import json, os, signal, sys, time
start = json.loads(sys.stdin.readline())
launch_id = start["launch_id"]
root = start["workspace"]["project_root"]
pid_file = os.environ.get("FAKE_PID_FILE")
if pid_file:
    with open(pid_file, "w") as handle:
        handle.write(str(os.getpid()))

def send(message):
    envelope = {"protocol": "lrh-desktop-server", "protocol_version": 1,
                "launch_id": launch_id}
    envelope.update(message)
    sys.stdout.write(json.dumps(envelope) + "\n")
    sys.stdout.flush()

def ready(**overrides):
    message = {"type": "ready", "pid": os.getpid(), "backend": {"name": "fake"},
               "workspace": {"requested_project_root": root, "project_root": root,
                             "project_dir": os.path.join(root, "project")},
               "endpoint": {"scheme": "http", "host": "127.0.0.1", "port": 9,
                            "url": "http://127.0.0.1:9/"}}
    message.update(overrides)
    send(message)
"#;

#[cfg(unix)]
fn pid_alive(pid: u32) -> bool {
    let pid = libc::pid_t::try_from(pid).expect("pid fits pid_t");
    // SAFETY: kill(2) with signal 0 only checks for existence.
    unsafe { libc::kill(pid, 0) == 0 }
}

#[cfg(unix)]
fn wait_until_dead(pid: u32, bound: Duration) -> bool {
    let deadline = Instant::now() + bound;
    while Instant::now() < deadline {
        if !pid_alive(pid) {
            return true;
        }
        thread::sleep(Duration::from_millis(50));
    }
    !pid_alive(pid)
}

fn http_status(port: u16, path: &str) -> Option<u16> {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).ok()?;
    stream.set_read_timeout(Some(Duration::from_secs(5))).ok()?;
    write!(stream, "GET {path} HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n").ok()?;
    let mut response = String::new();
    stream.read_to_string(&mut response).ok()?;
    response.split_whitespace().nth(1)?.parse().ok()
}

fn wait_for_state(supervisor: &Supervisor, state: State, bound: Duration) -> bool {
    let deadline = Instant::now() + bound;
    while Instant::now() < deadline {
        if supervisor.state() == state {
            return true;
        }
        thread::sleep(Duration::from_millis(50));
    }
    supervisor.state() == state
}

fn expect_error(result: Result<impl std::fmt::Debug, SupervisorError>) -> SupervisorError {
    result.expect_err("expected the launch to fail")
}

#[test]
fn start_serves_the_workspace_and_stop_is_graceful() {
    let supervisor = Supervisor::new(lrh_config());
    let handshake = supervisor.start().expect("backend starts");

    assert_eq!(supervisor.state(), State::Running);
    assert_eq!(handshake.host, "127.0.0.1");
    assert_eq!(
        handshake.workspace["project_root"],
        repo_root().to_string_lossy().as_ref()
    );
    assert_eq!(http_status(handshake.port, "/health"), Some(200));
    let pong = supervisor.ping(Duration::from_secs(5)).expect("pong");
    assert_eq!(pong["type"], "pong");

    let result = supervisor.stop().expect("an owned child was stopped");
    assert_eq!(result.exit_code, Some(0));
    assert_eq!(result.escalation, Escalation::None);
    assert_eq!(result.reason.as_deref(), Some("shutdown_requested"));
    assert_eq!(supervisor.state(), State::Stopped);
    assert_eq!(http_status(handshake.port, "/health"), None);
    // Stopping again is a no-op.
    assert!(supervisor.stop().is_none());
}

#[test]
fn repeated_and_concurrent_start_never_creates_a_second_backend() {
    let supervisor = Arc::new(Supervisor::new(lrh_config()));
    let first = supervisor.start().expect("backend starts");

    let again = supervisor.start().expect("start is idempotent");
    assert_eq!(again.launch_id, first.launch_id);
    assert_eq!(again.generation, first.generation);

    let threads: Vec<_> = (0..4)
        .map(|_| {
            let supervisor = Arc::clone(&supervisor);
            thread::spawn(move || supervisor.start().expect("start").launch_id)
        })
        .collect();
    for thread in threads {
        assert_eq!(thread.join().unwrap(), first.launch_id);
    }
    assert_eq!(supervisor.stop().and_then(|r| r.exit_code), Some(0));
}

#[test]
fn restart_waits_for_the_previous_child_and_uses_a_new_launch() {
    let supervisor = Supervisor::new(lrh_config());
    let first = supervisor.start().expect("backend starts");
    let first_pid = supervisor.child_pid().expect("owned child");

    let second = supervisor.restart().expect("backend restarts");
    assert_ne!(second.launch_id, first.launch_id);
    assert_eq!(second.generation, first.generation + 1);
    assert!(!supervisor.is_current(first.generation));
    assert!(supervisor.is_current(second.generation));
    #[cfg(unix)]
    assert!(
        !pid_alive(first_pid),
        "the previous child must have exited before the new launch"
    );
    #[cfg(not(unix))]
    let _ = first_pid;
    assert_eq!(http_status(second.port, "/health"), Some(200));
    supervisor.stop();
}

#[test]
fn an_invalid_workspace_is_reported_by_the_backend_and_leaves_nothing_running() {
    let mut config = lrh_config();
    config.project_root = std::env::temp_dir();
    let supervisor = Supervisor::new(config);

    let error = expect_error(supervisor.start());
    assert_eq!(error.kind, ErrorKind::BackendFailed);
    let code = error
        .backend_error
        .as_ref()
        .and_then(|e| e["code"].as_str());
    assert_eq!(code, Some("workspace_not_lrh_project"));
    assert_eq!(error.exit_code, Some(3));
    assert_eq!(supervisor.state(), State::Failed);
}

#[test]
fn a_missing_program_is_a_spawn_failure() {
    let mut config = lrh_config();
    config.program = repo_root().join("no-such-lrh-executable");
    let error = expect_error(Supervisor::new(config).start());
    assert_eq!(error.kind, ErrorKind::SpawnFailed);
}

#[cfg(unix)]
#[test]
fn a_readiness_timeout_stops_the_silent_child() {
    let pid_file = std::env::temp_dir().join(format!("lrh-sup-timeout-{}", std::process::id()));
    let mut config = fake_config("time.sleep(60)");
    config.startup_timeout = Duration::from_millis(1500);
    config.env = vec![("FAKE_PID_FILE".into(), pid_file.clone().into_os_string())];
    let supervisor = Supervisor::new(config);

    let started = Instant::now();
    let error = expect_error(supervisor.start());
    assert_eq!(error.kind, ErrorKind::StartupTimeout);
    assert!(started.elapsed() < Duration::from_secs(8), "bounded wait");
    let pid: u32 = std::fs::read_to_string(&pid_file).unwrap().parse().unwrap();
    let _ = std::fs::remove_file(&pid_file);
    assert!(wait_until_dead(pid, Duration::from_secs(2)), "no orphan");
}

#[cfg(unix)]
#[test]
fn a_child_killed_by_a_signal_before_ready_is_reaped_not_signalled() {
    // Death by signal leaves no exit code; the failed start must still see
    // the child as exited and never signal its (reaped) PID again.
    let body = "os.kill(os.getpid(), signal.SIGKILL)";
    let error = expect_error(Supervisor::new(fake_config(body)).start());
    assert_eq!(error.kind, ErrorKind::ExitedBeforeReady);
    assert_eq!(error.exit_code, None);
}

#[test]
fn an_exit_is_noticed_even_if_a_leaked_descriptor_keeps_stdout_open() {
    // A grandchild inherits stdout, so no EOF arrives when the child exits.
    let body = r#"import subprocess
subprocess.Popen([sys.executable, "-c", "import time; time.sleep(4)"])
sys.exit(9)"#;
    let started = Instant::now();
    let error = expect_error(Supervisor::new(fake_config(body)).start());
    assert_eq!(error.kind, ErrorKind::ExitedBeforeReady);
    assert_eq!(error.exit_code, Some(9));
    assert!(
        started.elapsed() < Duration::from_secs(8),
        "the exit must be noticed well before the 10 s startup timeout"
    );
}

#[test]
fn an_incompatible_protocol_version_is_rejected() {
    let error = expect_error(Supervisor::new(fake_config("ready(protocol_version=2)")).start());
    assert_eq!(error.kind, ErrorKind::IncompatibleBackend);

    let body = r#"send({"type": "failed", "error": {"code": "unsupported_protocol_version",
        "message": "no", "details": {"supported_versions": [2]}}}); sys.exit(3)"#;
    let error = expect_error(Supervisor::new(fake_config(body)).start());
    assert_eq!(error.kind, ErrorKind::IncompatibleBackend);
    assert_eq!(error.exit_code, Some(3));
}

#[test]
fn a_wrong_workspace_or_launch_id_is_rejected() {
    let body = r#"ready(workspace={"requested_project_root": root,
        "project_root": "/elsewhere", "project_dir": "/elsewhere/project"}); time.sleep(60)"#;
    let error = expect_error(Supervisor::new(fake_config(body)).start());
    assert_eq!(error.kind, ErrorKind::WorkspaceMismatch);

    let error = expect_error(
        Supervisor::new(fake_config("ready(launch_id='another'); time.sleep(60)")).start(),
    );
    assert_eq!(error.kind, ErrorKind::LaunchIdMismatch);
}

#[test]
fn a_crash_while_running_is_reported_and_start_relaunches() {
    let supervisor = Supervisor::new(fake_config("ready(); time.sleep(0.5); sys.exit(7)"));
    let first = supervisor.start().expect("fake reports ready");

    assert!(wait_for_state(
        &supervisor,
        State::Failed,
        Duration::from_secs(10)
    ));
    let status = supervisor.status();
    assert_eq!(status.last_exit_code, Some(7));
    assert_eq!(
        status.last_error.map(|error| error.kind),
        Some(ErrorKind::ExitedUnexpectedly)
    );
    assert!(!supervisor.is_current(first.generation));

    let second = supervisor.start().expect("start relaunches after a crash");
    assert_eq!(second.generation, first.generation + 1);
    supervisor.stop();
}

#[cfg(unix)]
#[test]
fn a_child_that_ignores_shutdown_and_sigterm_is_killed() {
    let body = "signal.signal(signal.SIGTERM, signal.SIG_IGN); ready(); time.sleep(60)";
    let mut config = fake_config(body);
    config.shutdown_timeout = Duration::from_millis(500);
    config.terminate_timeout = Duration::from_millis(500);
    let supervisor = Supervisor::new(config);
    supervisor.start().expect("fake reports ready");
    let pid = supervisor.child_pid().unwrap();

    let result = supervisor.stop().expect("stopped");
    assert_eq!(result.escalation, Escalation::Kill);
    assert!(wait_until_dead(pid, Duration::from_secs(5)));
}

/// Re-entered as a child process by
/// `parent_loss_stops_the_owned_backend`: starts a backend, reports its PID,
/// and waits to be killed. Without the helper variable it does nothing.
#[cfg(unix)]
#[test]
fn zz_parent_loss_helper_process() {
    if std::env::var_os(HELPER_ENV).is_none() {
        return;
    }
    let supervisor = Supervisor::new(lrh_config());
    supervisor.start().expect("helper backend starts");
    println!("{HELPER_PID_PREFIX}{}", supervisor.child_pid().unwrap());
    std::io::stdout().flush().unwrap();
    thread::sleep(Duration::from_secs(60));
}

#[cfg(unix)]
#[test]
fn parent_loss_stops_the_owned_backend() {
    let mut helper = Command::new(std::env::current_exe().unwrap())
        .args([
            "--exact",
            "zz_parent_loss_helper_process",
            "--nocapture",
            "--test-threads",
            "1",
        ])
        .env(HELPER_ENV, "1")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("spawn helper supervisor");

    let child_pid = read_helper_pid(&mut helper, Duration::from_secs(30));
    assert!(pid_alive(child_pid));

    // SIGKILL the supervising process: no cleanup code of ours runs.
    helper.kill().unwrap();
    helper.wait().unwrap();

    // The child notices stdin EOF within 0.25 s and stops within 5 s.
    assert!(
        wait_until_dead(child_pid, Duration::from_secs(10)),
        "the backend outlived its supervisor"
    );
}

#[cfg(unix)]
fn read_helper_pid(helper: &mut Child, bound: Duration) -> u32 {
    let stdout = helper.stdout.take().unwrap();
    let (sender, receiver) = std::sync::mpsc::channel();
    thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            // libtest may print `test <name> ... ` on the same line first.
            if let Some((_, pid)) = line.split_once(HELPER_PID_PREFIX) {
                let _ = sender.send(pid.trim().parse::<u32>().unwrap());
                return;
            }
        }
    });
    match receiver.recv_timeout(bound) {
        Ok(pid) => pid,
        Err(_) => {
            let _ = helper.kill();
            let _ = helper.wait();
            panic!("helper never reported its backend PID");
        }
    }
}

/// A separately started, foreground `lrh serve` the supervisor never owns.
struct UnrelatedServer {
    child: Child,
    port: u16,
}

impl UnrelatedServer {
    fn start() -> Self {
        let port = TcpListener::bind("127.0.0.1:0")
            .and_then(|listener| listener.local_addr())
            .expect("free port")
            .port();
        let (key, value) = pythonpath();
        let child = Command::new(python())
            .args(["-m", "lrh.cli.main", "serve", "--host", "127.0.0.1"])
            .args(["--port", &port.to_string()])
            .arg("--project-root")
            .arg(repo_root())
            .env(key, value)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .expect("spawn unrelated lrh serve");
        let mut server = UnrelatedServer { child, port };
        let deadline = Instant::now() + Duration::from_secs(30);
        while http_status(port, "/health") != Some(200) {
            assert!(Instant::now() < deadline, "unrelated server never came up");
            assert!(server.child.try_wait().unwrap().is_none(), "exited early");
            thread::sleep(Duration::from_millis(100));
        }
        server
    }

    fn assert_untouched(&mut self, after: &str) {
        assert!(
            self.child.try_wait().unwrap().is_none(),
            "unrelated server exited after {after}"
        );
        assert_eq!(
            http_status(self.port, "/health"),
            Some(200),
            "unrelated server stopped answering after {after}"
        );
    }
}

impl Drop for UnrelatedServer {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[test]
fn a_separately_started_server_is_never_touched() {
    let mut unrelated = UnrelatedServer::start();

    let supervisor = Supervisor::new(lrh_config());
    let handshake = supervisor.start().expect("owned backend starts");
    assert_ne!(handshake.port, unrelated.port);
    unrelated.assert_untouched("Start");

    supervisor.restart().expect("owned backend restarts");
    unrelated.assert_untouched("Restart");

    supervisor.stop();
    unrelated.assert_untouched("Stop");

    let failing = Supervisor::new(fake_config("ready(); time.sleep(0.2); sys.exit(1)"));
    failing.start().expect("fake reports ready");
    assert!(wait_for_state(
        &failing,
        State::Failed,
        Duration::from_secs(10)
    ));
    failing.stop();
    unrelated.assert_untouched("a backend failure");
}
