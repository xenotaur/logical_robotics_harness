//! Narrow browser handoff: open one `http(s)` URL in Chrome or the default
//! browser.
//!
//! No shell is involved. The opener is a fixed program with fixed arguments,
//! and the URL is validated first. Handoffs are rate-limited so page content
//! cannot flood the browser with tabs.

use std::process::{Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::Url;

use crate::settings::BrowserChoice;

/// At most one handoff per this interval.
pub const MIN_HANDOFF_INTERVAL: Duration = Duration::from_secs(1);

/// The macOS application name used for Chrome.
pub const CHROME_APP: &str = "Google Chrome";

/// Which browser a handoff actually used.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Opened {
    Chrome,
    DefaultBrowser,
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

#[cfg(unix)]
fn run(command: &mut Command) -> Result<(), String> {
    let status = command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|error| format!("could not start the browser opener: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("the browser opener failed ({status})"))
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
}
