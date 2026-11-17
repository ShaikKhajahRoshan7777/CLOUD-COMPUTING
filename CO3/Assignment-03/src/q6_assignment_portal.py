"""
Q6 - Mini investigation: Cloud-Based Assignment Submission and Evaluation (prototype).
Cloud ACCESS (token login from two client types) + cloud COLLABORATION (shared workspace,
roles, versioning, comments). Two user scenarios are executed and logged.
Run:  python src/q6_assignment_portal.py
"""
from cloud_collab import ConflictError, PermissionDenied, Workspace
from q4_auth_demo import access_resource, authenticate


def banner(text):
    print("\n" + "=" * 64 + f"\n{text}\n" + "=" * 64)


def main():
    ws = Workspace("CSA15-Assignment-Portal", owner="admin")
    ws.share("admin", "asha", "editor")      # faculty-side collaborator / student A
    ws.share("admin", "ravi", "viewer")      # second student, read-only on rubric

    banner("SCENARIO 1 - Student submits from a LAPTOP BROWSER, faculty reviews from MOBILE APP")
    tok = authenticate("asha", "S3cure#Pass1")
    print("[browser ] login ........:", "token issued" if tok else "denied")
    print("[browser ] upload check .:", access_resource(tok, "write"))
    ws.create("asha", "Assignment3.docx", "Draft answer for Q1-Q3")
    print("[mobile  ] faculty opens :", ws.read("admin", "Assignment3.docx"))
    ws.comment("admin", "Assignment3.docx", "Add API response screenshot in Q3")
    ws.edit("asha", "Assignment3.docx", "Final answer with API screenshot", base_version=1)
    print("[system  ] version history:", ws.history("Assignment3.docx"))

    banner("SCENARIO 2 - Wrong permission and simultaneous edit")
    for label, fn in [
        ("viewer tries to edit    ", lambda: ws.edit("ravi", "Assignment3.docx", "hack", 2)),
        ("outsider tries to read  ", lambda: ws.read("stranger", "Assignment3.docx")),
        ("stale edit (conflict)   ", lambda: ws.edit("admin", "Assignment3.docx", "grade note", 1)),
    ]:
        try:
            fn()
            print(f"{label}: allowed")
        except (PermissionDenied, ConflictError) as exc:
            print(f"{label}: BLOCKED -> {exc}")

    banner("AUDIT LOG (accountability evidence)")
    print("\n".join(ws.audit))


if __name__ == "__main__":
    main()
