"""
Q7 - Stage 4 Experimental Validation: test cases for the 'SIMATS Cloud Project Hub'.
Expected vs observed behaviour for different users and access conditions.
Run:  python src/q7_validation_tests.py
"""
from cloud_collab import ConflictError, PermissionDenied, Workspace
from q4_auth_demo import access_resource, authenticate


def build():
    hub = Workspace("SIMATS-Cloud-Project-Hub", owner="faculty")
    hub.share("faculty", "asha", "editor")
    hub.share("faculty", "ravi", "editor")
    hub.share("faculty", "guest", "viewer")
    hub.create("asha", "Design.docx", "Initial design")
    return hub


def run(hub):
    cases = []

    def case(cid, desc, expected, fn):
        try:
            out = fn()
            observed = out if isinstance(out, str) else "ALLOWED"
        except PermissionDenied:
            observed = "DENIED"
        except ConflictError:
            observed = "CONFLICT"
        cases.append((cid, desc, expected, observed))

    asha, guest = authenticate("asha", "S3cure#Pass1"), authenticate("ravi", "V!ewOnly22")
    case("TC1", "Valid login, write via token", "200", lambda: access_resource(asha, "write")[:3])
    case("TC2", "Viewer token tries to delete", "403", lambda: access_resource(guest, "delete")[:3])
    case("TC3", "Request without valid token", "401", lambda: access_resource("bad.token", "read")[:3])
    case("TC4", "Editor edits shared file", "ALLOWED", lambda: hub.edit("asha", "Design.docx", "v2 by asha", 1))
    case("TC5", "Viewer (guest) reads file", "ALLOWED", lambda: hub.read("guest", "Design.docx") and None)
    case("TC6", "Viewer (guest) edits file", "DENIED", lambda: hub.edit("guest", "Design.docx", "x", 2))
    case("TC7", "Two editors, stale version", "CONFLICT", lambda: hub.edit("ravi", "Design.docx", "late", 1))
    case("TC8", "Non-member reads file", "DENIED", lambda: hub.read("outsider", "Design.docx"))
    case("TC9", "Editor tries to share workspace", "DENIED", lambda: hub.share("asha", "x", "editor"))
    return cases


def main():
    cases = run(build())
    print(f"{'ID':4}{'Test case':38}{'Expected':10}{'Observed':10}Result")
    print("-" * 70)
    passed = 0
    for cid, desc, exp, obs in cases:
        ok = exp == obs
        passed += ok
        print(f"{cid:4}{desc:38}{exp:10}{obs:10}{'PASS' if ok else 'FAIL'}")
    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(cases)} test cases passed")


if __name__ == "__main__":
    main()
