//! Narrow browser handoff: open one `http(s)` URL in Chrome or the default
//! browser.
//!
//! No shell is involved. The opener is a fixed program with fixed arguments,
//! and the URL is validated first. Handoffs are rate-limited so page content
//! cannot flood the browser with tabs.
//!
//! Agent-session deep links are a second, separate handoff
//! ([`validate_session_link`], [`open_session_link`]). They are allowed only
//! when they match an entry in the shared route definition
//! `src/lrh/conversations/session_links.json`, which the Python side reads
//! too; no vendor route is written in this file. [`validate_url`] is
//! deliberately unchanged and still refuses every non-`http(s)` scheme.

use std::process::{Command, Stdio};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

use serde::Deserialize;
use tauri::Url;

use crate::settings::BrowserChoice;

/// The shared route definition, embedded at compile time. It lives under
/// `src/lrh/` because the Python sdist excludes `apps/`.
const SESSION_LINKS_JSON: &str =
    include_str!("../../../../src/lrh/conversations/session_links.json");

/// At most one handoff per this interval.
pub const MIN_HANDOFF_INTERVAL: Duration = Duration::from_secs(1);

/// The macOS application name used for Chrome.
pub const CHROME_APP: &str = "Google Chrome";

/// Which application a handoff actually used.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Opened {
    Chrome,
    DefaultBrowser,
    /// A vendor desktop app, for an allowlisted session deep link.
    VendorApp,
}

/// The result of a handoff.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct Handoff {
    pub opened: Opened,
    /// Why the requested browser was not used, if it was not.
    pub note: Option<String>,
}

/// Accepts only plain `http`/`https` URLs with a host and no credentials.
pub fn validate_url(url: &Url) -> Result<(), String> {
    if !matches!(url.scheme(), "http" | "https") {
        return Err(format!(
            "only http and https links open in a browser, not {}:",
            url.scheme()
        ));
    }
    if url.host_str().is_none_or(str::is_empty) {
        return Err("the link has no host".into());
    }
    if !url.username().is_empty() || url.password().is_some() {
        return Err("links with embedded credentials are not opened".into());
    }
    Ok(())
}

/// One vendor's link shape, as written in the shared route definition.
#[derive(Debug, Deserialize)]
struct SessionVendor {
    name: String,
    scheme: String,
    host: String,
    path_template: String,
    id_prefix: String,
    id_shape: String,
}

/// The parts of the shared route definition this crate reads. Unknown fields
/// (pointer prefixes, statuses, test vectors) belong to the Python side.
#[derive(Debug, Deserialize)]
struct SessionLinkDefinition {
    schema_version: u32,
    vendors: Vec<SessionVendor>,
}

/// A vendor route ready to match: the path is `before`, an id, then `after`.
#[derive(Debug)]
struct SessionRoute {
    scheme: String,
    host: String,
    before: String,
    after: String,
}

impl SessionRoute {
    fn from_vendor(vendor: SessionVendor) -> Result<Self, String> {
        if vendor.id_shape != "uuid" {
            return Err(format!(
                "route {}: unsupported id shape {:?}",
                vendor.name, vendor.id_shape
            ));
        }
        let path = vendor
            .path_template
            .replace("{id_prefix}", &vendor.id_prefix);
        let mut pieces = path.split("{id}");
        let (Some(before), Some(after), None) = (pieces.next(), pieces.next(), pieces.next())
        else {
            return Err(format!(
                "route {}: the path template must contain {{id}} exactly once",
                vendor.name
            ));
        };
        if !before.starts_with('/')
            || vendor.scheme.is_empty()
            || vendor.scheme != vendor.scheme.to_ascii_lowercase()
            || vendor.host.is_empty()
        {
            return Err(format!(
                "route {}: invalid scheme, host or path",
                vendor.name
            ));
        }
        Ok(Self {
            scheme: vendor.scheme,
            host: vendor.host,
            before: before.to_owned(),
            after: after.to_owned(),
        })
    }

    /// True if `path` is exactly `before` + a UUID + `after`.
    fn matches_path(&self, path: &str) -> bool {
        path.strip_prefix(self.before.as_str())
            .and_then(|rest| rest.strip_suffix(self.after.as_str()))
            .is_some_and(is_uuid)
    }
}

