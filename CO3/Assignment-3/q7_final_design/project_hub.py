"""
Q7 - Design Challenge : CloudCollab Hub
A cloud-based collaborative student-project workspace.

Architecture:
Users -> Client (web / mobile / API) -> Internet (HTTPS) -> Cloud Platform
      -> Application / API layer -> Shared Resources (tasks, files, versions)
"""
import hashlib
import secrets
import threading
import time

PERMISSIONS = {"lead": {"read", "write", "assign", "manage"},
               "member": {"read", "write"},
               "mentor": {"read"}}


class AccessError(Exception):
    pass


class ConflictError(Exception):
    pass


class ProjectHub:
    def __init__(self):
        self.users, self.sessions, self.projects = {}, {}, {}
        self.audit, self._lock = [], threading.Lock()

    # ---- authentication ------------------------------------------------
    def register(self, user, password):
        salt = secrets.token_bytes(8)
        self.users[user] = (salt, hashlib.sha256(salt + password.encode()).hexdigest())

    def login(self, user, password, ttl=600):
        rec = self.users.get(user)
        if not rec or hashlib.sha256(rec[0] + password.encode()).hexdigest() != rec[1]:
            self.audit.append((user, "LOGIN_FAILED"))
            raise AccessError("invalid credentials")
        token = secrets.token_urlsafe(16)
        self.sessions[token] = (user, time.time() + ttl)
        self.audit.append((user, "LOGIN_OK"))
        return token

    def _user(self, token):
        s = self.sessions.get(token)
        if not s or s[1] < time.time():
            raise AccessError("session invalid or expired")
        return s[0]

    # ---- authorization -------------------------------------------------
    def _check(self, token, project, action):
        user = self._user(token)
        role = self.projects[project]["members"].get(user)
        if not role or action not in PERMISSIONS[role]:
            self.audit.append((user, f"DENIED_{action.upper()}"))
            raise AccessError(f"{user} ({role or 'not a member'}) cannot {action}")
        return user

    # ---- collaboration -------------------------------------------------
    def create_project(self, token, name):
        user = self._user(token)
        self.projects[name] = {"members": {user: "lead"}, "tasks": [], "files": {}}
        self.audit.append((user, f"CREATE_PROJECT:{name}"))

    def add_member(self, token, project, member, role):
        self._check(token, project, "manage")
        self.projects[project]["members"][member] = role

    def add_task(self, token, project, title, assignee):
        user = self._check(token, project, "assign")
        self.projects[project]["tasks"].append({"title": title, "to": assignee, "done": False})
        self.audit.append((user, f"TASK:{title}"))

    def complete_task(self, token, project, index):
        user = self._check(token, project, "write")
        self.projects[project]["tasks"][index]["done"] = True
        self.audit.append((user, f"DONE:{index}"))

    def save_file(self, token, project, name, text, base_version):
        with self._lock:
            user = self._check(token, project, "write")
            versions = self.projects[project]["files"].setdefault(name, [])
            if base_version != len(versions):
                raise ConflictError(f"{name}: latest is v{len(versions)}")
            versions.append((user, text))
            return len(versions)

    def read_file(self, token, project, name):
        self._check(token, project, "read")
        return self.projects[project]["files"][name][-1]


class OfflineClient:
    """Queues changes while the network is down and syncs on reconnect."""
    def __init__(self, hub, token, project):
        self.hub, self.token, self.project = hub, token, project
        self.online, self.queue = True, []

    def save(self, name, text, base_version):
        if not self.online:
            self.queue.append((name, text, base_version))
            return "queued"
        return self.hub.save_file(self.token, self.project, name, text, base_version)

    def reconnect(self):
        self.online, synced = True, 0
        while self.queue:
            self.hub.save_file(self.token, self.project, *self.queue.pop(0))
            synced += 1
        return synced


def demo():
    hub = ProjectHub()
    for u, p in [("lead", "L#1"), ("member", "M#2"), ("mentor", "T#3")]:
        hub.register(u, p)
    t = {u: hub.login(u, p) for u, p in [("lead", "L#1"), ("member", "M#2"), ("mentor", "T#3")]}
    print("=" * 74)
    print("  Q7 : CloudCollab Hub  -  complete workflow")
    print("=" * 74)
    hub.create_project(t["lead"], "CloudApp")
    hub.add_member(t["lead"], "CloudApp", "member", "member")
    hub.add_member(t["lead"], "CloudApp", "mentor", "mentor")
    print("1. Lead creates project 'CloudApp' and invites member + mentor")
    hub.add_task(t["lead"], "CloudApp", "Design architecture", "member")
    print("2. Lead assigns task -> 'Design architecture' to member")
    print("3. Member saves design.md  -> version v%d" %
          hub.save_file(t["member"], "CloudApp", "design.md", "Architecture v1", 0))
    hub.complete_task(t["member"], "CloudApp", 0)
    print("4. Member marks task as completed")
    print("5. Mentor reads latest file ->", hub.read_file(t["mentor"], "CloudApp", "design.md"))
    print("6. Project state :", hub.projects["CloudApp"]["tasks"])
    print("7. Audit trail   :", len(hub.audit), "events recorded")


if __name__ == "__main__":
    demo()
