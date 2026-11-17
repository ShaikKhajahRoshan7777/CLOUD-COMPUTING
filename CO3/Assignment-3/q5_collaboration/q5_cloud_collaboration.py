"""
Q5 - Collaboration Using Cloud-Based Services
Simulates a shared cloud workspace: one master copy, role-based sharing,
version history, concurrent-edit conflict detection and an audit log.
"""
import threading
from datetime import datetime

ROLES = {"owner": {"view", "edit", "share"}, "editor": {"view", "edit"},
         "viewer": {"view"}}


class SharedDocument:
    def __init__(self, title, owner, text):
        self.title, self.members = title, {owner: "owner"}
        self.versions = [(1, owner, text)]          # (version, author, content)
        self.log, self._lock = [], threading.Lock()
        self._audit(owner, "created document")

    def _audit(self, user, msg):
        self.log.append(f"{datetime.now():%H:%M:%S}  {user:<6} {msg}")

    @property
    def current(self):
        return self.versions[-1]

    def share(self, by, user, role):
        self._need(by, "share")
        self.members[user] = role
        self._audit(by, f"shared with {user} as {role.upper()}")

    def _need(self, user, action):
        role = self.members.get(user)
        if role is None or action not in ROLES[role]:
            self._audit(user, f"DENIED {action}")
            raise PermissionError(f"{user} ({role or 'no access'}) cannot {action}")

    def edit(self, user, text, base_version):
        with self._lock:                              # concurrent access control
            self._need(user, "edit")
            if base_version != self.current[0]:
                self._audit(user, f"CONFLICT (had v{base_version}, latest v{self.current[0]})")
                raise ValueError(f"edit conflict - refresh to v{self.current[0]}")
            v = self.current[0] + 1
            self.versions.append((v, user, text))
            self._audit(user, f"saved version v{v}")
            return v


if __name__ == "__main__":
    print("=" * 70)
    print("  Q5 : CLOUD COLLABORATION  -  shared workspace simulation")
    print("=" * 70)
    doc = SharedDocument("Project Report", "alice", "Draft: intro")
    doc.share("alice", "bob", "editor")
    doc.share("alice", "carol", "viewer")
    print(f"Workspace : '{doc.title}'  members = {doc.members}")

    print("\n[Activity 1] Bob (editor) adds a section")
    print("  ->", "saved as v%d" % doc.edit("bob", "Draft: intro + methods", 1))

    print("[Activity 2] Carol (viewer) tries to edit")
    try:
        doc.edit("carol", "hack", 2)
    except PermissionError as e:
        print("  -> blocked:", e)

    print("[Activity 3] Alice edits with a stale copy (still on v1)")
    try:
        doc.edit("alice", "Draft: intro + results", 1)
    except ValueError as e:
        print("  -> blocked:", e)
        print("  -> retry after refresh: saved as v%d" %
              doc.edit("alice", "Draft: intro + methods + results", doc.current[0]))

    print("\nVersion history")
    for v, who, text in doc.versions:
        print(f"  v{v}  by {who:<6} {text}")
    print("\nAudit log")
    for line in doc.log:
        print("  " + line)
    n_users = len(doc.members)
    print(f"\nCopies of the file: cloud = 1  |  e-mail attachments = {n_users * len(doc.versions)}")
