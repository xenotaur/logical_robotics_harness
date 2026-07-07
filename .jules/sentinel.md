## 2026-07-06 - Add security headers to lrh serve
**Vulnerability:** The local `lrh serve` HTTP server was missing security headers like `Content-Security-Policy`, `X-Content-Type-Options`, and `X-Frame-Options`, leaving it potentially susceptible to MIME sniffing, clickjacking, and XSS (Cross-Site Scripting) vectors through rendered project content.
**Learning:** Even read-only local viewers processing external or repository state benefit from strict defense-in-depth security headers, especially CSP when inline styles are used but scripts are forbidden.
**Prevention:** Always implement strong, restrictive security headers (e.g., CSP `default-src 'none'`) on internal HTTP servers handling untrusted state.
## 2024-05-15 - [CRLF and Header Injection in File Downloads]
**Vulnerability:** File download filenames (`Content-Disposition: attachment; filename="..."`) used raw properties (`artifact.work_item_id`) without sanitization, allowing potential HTTP header injection (CRLF) or breaking out of the filename attribute.
**Learning:** Even internal or local-only web servers serving file downloads can be subject to header injection if user-provided strings contain double quotes or newline characters.
**Prevention:** Sanitize filename strings in `Content-Disposition` headers by removing `\r`, `\n`, and replacing `"` with safe characters like `_`.
