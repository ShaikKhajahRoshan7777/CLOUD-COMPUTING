"""Q7 - Experimental validation: expected vs observed behaviour."""
import threading
import time
import unittest

from project_hub import AccessError, ConflictError, OfflineClient, ProjectHub


class TestCloudCollabHub(unittest.TestCase):
    def setUp(self):
        self.hub = ProjectHub()
        for u in ("lead", "member", "mentor", "outsider"):
            self.hub.register(u, u + "#pw")
        self.t = {u: self.hub.login(u, u + "#pw") for u in ("lead", "member", "mentor", "outsider")}
        self.hub.create_project(self.t["lead"], "P1")
        self.hub.add_member(self.t["lead"], "P1", "member", "member")
        self.hub.add_member(self.t["lead"], "P1", "mentor", "mentor")

    def test_01_valid_login_returns_token(self):
        self.assertTrue(self.hub.login("lead", "lead#pw"))

    def test_02_wrong_password_rejected(self):
        with self.assertRaises(AccessError):
            self.hub.login("lead", "wrong")

    def test_03_lead_can_assign_task(self):
        self.hub.add_task(self.t["lead"], "P1", "Write report", "member")
        self.assertEqual(len(self.hub.projects["P1"]["tasks"]), 1)

    def test_04_member_cannot_manage_members(self):
        with self.assertRaises(AccessError):
            self.hub.add_member(self.t["member"], "P1", "outsider", "member")

    def test_05_mentor_is_read_only(self):
        with self.assertRaises(AccessError):
            self.hub.save_file(self.t["mentor"], "P1", "a.md", "x", 0)

    def test_06_non_member_denied(self):
        with self.assertRaises(AccessError):
            self.hub.read_file(self.t["outsider"], "P1", "a.md")

    def test_07_file_versioning(self):
        self.assertEqual(self.hub.save_file(self.t["member"], "P1", "a.md", "v1", 0), 1)
        self.assertEqual(self.hub.save_file(self.t["lead"], "P1", "a.md", "v2", 1), 2)

    def test_08_stale_edit_conflict_detected(self):
        self.hub.save_file(self.t["member"], "P1", "a.md", "v1", 0)
        with self.assertRaises(ConflictError):
            self.hub.save_file(self.t["lead"], "P1", "a.md", "stale", 0)

    def test_09_expired_session_rejected(self):
        old = self.hub.login("member", "member#pw", ttl=-1)
        with self.assertRaises(AccessError):
            self.hub.read_file(old, "P1", "a.md")

    def test_10_offline_changes_sync_after_reconnect(self):
        c = OfflineClient(self.hub, self.t["member"], "P1")
        c.online = False
        self.assertEqual(c.save("n.md", "offline note", 0), "queued")
        self.assertEqual(c.reconnect(), 1)
        self.assertEqual(self.hub.read_file(self.t["lead"], "P1", "n.md")[1], "offline note")

    def test_11_fifty_concurrent_users_scalability(self):
        hub = self.hub
        for i in range(50):
            hub.register(f"u{i}", "pw")
            hub.projects["P1"]["members"][f"u{i}"] = "member"
        toks = [hub.login(f"u{i}", "pw") for i in range(50)]
        done = []

        def work(tok):
            for _ in range(20):
                try:
                    v = len(hub.projects["P1"]["files"].get("shared.md", []))
                    hub.save_file(tok, "P1", "shared.md", "x", v)
                    done.append(1)
                    return
                except ConflictError:
                    time.sleep(0.001)

        th = [threading.Thread(target=work, args=(t,)) for t in toks]
        [x.start() for x in th]
        [x.join() for x in th]
        self.assertEqual(len(hub.projects["P1"]["files"]["shared.md"]), len(done))

    def test_12_audit_log_records_denied_access(self):
        with self.assertRaises(AccessError):
            self.hub.save_file(self.t["mentor"], "P1", "a.md", "x", 0)
        self.assertIn(("mentor", "DENIED_WRITE"), self.hub.audit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
