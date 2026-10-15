"""Annotation coverage and consistency with name-derived operation class (RQ3 motivation)."""
import json
from collections import Counter
from common import PROC, RES, jload, jdump

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    groups = jload(PROC / "sibling_groups.json")
    in_grp = [t for t in cat if t.get("group")]
    out = {}
    for name, ts in (("all", cat), ("sibling_group_tools", in_grp)):
        ann = [t for t in ts if t["annotations"]]
        has_ro = [t for t in ts if "readOnlyHint" in t["annotations"]]
        known = [t for t in has_ro if t["sev"] is not None]
        # contradictions between the server's own hint and the name-derived class
        ro_true_but_write = [t for t in known if t["annotations"]["readOnlyHint"] is True and t["sev"] >= 2]
        ro_false_but_read = [t for t in known if t["annotations"]["readOnlyHint"] is False and t["sev"] == 0]
        dest_true_on_read = [t for t in known if t["annotations"].get("destructiveHint") is True and t["sev"] == 0]
        delete_named = [t for t in ts if t["sev"] == 3]
        delete_flagged = [t for t in delete_named if t["annotations"].get("destructiveHint") is True]
        out[name] = {
            "tools": len(ts), "any_annotation": len(ann) / len(ts),
            "readOnlyHint_present": len(has_ro) / len(ts),
            "destructiveHint_present": sum("destructiveHint" in t["annotations"] for t in ts) / len(ts),
            "readOnly_true_on_update_or_delete_named": len(ro_true_but_write),
            "readOnly_false_on_read_named": len(ro_false_but_read),
            "destructive_true_on_read_named": len(dest_true_on_read),
            "delete_named_tools": len(delete_named),
            "delete_named_with_destructiveHint_true": len(delete_flagged),
            "delete_named_with_no_hint": sum(1 for t in delete_named if "destructiveHint" not in t["annotations"]),
            "examples_readonly_true_on_write": [t["id"] for t in ro_true_but_write[:15]],
        }
    # groups whose escalation risk is fully covered by trustworthy hints
    cov = 0
    esc = 0
    for g, idx in groups.items():
        ts = [cat[i] for i in idx]
        if any(t["sev"] == 0 for t in ts) and any(t["sev"] >= 2 for t in ts):
            esc += 1
            if all("readOnlyHint" in t["annotations"] for t in ts):
                cov += 1
    out["escalation_groups"] = esc
    out["escalation_groups_fully_annotated"] = cov
    out["op_source"] = Counter(t["src"] for t in cat)
    jdump(json.loads(json.dumps(out, default=str)), RES / "ecosystem_stats.json")
    print(json.dumps(out, indent=1, default=str))
