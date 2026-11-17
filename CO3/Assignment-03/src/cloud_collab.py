"""
Core engine for the cloud collaboration prototype (Q5, Q6, Q7).
Models what a cloud workspace provides: sharing, role-based permissions,
version history, concurrent-edit conflict detection and an audit log.
"""
import datetime

ROLE_RIGHTS = {
    "owner": {"read", "comment", "edit", "share", "delete"},
    "editor": {"read", "comment", "edit"},
    "commenter": {"read", "comment"},
    "viewer": {"read"},
}


class PermissionDenied(Exception):
    pass


class ConflictError(Exception):
    pass


class Workspace:
    def __init__(self, name, owner):
        self.name = name
        self.members = {owner: "owner"}
        self.docs = {}
        self.audit = []

    def _log(self, user, action, doc, note=""):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.audit.append(f"[{stamp}] {user:8} {action:9} {doc} {note}".rstrip())

    def _check(self, user, right):
        role = self.members.get(user)
        if role is None:
            raise PermissionDenied(f"{user} is not a member of '{self.name}'")
        if right not in ROLE_RIGHTS[role]:
            raise PermissionDenied(f"{user} ({role}) lacks '{right}' permission")
        return role

    def share(self, actor, user, role):
        self._check(actor, "share")
        self.members[user] = role
        self._log(actor, "share", user, f"-> {role}")

    def create(self, actor, doc, text):
        self._check(actor, "edit")
        self.docs[doc] = {"versions": [(actor, text)], "comments": []}
        self._log(actor, "create", doc, "v1")

    def read(self, actor, doc):
        self._check(actor, "read")
        return self.docs[doc]["versions"][-1][1]

    def version(self, doc):
        return len(self.docs[doc]["versions"])

    def edit(self, actor, doc, text, base_version):
        """base_version = version the user was looking at when they started editing."""
        self._check(actor, "edit")
        if base_version != self.version(doc):
            raise ConflictError(f"{actor} edited v{base_version} but latest is v{self.version(doc)} - merge needed")
        self.docs[doc]["versions"].append((actor, text))
        self._log(actor, "edit", doc, f"v{self.version(doc)}")

    def comment(self, actor, doc, text):
        self._check(actor, "comment")
        self.docs[doc]["comments"].append((actor, text))
        self._log(actor, "comment", doc)

    def history(self, doc):
        return [f"v{i + 1} by {a}" for i, (a, _) in enumerate(self.docs[doc]["versions"])]
