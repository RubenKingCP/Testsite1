"""
============================================================================
  INTENTIONALLY VULNERABLE TEST TARGET  --  LOCAL USE ONLY
============================================================================
This application contains DELIBERATE security vulnerabilities. It exists
solely so you can point a security scanner at a target you own and confirm
the scanner reports the issues it should.

  * DO NOT deploy this anywhere reachable from the internet.
  * DO NOT put real data in it.
  * It binds to 127.0.0.1 (loopback) on purpose -- keep it that way.

Each vulnerable route is annotated with the OWASP Top 10 (2021) category it
demonstrates, so you can map scanner findings back to expected results.
============================================================================
"""

import os
import sqlite3
import subprocess
import pickle
import base64

from flask import Flask, request, render_template_string, make_response, redirect

app = Flask(__name__)

# [A02:2021 Cryptographic Failures] Hardcoded secret committed to source.
# A scanner / secret-detector should flag this.
app.secret_key = "super-secret-hardcoded-key-123"
API_TOKEN = "AKIAIOSFODNN7EXAMPLE"  # fake AWS-style key shape for secret scanners

DB_PATH = "/tmp/vuln_testsite.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users "
              "(id INTEGER PRIMARY KEY, username TEXT, password TEXT, note TEXT)")
    c.execute("DELETE FROM users")
    # [A02] Passwords stored in plaintext.
    seed = [
        (1, "alice", "password123", "alice private note"),
        (2, "bob", "hunter2", "bob private note"),
        (3, "admin", "admin", "admin secret note"),
    ]
    c.executemany("INSERT INTO users VALUES (?,?,?,?)", seed)
    conn.commit()
    conn.close()


PAGE = """
<!doctype html>
<title>Vuln Test Site</title>
<h1>Local Vulnerable Test Site</h1>
<p style="color:red"><b>Intentionally insecure. Local scanner-testing only.</b></p>
<ul>
  <li><a href="/search?q=test">/search?q=</a> &ndash; reflected XSS (A03)</li>
  <li><a href="/login">/login</a> &ndash; SQL injection (A03)</li>
  <li><a href="/profile?id=1">/profile?id=1</a> &ndash; IDOR / broken access control (A01)</li>
  <li><a href="/ping?host=127.0.0.1">/ping?host=</a> &ndash; command injection (A03)</li>
  <li><a href="/fetch?url=http://127.0.0.1:5000/">/fetch?url=</a> &ndash; SSRF (A10)</li>
  <li><a href="/download?file=app.py">/download?file=</a> &ndash; path traversal (A01)</li>
  <li><a href="/load?data=">/load?data=</a> &ndash; insecure deserialization (A08)</li>
  <li><a href="/redirect?next=/">/redirect?next=</a> &ndash; open redirect (A01)</li>
  <li><a href="/debug">/debug</a> &ndash; security misconfiguration / info leak (A05)</li>
</ul>
"""


@app.route("/")
def index():
    return PAGE


# ---------------------------------------------------------------------------
# [A03:2021 Injection] Reflected Cross-Site Scripting.
# User input is rendered into the page without escaping.
# ---------------------------------------------------------------------------
@app.route("/search")
def search():
    q = request.args.get("q", "")
    # render_template_string on attacker-controlled input -> XSS (and SSTI).
    return render_template_string(
        "<h2>Results for " + q + "</h2><p>Nothing found.</p>")


# ---------------------------------------------------------------------------
# [A03:2021 Injection] SQL Injection via string-concatenated query.
# Try username:  admin' --
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <form method="post">
          user: <input name="username">
          pass: <input name="password" type="password">
          <button>login</button>
        </form>"""
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = ("SELECT * FROM users WHERE username = '" + username +
             "' AND password = '" + password + "'")
    rows = c.execute(query).fetchall()
    conn.close()
    if rows:
        return "Welcome, " + str(rows[0][1])
    return "Invalid credentials"


# ---------------------------------------------------------------------------
# [A01:2021 Broken Access Control] IDOR -- any id returns any user's note
# with no authentication or ownership check.
# ---------------------------------------------------------------------------
@app.route("/profile")
def profile():
    uid = request.args.get("id", "1")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute("SELECT username, note FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    if not row:
        return "no such user"
    return "User: %s<br>Private note: %s" % (row[0], row[1])


# ---------------------------------------------------------------------------
# [A03:2021 Injection] OS Command Injection.
# host is passed to a shell. Try:  127.0.0.1; id
# ---------------------------------------------------------------------------
@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    out = subprocess.run("ping -c 1 " + host, shell=True,
                         capture_output=True, text=True)
    return "<pre>" + out.stdout + out.stderr + "</pre>"


# ---------------------------------------------------------------------------
# [A10:2021 Server-Side Request Forgery] Fetches any URL the client gives.
# ---------------------------------------------------------------------------
@app.route("/fetch")
def fetch():
    import urllib.request
    url = request.args.get("url", "")
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return "<pre>" + r.read(2000).decode("utf-8", "replace") + "</pre>"
    except Exception as e:
        return "error: " + str(e)


# ---------------------------------------------------------------------------
# [A01:2021 Broken Access Control] Path traversal.
# Try:  /download?file=../etc/hostname
# ---------------------------------------------------------------------------
@app.route("/download")
def download():
    name = request.args.get("file", "app.py")
    path = os.path.join(os.getcwd(), name)
    try:
        with open(path) as f:
            return "<pre>" + f.read() + "</pre>"
    except Exception as e:
        return "error: " + str(e)


# ---------------------------------------------------------------------------
# [A08:2021 Software and Data Integrity Failures] Insecure deserialization.
# Unpickles attacker-supplied base64 data.
# ---------------------------------------------------------------------------
@app.route("/load")
def load():
    data = request.args.get("data", "")
    if not data:
        return "pass ?data=<base64 pickle>"
    try:
        obj = pickle.loads(base64.b64decode(data))
        return "loaded: " + str(obj)
    except Exception as e:
        return "error: " + str(e)


# ---------------------------------------------------------------------------
# [A01:2021 Broken Access Control] Open redirect.
# ---------------------------------------------------------------------------
@app.route("/redirect")
def open_redirect():
    return redirect(request.args.get("next", "/"))


# ---------------------------------------------------------------------------
# [A05:2021 Security Misconfiguration] Information disclosure endpoint,
# and no security headers are set anywhere in the app.
# ---------------------------------------------------------------------------
@app.route("/debug")
def debug():
    resp = make_response(
        "secret_key=%s\napi_token=%s\nenv=%s" %
        (app.secret_key, API_TOKEN, dict(os.environ)))
    resp.headers["Content-Type"] = "text/plain"
    return resp


if __name__ == "__main__":
    init_db()
    # Bound to loopback ONLY. Do not change host to 0.0.0.0.
    # debug=True (Werkzeug debugger) is itself an intentional misconfiguration.
    app.run(host="127.0.0.1", port=5000, debug=True)