/// Eight-four-four-four-twelve hexadecimal digits, either case, nothing else.
/// Any UUID version: some vendors use time-ordered (v7) ids.
fn is_uuid(text: &str) -> bool {
    let bytes = text.as_bytes();
    bytes.len() == 36
        && bytes.iter().enumerate().all(|(index, byte)| match index {
            8 | 13 | 18 | 23 => *byte == b'-',
            _ => byte.is_ascii_hexdigit(),
        })
}

fn parse_session_routes(text: &str) -> Result<Vec<SessionRoute>, String> {
    let definition: SessionLinkDefinition = serde_json::from_str(text)
        .map_err(|error| format!("the session link definition is not valid: {error}"))?;
    if definition.schema_version != 1 {
        return Err(format!(
            "unsupported session link definition version {}",
            definition.schema_version
        ));
    }
    if definition.vendors.is_empty() {
        return Err("the session link definition has no routes".into());
    }
    definition
        .vendors
        .into_iter()
        .map(SessionRoute::from_vendor)
        .collect()
}

/// The routes from the embedded definition, parsed once. A malformed
/// definition is an error here, so every session link is refused rather than
/// guessed at.
fn session_routes() -> Result<&'static [SessionRoute], String> {
    static ROUTES: OnceLock<Result<Vec<SessionRoute>, String>> = OnceLock::new();
    ROUTES
        .get_or_init(|| parse_session_routes(SESSION_LINKS_JSON))
        .as_ref()
        .map(Vec::as_slice)
        .map_err(Clone::clone)
}

/// Accepts only an agent-session deep link that exactly matches an entry in
/// the shared route definition: its scheme, host and path shape, with a UUID
/// id, and no credentials, port, query, fragment or extra path segments.
pub fn validate_session_link(url: &Url) -> Result<(), String> {
    let routes = session_routes()?;
    if !url.username().is_empty() || url.password().is_some() {
        return Err("links with embedded credentials are not opened".into());
    }
    if url.port().is_some() {
        return Err("session links with a port are not opened".into());
    }
    if url.query().is_some() || url.fragment().is_some() {
        return Err("session links with a query or fragment are not opened".into());
    }
    let host = url.host_str().unwrap_or_default();
    if routes.iter().any(|route| {
        route.scheme == url.scheme() && route.host == host && route.matches_path(url.path())
    }) {
        Ok(())
    } else {
        Err(format!(
            "not an allowlisted session link: {}:",
            url.scheme()
        ))
    }
}

/// Opens an allowlisted session link in its vendor's desktop app. The URL
/// must pass [`validate_session_link`].
pub fn open_session_link(url: &Url) -> Result<Handoff, String> {
    open_session_link_with(url, launch_session_link)
}

/// [`open_session_link`] with the launcher injected, so a test can prove that a
/// refused link never reaches it without ever starting an application.
fn open_session_link_with(
    url: &Url,
    launch: fn(&Url) -> Result<(), String>,
) -> Result<Handoff, String> {
    validate_session_link(url)?;
    launch(url)?;
    Ok(Handoff {
        opened: Opened::VendorApp,
        note: Some(format!("{} session link", url.scheme())),
    })
}

/// Allows one handoff per [`MIN_HANDOFF_INTERVAL`].
#[derive(Default)]
pub struct RateLimiter {
    last: Mutex<Option<Instant>>,
}

impl RateLimiter {
    /// True if a handoff may happen now; records it if so.
    pub fn try_acquire(&self) -> bool {
        self.try_acquire_at(Instant::now())
    }

    fn try_acquire_at(&self, now: Instant) -> bool {
        let mut last = self
            .last
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        if last.is_some_and(|previous| now.duration_since(previous) < MIN_HANDOFF_INTERVAL) {
            return false;
        }
        *last = Some(now);
        true
    }
}

/// True if Chrome is installed (macOS asks Launch Services; elsewhere false).
pub fn chrome_available() -> bool {
    #[cfg(target_os = "macos")]
    {
        Command::new("/usr/bin/open")
            .args(["-Ra", CHROME_APP])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .is_ok_and(|status| status.success())
    }
    #[cfg(not(target_os = "macos"))]
    {
        false
    }
}

