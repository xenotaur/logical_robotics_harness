## 2026-07-06 - Add security headers to lrh serve
**Vulnerability:** The local `lrh serve` HTTP server was missing security headers like `Content-Security-Policy`, `X-Content-Type-Options`, and `X-Frame-Options`, leaving it potentially susceptible to MIME sniffing, clickjacking, and XSS (Cross-Site Scripting) vectors through rendered project content.
**Learning:** Even read-only local viewers processing external or repository state benefit from strict defense-in-depth security headers, especially CSP when inline styles are used but scripts are forbidden.
**Prevention:** Always implement strong, restrictive security headers (e.g., CSP `default-src 'none'`) on internal HTTP servers handling untrusted state.
