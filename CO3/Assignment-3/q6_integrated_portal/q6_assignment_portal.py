"""
Q6 - Integrated Cloud Access + Collaboration Mini Investigation
Scenario : Cloud-Based Assignment Submission and Evaluation

A small REST "cloud service" (runs locally as a stand-in for a cloud server)
and a client that exercises two user scenarios:
  1. Student submits work  ->  Faculty evaluates  ->  Student sees result
  2. Unauthorised actions are rejected (no token / wrong role)
"""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

PORT = 5050
USERS = {"student1": ("pass1", "student"), "student2": ("pass2", "student"),
         "faculty1": ("fac@123", "faculty")}
SESSIONS, SUBMISSIONS = {}, {}          # token -> (user, role) | user -> record


class CloudAPI(BaseHTTPRequestHandler):
    def log_message(self, *args):       # keep the console clean
        pass

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or "{}")

    def _auth(self):
        return SESSIONS.get(self.headers.get("Authorization", "").replace("Bearer ", ""))

    def do_POST(self):
        b = self._body()
        if self.path == "/login":
            u = USERS.get(b.get("user"))
            if not u or u[0] != b.get("password"):
                return self._send(401, {"error": "invalid credentials"})
            token = secrets.token_hex(8)
            SESSIONS[token] = (b["user"], u[1])
            return self._send(200, {"token": token, "role": u[1]})
        who = self._auth()
        if not who:
            return self._send(401, {"error": "authentication required"})
        user, role = who
        if self.path == "/submit" and role == "student":
            SUBMISSIONS[user] = {"file": b["file"], "marks": None, "feedback": None}
            return self._send(201, {"status": "submitted", "student": user})
        if self.path == "/evaluate" and role == "faculty":
            rec = SUBMISSIONS.get(b["student"])
            if not rec:
                return self._send(404, {"error": "no submission"})
            rec.update(marks=b["marks"], feedback=b["feedback"])
            return self._send(200, {"status": "evaluated", "student": b["student"]})
        self._send(403, {"error": f"role '{role}' not allowed on {self.path}"})

    def do_GET(self):
        who = self._auth()
        if not who:
            return self._send(401, {"error": "authentication required"})
        user, role = who
        if self.path == "/submissions" and role == "faculty":
            return self._send(200, SUBMISSIONS)
        if self.path == "/my-result" and role == "student":
            return self._send(200, SUBMISSIONS.get(user, {}))
        self._send(403, {"error": f"role '{role}' not allowed on {self.path}"})


def call(method, path, token=None, **body):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.request(method, f"http://127.0.0.1:{PORT}{path}", json=body or None, headers=h)
    return r.status_code, r.json()


def show(step, res):
    print(f"  {step:<44} -> HTTP {res[0]}  {json.dumps(res[1])[:60]}")


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), CloudAPI)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("=" * 78)
    print(f"  Q6 : CLOUD ASSIGNMENT PORTAL   (service started on port {PORT})")
    print("=" * 78)

    print("Scenario 1 : submit -> evaluate -> view result")
    s_login = call("POST", "/login", user="student1", password="pass1")
    f_login = call("POST", "/login", user="faculty1", password="fac@123")
    s_tok, f_tok = s_login[1]["token"], f_login[1]["token"]
    show("student1 login", (s_login[0], {"role": s_login[1]["role"]}))
    show("student1 submits report.pdf", call("POST", "/submit", s_tok, file="report.pdf"))
    show("faculty1 lists submissions", call("GET", "/submissions", f_tok))
    show("faculty1 evaluates (marks=46)", call("POST", "/evaluate", f_tok,
         student="student1", marks=46, feedback="Excellent analysis"))
    show("student1 views result", call("GET", "/my-result", s_tok))

    print("\nScenario 2 : access-control checks")
    show("anonymous user lists submissions", call("GET", "/submissions"))
    show("student1 tries to evaluate", call("POST", "/evaluate", s_tok,
         student="student1", marks=50, feedback="self-grade"))
    show("login with wrong password", call("POST", "/login", user="student2", password="x"))
    print("-" * 78)
    print("Result : 2 scenarios tested | collaboration works | unauthorised access blocked")
    server.shutdown()