/// Opens `url` in the chosen browser, falling back to the default browser
/// when Chrome is chosen but missing. The URL must pass [`validate_url`].
pub fn open(url: &Url, choice: BrowserChoice) -> Result<Handoff, String> {
    validate_url(url)?;
    let (opened, note) = match choice {
        BrowserChoice::Chrome if chrome_available() => (Opened::Chrome, None),
        BrowserChoice::Chrome => (
            Opened::DefaultBrowser,
            Some(format!(
                "{CHROME_APP} was not found, so the default browser was used."
            )),
        ),
        BrowserChoice::DefaultBrowser => (Opened::DefaultBrowser, None),
    };
    launch(url, opened)?;
    Ok(Handoff { opened, note })
}

#[cfg(target_os = "macos")]
fn launch(url: &Url, opened: Opened) -> Result<(), String> {
    let mut command = Command::new("/usr/bin/open");
    if opened == Opened::Chrome {
        command.args(["-a", CHROME_APP]);
    }
    run(command.arg(url.as_str()))
}

#[cfg(all(unix, not(target_os = "macos")))]
fn launch(url: &Url, _opened: Opened) -> Result<(), String> {
    run(Command::new("/usr/bin/xdg-open").arg(url.as_str()))
}

#[cfg(not(unix))]
fn launch(_url: &Url, _opened: Opened) -> Result<(), String> {
    Err("browser handoff is not supported on this platform yet".into())
}

/// Session links use the same fixed, per-platform opener as browser links:
/// `/usr/bin/open` on macOS, `/usr/bin/xdg-open` on other unix. No shell, and
/// the only argument is the validated URL.
#[cfg(target_os = "macos")]
const SESSION_LINK_OPENER: &str = "/usr/bin/open";

#[cfg(all(unix, not(target_os = "macos")))]
const SESSION_LINK_OPENER: &str = "/usr/bin/xdg-open";

/// The command that opens one validated session link: a fixed program with
/// the URL as its only argument. Built apart from running it so a test can
/// check it without starting an application.
#[cfg(unix)]
fn session_link_command(url: &Url) -> Command {
    let mut command = Command::new(SESSION_LINK_OPENER);
    command.arg(url.as_str());
    command
}

#[cfg(unix)]
fn launch_session_link(url: &Url) -> Result<(), String> {
    run_opener(&mut session_link_command(url), "app opener")
}

#[cfg(not(unix))]
fn launch_session_link(_url: &Url) -> Result<(), String> {
    Err("session link handoff is not supported on this platform yet".into())
}

#[cfg(unix)]
fn run(command: &mut Command) -> Result<(), String> {
    run_opener(command, "browser opener")
}

