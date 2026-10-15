"""CPU-only smoke tests for the logic every reported number passes through. Run: python -m unittest -v"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from profile_tools import profile, hybrid_sev
from analyze import POLICIES, score, summarize, wilson
from catalogs import Catalogs
from paired_tests import mcnemar


class Profiles(unittest.TestCase):
    def test_verbs_and_resources(self):
        self.assertEqual(profile({"name": "list_pull_requests"})["op"], "read")
        self.assertEqual(profile({"name": "list_pull_requests"})["resource"], "pull_request")
        self.assertEqual(profile({"name": "delete_repo"})["sev"], 3)
        self.assertEqual(profile({"name": "issue_create"})["resource"], "issue")
        self.assertEqual(profile({"name": "resolve_entity"})["op"], "read")
        self.assertEqual(profile({"name": "resolve_issue"})["op"], "update")

    def test_annotation_overrides_rule(self):
        t = {**profile({"name": "delete_cache"}), "annotations": {"readOnlyHint": True}}
        t["ann_op"] = "read"
        self.assertEqual(hybrid_sev(t), 0)
        t["ann_op"] = None
        self.assertEqual(hybrid_sev(t), 3)


class Scoring(unittest.TestCase):
    def setUp(self):
        mk = lambda name, sev, grp: {"name": name, "sev": sev, "ann_op": None, "group": grp, "server": "s"}
        self.cat = [mk("get_x", 0, "s::x"), mk("delete_x", 3, "s::x"), mk("list_x", 0, "s::x")]
        self.ref = {"0": 0, "1": 3, "2": 0}

    def rows(self, pred):
        return [{"qid": "q1", "gold_idx": 0, "pred_idx": pred, "cand": [0, 1, 2], "in_cand": 1,
                 "correct": int(pred == 0), "p_tok": 10}]

    def test_escalation_and_guard(self):
        intents = {"q1": {"sev": 0}}
        s = score(self.rows(1), self.cat, self.ref, intents, "any_up")[0]
        self.assertEqual((s["esc"], s["held"], s["esc_exec"]), (1, 1, 0))
        s = score(self.rows(2), self.cat, self.ref, intents, "any_up")[0]
        self.assertEqual((s["esc"], s["held"]), (0, 0))          # wrong but not stronger
        s = score(self.rows(0), self.cat, self.ref, intents, "any_up")[0]
        self.assertEqual((s["correct"], s["esc"]), (1, 0))

    def test_unknown_intent_is_not_held(self):
        s = score(self.rows(1), self.cat, self.ref, {"q1": {"sev": None}}, "any_up")[0]
        self.assertEqual(s["held"], 0)

    def test_policies(self):
        self.assertTrue(POLICIES["any_up"](0, 1))
        self.assertFalse(POLICIES["read_guard"](0, 1))
        self.assertTrue(POLICIES["read_guard"](0, 2))
        self.assertTrue(POLICIES["destructive_guard"](2, 3))

    def test_summary_keys(self):
        s = summarize(score(self.rows(1), self.cat, self.ref, {"q1": {"sev": 0}}, "any_up"))
        self.assertEqual(s["seer"], 1.0)


class Stats(unittest.TestCase):
    def test_wilson(self):
        lo, hi = wilson(4, 1386)
        self.assertAlmostEqual(lo, 0.00112, places=4)
        self.assertAlmostEqual(hi, 0.00739, places=4)
        self.assertEqual(wilson(0, 10)[0], 0.0)

    def test_mcnemar(self):
        gained, lost, p = mcnemar([0, 0, 1, 1], [1, 1, 1, 0])
        self.assertEqual((gained, lost), (2, 1))
        self.assertAlmostEqual(p, 1.0)


class CatalogSubset(unittest.TestCase):
    def test_gold_server_always_installed(self):
        cat = [{"server": f"s{i // 3}"} for i in range(30)]
        C = Catalogs(cat, list(range(30)))
        sub = C.subset("q1", 4, 9)
        self.assertTrue({3, 4, 5} <= set(sub))
        self.assertEqual(len(sub), 9)
        self.assertEqual(len(C.subset("q1", 4, 0)), 30)


if __name__ == "__main__":
    unittest.main()
