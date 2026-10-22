# Local Vulnerable Test Site

**⚠️ INTENTIONALLY INSECURE. LOCAL SCANNER-TESTING ONLY. DO NOT DEPLOY. ⚠️**

A tiny Flask app containing deliberate OWASP Top 10 (2021) weaknesses, so you
can point a security scanner at a target you own and confirm it reports what it
should. It binds to `127.0.0.1:5000` only.

## Run

```bash
pip install flask
python3 app.py
# open http://127.0.0.1:5000/
```

Then point your scanner at `http://127.0.0.1:5000/`.

## Intentional issues (map scanner findings to these)

| Route | OWASP 2021 | Issue |
|-------|-----------|-------|
| `/search?q=` | A03 Injection | Reflected XSS / SSTI |
| `/login` | A03 Injection | SQL injection (`admin' --`) |
| `/profile?id=` | A01 Broken Access Control | IDOR, no authz |
| `/ping?host=` | A03 Injection | OS command injection |
| `/fetch?url=` | A10 SSRF | Fetches any URL |
| `/download?file=` | A01 Broken Access Control | Path traversal |
| `/load?data=` | A08 Integrity Failures | Insecure deserialization (pickle) |
| `/redirect?next=` | A01 Broken Access Control | Open redirect |
| `/debug` | A05 Security Misconfiguration | Secret/env disclosure, no security headers, debug mode |

Also present throughout: hardcoded secrets (A02), plaintext passwords (A02),
and missing security headers (A05).

## Safety

- Keep the bind address at `127.0.0.1`. Never change it to `0.0.0.0`.
- Never feed it real credentials or data.
- Delete the SQLite file (`/tmp/vuln_testsite.db`) when done.