#[cfg(unix)]
fn run_opener(command: &mut Command, what: &str) -> Result<(), String> {
    let status = command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|error| format!("could not start the {what}: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("the {what} failed ({status})"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn url(text: &str) -> Url {
        Url::parse(text).unwrap()
    }

    #[test]
    fn only_plain_web_links_are_handed_off() {
        assert!(validate_url(&url("https://github.com/xenotaur")).is_ok());
        assert!(validate_url(&url("http://127.0.0.1:50543/meta")).is_ok());
        for refused in [
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html,hi",
            "tauri://localhost/index.html",
            "https://user:secret@example.com/",
            "mailto:someone@example.com",
        ] {
            assert!(
                validate_url(&url(refused)).is_err(),
                "{refused} must be refused"
            );
        }
    }

    #[test]
    fn handoffs_are_rate_limited() {
        let limiter = RateLimiter::default();
        let start = Instant::now();
        assert!(limiter.try_acquire_at(start));
        assert!(!limiter.try_acquire_at(start + Duration::from_millis(500)));
        assert!(limiter.try_acquire_at(start + MIN_HANDOFF_INTERVAL));
    }

    /// The shared accept and reject examples, from the same JSON file the
    /// Python tests run.
    #[derive(Deserialize)]
    struct VectorFile {
        vectors: Vectors,
    }

    #[derive(Deserialize)]
    struct Vectors {
        accept: Vec<AcceptVector>,
        reject_links: Vec<String>,
    }

    #[derive(Deserialize)]
    struct AcceptVector {
        link: String,
    }

    fn vectors() -> Vectors {
        serde_json::from_str::<VectorFile>(SESSION_LINKS_JSON)
            .expect("the shared definition parses")
            .vectors
    }

    const CLAUDE_ID: &str = "a6e3e7d1-6dca-4a75-999f-73b646ceb1fa";
    const CODEX_ID: &str = "01a032cd-cef2-73c0-9714-b61b36ae4513";

    #[test]
    fn the_shared_accept_vectors_are_allowlisted_and_stay_canonical() {
        let accept = vectors().accept;
        assert!(accept.len() >= 2, "expected at least two accept vectors");
        for vector in accept {
            let parsed = url(&vector.link);
            assert_eq!(validate_session_link(&parsed), Ok(()), "{}", vector.link);
            // What is validated is exactly what the opener would receive.
            assert_eq!(parsed.as_str(), vector.link);
        }
    }

    #[test]
    fn the_shared_reject_vectors_are_refused() {
        let reject = vectors().reject_links;
        assert!(!reject.is_empty());
        for link in reject {
            // A link that does not even parse is refused before it gets here.
            if let Ok(parsed) = Url::parse(&link) {
                assert!(
                    validate_session_link(&parsed).is_err(),
                    "{link} must be refused"
                );
            }
        }
    }

    #[test]
    fn session_links_are_still_not_plain_web_links() {
        for vector in vectors().accept {
            assert!(
                validate_url(&url(&vector.link)).is_err(),
                "validate_url must keep refusing {}",
                vector.link
            );
        }
        assert!(validate_session_link(&url("https://github.com/xenotaur")).is_err());
        assert!(validate_session_link(&url("http://127.0.0.1:50543/meta")).is_err());
    }

    #[test]
    fn near_miss_session_links_are_refused() {
        let accept = vectors().accept;
        let first = accept[0].link.as_str();
        let lookalikes = [
            // A host that merely contains or extends the allowed one.
            first.replacen("://", "://x", 1),
            first.replacen("://", "://evil.example/", 1),
            format!("{first}/extra"),
            format!("{first}/"),
            format!("{first}?x=1"),
            format!("{first}?"),
            format!("{first}#frag"),
            first.replacen("://", "://user@", 1),
            first.replacen("://", "://user:secret@", 1),
            // Not the allowlisted scheme.
            first.replacen("claude:", "https:", 1),
            "javascript:alert(1)".to_string(),
            "file:///etc/passwd".to_string(),
            "tauri://localhost/index.html".to_string(),
            "vscode://file/etc/passwd".to_string(),
            "slack://open".to_string(),
            // Ids that are not UUIDs.
            format!("{}not-a-uuid", &first[..first.len() - CLAUDE_ID.len()]),
            format!(
                "{}{}",
                &first[..first.len() - CLAUDE_ID.len()],
                &CLAUDE_ID[..35]
            ),
            format!("{}{CLAUDE_ID}0", &first[..first.len() - CLAUDE_ID.len()]),
            format!(
                "{}%61{}",
                &first[..first.len() - CLAUDE_ID.len()],
                &CLAUDE_ID[1..]
            ),
        ];
        for link in lookalikes {
            if let Ok(parsed) = Url::parse(&link) {
                assert!(
                    validate_session_link(&parsed).is_err(),
                    "{link} must be refused"
                );
            }
        }
    }

    #[test]
    fn a_port_is_refused_even_on_an_allowlisted_host() {
        for vector in vectors().accept {
            let (scheme, rest) = vector.link.split_once("://").unwrap();
            let (host, path) = rest.split_once('/').unwrap();
            let link = format!("{scheme}://{host}:8080/{path}");
            assert!(validate_session_link(&url(&link)).is_err(), "{link}");
        }
    }

    #[test]
    fn id_case_does_not_matter_but_shape_does() {
        for vector in vectors().accept {
            // Scheme and host are matched exactly, so only the id is recased.
            let (head, id) = vector.link.split_at(vector.link.len() - 36);
            let cased = format!("{head}{}", id.to_ascii_uppercase());
            assert_eq!(validate_session_link(&url(&cased)), Ok(()), "{cased}");
        }
        assert!(is_uuid(CLAUDE_ID));
        assert!(is_uuid(CODEX_ID));
        assert!(is_uuid(&CODEX_ID.to_ascii_uppercase()));
        assert!(!is_uuid(""));
        assert!(!is_uuid("a6e3e7d16dca4a75999f73b646ceb1fa"));
        assert!(!is_uuid("a6e3e7d1-6dca-4a75-999f-73b646ceb1fg"));
        assert!(!is_uuid(&format!("{CLAUDE_ID} ")));
    }

    #[test]
    fn a_malformed_definition_is_an_error_not_a_guess() {
        let good = r#"{"schema_version":1,"vendors":[{"name":"x","scheme":"x","host":"h","path_template":"/{id}","id_prefix":"","id_shape":"uuid"}]}"#;
        assert!(parse_session_routes(good).is_ok());
        for bad in [
            "{not json",
            r#"{"schema_version":2,"vendors":[]}"#,
            r#"{"schema_version":1,"vendors":[]}"#,
            r#"{"schema_version":1}"#,
            &good.replace(r#""id_shape":"uuid""#, r#""id_shape":"integer""#),
            &good.replace("/{id}", "/fixed"),
            &good.replace("/{id}", "/{id}/{id}"),
            &good.replace("/{id}", "{id}"),
            &good.replace(r#""scheme":"x""#, r#""scheme":"X""#),
            &good.replace(r#""host":"h""#, r#""host":"""#),
        ] {
            assert!(parse_session_routes(bad).is_err(), "{bad} must be an error");
        }
    }

    #[test]
    fn the_embedded_definition_loads() {
        let routes = session_routes().expect("the embedded definition is valid");
        assert!(routes.len() >= 2);
    }

    #[test]
    fn production_code_writes_no_vendor_route() {
        let source = include_str!("browser.rs");
        let production = source.split("#[cfg(test)]").next().unwrap();
        for forbidden in ["epitaxy", "claude.ai", "codex://", "claude://", "threads"] {
            assert!(
                !production.contains(forbidden),
                "browser.rs production code must not hard-code {forbidden}; it belongs in the shared definition"
            );
        }
    }

    fn must_not_launch(url: &Url) -> Result<(), String> {
        panic!("a refused link reached the launcher: {url}");
    }

    fn pretend_launch(_url: &Url) -> Result<(), String> {
        Ok(())
    }

    fn failing_launch(_url: &Url) -> Result<(), String> {
        Err("the app opener failed (exit status: 1)".to_string())
    }

    #[test]
    fn a_refused_link_never_reaches_the_launcher() {
        let first = vectors().accept[0].link.clone();
        for refused in [
            "https://example.com/".to_string(),
            "javascript:alert(1)".to_string(),
            "http://127.0.0.1:50543/meta".to_string(),
            format!("{first}/extra"),
            format!("{first}?x=1"),
            first.replacen("://", "://user@", 1),
            format!("{}not-a-uuid", &first[..first.len() - 36]),
        ] {
            let result = open_session_link_with(&url(&refused), must_not_launch);
            assert!(result.is_err(), "{refused} must be refused");
        }
    }

    #[test]
    fn an_allowlisted_link_reaches_the_launcher_and_reports_the_app() {
        for vector in vectors().accept {
            let parsed = url(&vector.link);
            let handoff = open_session_link_with(&parsed, pretend_launch).unwrap();
            assert_eq!(handoff.opened, Opened::VendorApp);
            assert_eq!(
                handoff.note,
                Some(format!("{} session link", parsed.scheme()))
            );
        }
    }

    #[test]
    fn a_failed_launch_is_an_error_not_a_handoff() {
        let link = url(&vectors().accept[0].link);
        assert_eq!(
            open_session_link_with(&link, failing_launch),
            Err("the app opener failed (exit status: 1)".to_string())
        );
    }

    /// What actually runs, without running it: a fixed program chosen per
    /// platform, no shell, and the validated URL as the only argument.
    #[cfg(unix)]
    #[test]
    fn the_session_link_opener_is_a_fixed_program_with_only_the_url() {
        for vector in vectors().accept {
            let link = url(&vector.link);
            let command = session_link_command(&link);

            #[cfg(target_os = "macos")]
            assert_eq!(command.get_program(), "/usr/bin/open");
            #[cfg(all(unix, not(target_os = "macos")))]
            assert_eq!(command.get_program(), "/usr/bin/xdg-open");

            let args: Vec<_> = command.get_args().collect();
            assert_eq!(args, [std::ffi::OsStr::new(link.as_str())]);
        }
    }

    #[test]
    fn the_scheme_is_case_normalized_before_validation_and_launch() {
        // The url crate lowercases the scheme, so the opener only ever sees the
        // canonical form. (The Python helper compares raw text and is stricter.)
        let first = vectors().accept[0].link.clone();
        let (scheme, rest) = first.split_once("://").unwrap();
        let shouty = url(&format!("{}://{rest}", scheme.to_ascii_uppercase()));
        assert_eq!(shouty.as_str(), first);
        assert_eq!(validate_session_link(&shouty), Ok(()));
    }
}
