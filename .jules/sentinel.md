## 2026-07-06 - Add security headers to lrh serve
**Vulnerability:** The local `lrh serve` HTTP server was missing security headers like `Content-Security-Policy`, `X-Content-Type-Options`, and `X-Frame-Options`, leaving it potentially susceptible to MIME sniffing, clickjacking, and XSS (Cross-Site Scripting) vectors through rendered project content.
**Learning:** Even read-only local viewers processing external or repository state benefit from strict defense-in-depth security headers, especially CSP when inline styles are used but scripts are forbidden.
**Prevention:** Always implement strong, restrictive security headers (e.g., CSP `default-src 'none'`) on internal HTTP servers handling untrusted state.
## 2025-02-14 - Fix permissions race condition in secrets scan
**Vulnerability:** The secrets scanner (`lrh secrets scan`) generated output files containing sensitive API keys and secrets with default Umask permissions, leaving them briefly world-readable before being restricted later via chmod.
**Learning:** Writing sensitive data and restricting permissions sequentially introduces a local file disclosure race condition. The subprocess generating the data or standard file-open calls create files based on process umask.
**Prevention:** Pre-create destination files with restricted permissions (`touch(mode=0o600)`) before any write operation or subprocess call writes sensitive data to them.
