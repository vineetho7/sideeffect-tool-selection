"""Write paper/numbers.tex: every number quoted in the paper, computed from results files."""
import json
from collections import Counter
from common import ROOT, PROC, RAW, RES, jload

M = {}


def put(name, v, fmt="{:,}"):
    M[name] = fmt.format(v) if not isinstance(v, str) else v


def pct(x):
    return f"{100 * x:.1f}"


if __name__ == "__main__":
    reg = jload(RAW / "registry.json")
    from probe_remotes import candidates
    rem = jload(RAW / "remote_tools.json")
    ok = [r for r in rem if r["ok"]]
    put("NumRegistry", len(reg))
    put("NumCandidates", len(candidates(reg)))
    put("NumRespondingServers", len(ok))
    put("NumRawTools", sum(len(r["tools"]) for r in ok))
    errs = Counter(r["error"][:40] for r in rem if not r["ok"])
    put("NumFailAuth", sum(v for k, v in errs.items() if "401" in k))
    put("NumFailRate", sum(v for k, v in errs.items() if "429" in k))
    cs = jload(PROC / "catalog_stats.json")
    put("NumCatTools", cs["tools"]); put("NumCatServers", cs["servers_unique"]); put("NumPublishers", cs["publishers"])
    put("NumSibGroups", cs["sibling_groups"]); put("NumEscGroups", cs["escalation_capable_groups"])
    put("NumSibTools", cs["tools_in_sibling_groups"]); put("NumSibServers", cs["servers_with_sibling_groups"])
    ss = jload(RES / "sibling_stats.json")
    put("NumReadDestructiveGroups", ss["read_and_destructive_rule"])
    put("NumGroupsNoAnnotation", ss["no_annotation_at_all"])
    put("PctGroupsNoAnnotation", pct(ss["no_annotation_at_all"] / ss["groups"]), "{}")
    put("NumServersGeTen", ss["servers_ge10_tools"]); put("NumServersGeTenEsc", ss["servers_ge10_with_esc_group"])
    put("PctServersGeTenEsc", pct(ss["servers_ge10_with_esc_group"] / ss["servers_ge10_tools"]), "{}")
    es = jload(RES / "ecosystem_stats.json")
    put("PctAnnotatedAny", pct(es["all"]["any_annotation"]), "{}")
    put("PctReadOnlyHint", pct(es["all"]["readOnlyHint_present"]), "{}")
    put("NumDeleteNamed", es["all"]["delete_named_tools"])
    put("NumDeleteNamedNoHint", es["all"]["delete_named_with_no_hint"])
    put("NumROTrueOnWrite", es["all"]["readOnly_true_on_update_or_delete_named"])
    au = jload(RES / "profile_audit_score.json")
    put("NumAuditTools", au["labeled"])
    put("RuleExact", pct(au["rule_exact_acc"]), "{}"); put("RuleKappa", f"{au['rule_kappa']:.2f}")
    put("AnnRWAcc", pct(au["annotation_read_vs_write_acc"]), "{}"); put("AnnPresent", pct(au["annotation_present"]), "{}")
    put("TrueDestructive", au["true_destructive"]); put("TrueDestructiveFlagged", au["true_destructive_flagged_by_annotation"])
    put("TrueDestructiveNoAnn", au["true_destructive_without_any_annotation"])
    try:
        ra = jload(RES / "ref_profile_audit.json")
        put("RefExact", pct(ra["ref_exact"]), "{}"); put("RefKappa", f"{ra['ref_kappa']:.2f}")
    except FileNotFoundError:
        put("RefExact", "??"); put("RefKappa", "??")
    try:
        qs = jload(PROC / "queries.json")
        gst = jload(PROC / "query_gen_stats.json")
        put("NumQueries", len(qs)); put("NumQueriesRead", sum(q["gold_sev"] == 0 for q in qs))
        put("NumQueriesWrite", sum(q["gold_sev"] != 0 for q in qs))
        put("NumQueryServers", len({q["group"].split("::")[0] for q in qs}))
        put("NumQueryGroups", len({q["group"] for q in qs}))
        put("NumGenerated", gst.get("generated", 0)); put("NumValidated", gst.get("validated", 0))
        put("NumValDisagree", gst.get("validator_disagreed", 0)); put("NumLeak", gst.get("leak_or_parse_fail", 0))
        put("NumPoolTools", len(jload(PROC / "pool.json")))
    except FileNotFoundError:
        for k in ("NumQueries", "NumQueriesRead", "NumQueriesWrite", "NumQueryServers", "NumPoolTools"):
            put(k, "??")
    # ---- RQ1 ----
    nn = jload(RES / "rq1_nearest_neighbour.json")
    put("NNSibQwen", pct(nn["qwen3emb"]["nn_is_sibling"]), "{}"); put("NNSibMini", pct(nn["minilm"]["nn_is_sibling"]), "{}")
    put("NNSibBge", pct(nn["bgebase"]["nn_is_sibling"]), "{}"); put("NNChance", pct(nn["qwen3emb"]["chance"]), "{}")
    put("NNTools", nn["qwen3emb"]["n"])
    ret = jload(RES / "retrieval.json")
    g = ret["geometry"]
    put("SibOutQwen", pct(g["qwen3emb"]["frac_queries_sibling_outscores_gold"]), "{}")
    put("SibOutBge", pct(g["bgebase"]["frac_queries_sibling_outscores_gold"]), "{}")
    put("SibOutMini", pct(g["minilm"]["frac_queries_sibling_outscores_gold"]), "{}")
    R = {(x["retriever"], x["N"]): x for x in ret["retrieval"]}
    pool = max(n for _, n in R)
    nm = {"bm25": "BM", "minilm": "Mini", "bgebase": "Bge", "qwen3emb": "Qwen"}
    for r, k in nm.items():
        for n, nk in ((200, "Small"), (1000, "K"), (pool, "Pool")):
            x = R[(r, n)]
            put(f"Ret{k}{nk}Acc", pct(x["acc1"]), "{}"); put(f"Ret{k}{nk}Seer", pct(x["seer1"]), "{}")
            put(f"Ret{k}{nk}Expo", pct(x["exposure_k_read"]), "{}"); put(f"Ret{k}{nk}Rec", pct(x["recall_k"]), "{}")
            put(f"Ret{k}{nk}Sib", pct(x["sibling_share_of_errors"]), "{}")
    # ---- HNSW ----
    h = [x for x in jload(RES / "hnsw_control.json") if x["embedder"] == "qwen3emb"]
    put("FlatMs", f"{h[0]['flat_ms_median']:.2f}"); put("HnswMsHundred", f"{[x for x in h if x['ef']==100][0]['hnsw_ms_median']:.2f}")
    put("HnswTenDrop", f"{100*(h[0]['top1_acc_exact']-h[0]['top1_acc_hnsw']):.1f}")
    # ---- selection ----
    S = {(x["run"], x["guard"]): x for x in jload(RES / "summary.json")
         if "_k5" in x["run"]}                       # macro keys drop k; budget baselines are cited from budget_pairs
    mk = {"qwen3.5-latest": "Q", "gemma3-12b": "G", "qwen3-1.7b": "S", "phi4-14b": "P"}
    for (run, pol), x in S.items():
        if pol != "read_or_destructive" or run.endswith("_terse"):
            continue
        v, n, _, model = run.split("_")[:4]
        key = f"Sel{mk.get(model,'X')}{v.capitalize()}{'K' if n=='n1000' else 'Pool'}"
        put(key + "Acc", pct(x["acc"]), "{}"); put(key + "Seer", f"{100*x['seer']:.2f}")
        put(key + "Exec", f"{100*x['seer_exec']:.2f}"); put(key + "Held", pct(x["held"]), "{}")
        put(key + "Needless", pct(x["held_correct"]), "{}"); put(key + "Tok", f"{x['p_tok']:.0f}")
        put(key + "InCand", pct(x["in_cand"]), "{}"); put(key + "SibErr", pct(x["sibling_share_of_errors"]), "{}")
        put(key + "N", f"{round(x['seer']*x['n'])}")
        put(key + "Conf", f"{100*x['seer_conf']:.2f}"); put(key + "ConfN", f"{round(x['seer_conf']*x['n'])}")
        put(key + "ConfExec", f"{100*x['seer_conf_exec']:.2f}")
    for (run, pol), x in S.items():
        if pol == "any_up" and "seer_conf_wilson" in x and x["esc_unlabeled"] == 0:
            v, n, _, model = run.split("_")[:4]
            key = f"{'Terse' if run.endswith('_terse') else 'Sel'}{mk.get(model,'X')}{v.capitalize()}{'' if run.endswith('_terse') else ('K' if n=='n1000' else 'Pool')}"
            lo, hi = x["seer_conf_wilson"]
            put(key + "CI", f"{100*lo:.2f}--{100*hi:.2f}")
    for (run, pol), x in S.items():
        if pol == "any_up" and not run.endswith("_terse"):
            v, n, _, model = run.split("_")[:4]
            key = f"Sel{mk.get(model,'X')}{v.capitalize()}{'K' if n=='n1000' else 'Pool'}"
            put(key + "ConfExecAny", f"{100*x['seer_conf_exec']:.2f}"); put(key + "HeldAny", pct(x["held"]), "{}")
    for (run, pol), x in S.items():
        if run.endswith("_terse") and pol == "read_or_destructive":
            v, n, _, model = run.split("_")[:4]
            key = f"Terse{mk.get(model,'X')}{v.capitalize()}"
            put(key + "Acc", pct(x["acc"]), "{}"); put(key + "Seer", f"{100*x['seer']:.2f}"); put(key + "Exec", f"{100*x['seer_exec']:.2f}")
            if x["esc_unlabeled"] == 0:        # terse flags carry no human labels yet
                put(key + "Conf", f"{100*x['seer_conf']:.2f}")
            put(key + "Unlab", f"{100*x['esc_unlabeled']:.2f}")
    # ---- guard on retriever-only routing ----
    gp = RES / "guard_retrieval_qwen3.5-latest.json"
    if gp.exists():
        pk = {"none": "None", "any_up": "Any", "tau2": "Tau", "read_guard": "Read", "destructive_guard": "Dest", "read_or_destructive": "RoD"}
        for x in jload(gp):
            if x["retriever"] == "qwen3emb" and x["N"] in (1000, 0):
                key = f"GR{pk[x['guard']]}{'K' if x['N']==1000 else 'Pool'}"
                put(key + "Exec", f"{100*x['seer_exec']:.2f}"); put(key + "Held", pct(x["held"]), "{}")
                put(key + "Needless", pct(x["needless"]), "{}"); put(key + "Auto", pct(x["auto_correct"]), "{}")
                if "seer_conf" in x:
                    put(key + "Conf", f"{100*x['seer_conf']:.2f}"); put(key + "ConfExec", f"{100*x['seer_conf_exec']:.2f}")
                if "seer_conf_wilson" in x:
                    put(key + "CI", f"{100*x['seer_conf_wilson'][0]:.2f}--{100*x['seer_conf_wilson'][1]:.2f}")
                    put(key + "ExecCI", f"{100*x['seer_conf_exec_wilson'][0]:.2f}--{100*x['seer_conf_exec_wilson'][1]:.2f}")
    tp = RES / "guard_retrieval_qwen3.5-latest_terse.json"
    if tp.exists():
        for x in jload(tp):
            if x["retriever"] == "qwen3emb" and x["N"] == 0 and x["guard"] in ("none", "any_up", "read_or_destructive"):
                key = {"none": "GRTNone", "any_up": "GRTAny", "read_or_destructive": "GRTRoD"}[x["guard"]]
                put(key + "Held", pct(x["held"]), "{}"); put(key + "Auto", pct(x["auto_correct"]), "{}")
                put(key + "Seer", f"{100*x['seer']:.2f}")
                if x["esc_unlabeled"] == 0:        # terse flags carry no human labels yet
                    put(key + "Conf", f"{100*x['seer_conf']:.2f}"); put(key + "ConfExec", f"{100*x['seer_conf_exec']:.2f}")
                    put(key + "CI", f"{100*x['seer_conf_wilson'][0]:.2f}--{100*x['seer_conf_wilson'][1]:.2f}")
        ts = jload(PROC / "terse_stats.json"); tq = jload(PROC / "queries_terse.json")
        put("TerseN", len(tq)); put("TerseWords", f"{sum(len(q['query'].split()) for q in tq)/len(tq):.1f}")
        put("TerseInvalid", ts["invalid"])
        rt = {(x["retriever"], x["N"]): x for x in jload(RES / "retrieval_terse.json")["retrieval"]}
        put("RetTQwenPoolAcc", pct(rt[("qwen3emb", pool)]["acc1"]), "{}"); put("RetTQwenPoolRec", pct(rt[("qwen3emb", pool)]["recall_k"]), "{}")
    ep = jload(RES / "escalation_precision.json")
    put("EscLabeled", ep["labeled"]); put("EscTrue", ep["true"]); put("EscPrec", pct(ep["precision"]), "{}")
    put("EscOverstate", f"{1/ep['precision']:.1f}")
    put("EscTrueFromRead", sum(v for k, v in ep["true_pairs"].items() if k.startswith("0->")))
    put("EscTrueReadCreate", ep["true_pairs"].get("0->1", 0))
    put("EscTrueToDelete", sum(v for k, v in ep["true_pairs"].items() if k.endswith("->3")))
    put("EscFalseUpdDest", ep["false_pairs"].get("2->3", 0))
    put("EscAmbig", ep["unlabeled"])
    ai = {}
    import csv as _csv
    for e in _csv.DictReader(open(ROOT / "data" / "labels" / "escalations_labeled.csv")):
        ai[(e["query"], e["pred"])] = e["true_escalation"]
    hl = list(_csv.DictReader(open(ROOT / "data" / "labels" / "human_escalations.csv")))
    put("EscAITrue", sum(ai.get((e["query"], e["pred"])) == "1" for e in hl)); put("EscFlagged", ep["flagged"]); put("EscUndecided", ep["flagged"] - ep["labeled"])
    ia = jload(RES / "independent_agreement.json")
    put("IndN", ia["all"]["n"]); put("IndAgree", pct(ia["all"]["agree"]), "{}"); put("IndKappa", f"{ia['all']['kappa']:.2f}")
    put("IndPos", f"{ia['all']['pos_agree']:.2f}"); put("IndFlagKappa", f"{ia['flagged']['kappa']:.2f}")
    put("IndFlagPos", f"{ia['flagged']['pos_agree']:.2f}")
    un = [ia[k] for k in ("unflagged_selector", "unflagged_retriever")]
    put("IndUnN", sum(x["n"] for x in un)); put("IndUnAuthorYes", sum(x["author_yes"] for x in un))
    put("IndUnIndYes", sum(x["independent_yes"] for x in un)); put("IndDis", len(ia["disagreements"]))
    from collections import Counter as _C
    cl = jload(ROOT / "data" / "labels" / "second_rater" / "consensus_labels.json")
    cs = jload(ROOT / "data" / "labels" / "second_rater" / "export_consensus" / "consensus" / "independent.json")
    cs = _C(cs.get("data", cs)["final"].values())
    put("ConsYes", cs["yes"]); put("ConsNo", cs["no"]); put("ConsAmbig", cs["ambiguous"])
    fl = [v["label"] for v in cl.values() if v["stratum"] == "flagged"]
    put("ConsFlagYes", fl.count("yes")); put("ConsFlagN", len(fl))
    es = jload(RES / "effect_summary.json")
    put("ReadReqs", f"{es['read_requests']:,}")
    for run, nm in (("retriever_top1_qwen3emb_30k", "Ret"), ("plain_n0_qwen3emb_qwen3.5-latest_k5", "QPlain"),
                    ("sibling_n0_qwen3emb_qwen3.5-latest_k5", "QSibling"), ("plain_n0_qwen3emb_gemma3-12b_k5", "GPlain"),
                    ("plain_n0_qwen3emb_phi4-14b_k5", "PPlain"), ("plain_n0_qwen3emb_qwen3-1.7b_k5", "SPlain")):
        x = es["runs"][run]
        put(f"RW{nm}", x["read_to_write"]); put(f"RW{nm}Rate", f"{100*x['r2w_of_reads']:.2f}")
        put(f"RW{nm}CI", f"{100*x['r2w_of_reads_ci'][0]:.2f}--{100*x['r2w_of_reads_ci'][1]:.2f}")
        put(f"RW{nm}All", f"{100*x['r2w_of_all']:.2f}")
    put("EffPairs", es["pairs"]); put("EffFromRead", es["pairs_from_read"]); put("EffTagged", es["pairs_human_tagged"])
    for k, v in es["pairs_by_effect"].items():
        put(f"Eff{k.capitalize()}", v)
    eb = jload(RES / "error_breakdown.json")["plain_n0_qwen3emb_qwen3.5-latest_k5"]
    put("ErrMiss", pct(eb.get("target_not_shortlisted", 0)), "{}"); put("ErrOther", pct(eb.get("same_operation_other_server", 0)), "{}")
    put("ErrSib", pct(eb.get("sibling", 0)), "{}"); put("ErrNone", pct(eb.get("none_or_unparsed", 0)), "{}")
    cn = [round(x["seer_conf"] * x["n"]) for (run, pol), x in S.items() if pol == "any_up" and not run.endswith("_terse")]
    put("ConfNMin", min(cn)); put("ConfNMax", max(cn))
    ra = jload(RES / "rater_agreement.json")["raters"]
    r1 = list(ra.values())[0]
    put("RaterToolAgree", pct(r1["tools_vs_first"]["agreement"]), "{}"); put("RaterToolKappa", f"{r1['tools_vs_first']['kappa']:.2f}")
    put("RaterPickAgree", pct(r1["picks_vs_first"]["agreement"]), "{}"); put("RaterPickKappa", f"{r1['picks_vs_first']['kappa']:.2f}")
    r2 = jload(RES / "rater_round2.json")
    put("RaterTwoAgree", pct(r2["agreement"]), "{}"); put("RaterTwoKappa", f"{r2['kappa']:.2f}")
    put("RaterTwoFirstYes", r2["first_yes"]); put("RaterTwoSecondYes", r2["second_yes"])
    ad = jload(RES / "adjudication_summary.json")
    put("AdjFlagFirstYes", ad["flagged_first_yes"]); put("AdjFlagYes", ad["flagged_adj_yes"])
    put("RaterToolN", r1["tools_vs_first"]["n"]); put("RaterPickN", r1["picks_vs_first"]["n"])
    put("RaterTwoN", r2["n"]); put("RaterTwoAnswered", r2["second_answered"]); put("RaterTwoFirstN", r2["first_n"])
    put("AdjUnflagN", ad["unflagged_n"])
    tp_ = jload(RES / "escalation_precision.json").get("terse", {})
    if tp_.get("labeled"):
        put("TerseEscTrue", tp_["true"]); put("TerseEscLabeled", tp_["labeled"])
    mr = jload(RES / "missed_rates.json")
    put("MissSelAI", pct(mr["selector_ai_adjudicated"]["rate"]), "{}"); put("MissRetAI", pct(mr["retriever_ai_adjudicated"]["rate"]), "{}")
    for k, nm in (("selector", "Sel"), ("retriever", "Ret")):
        put(f"Miss{nm}Yes", mr[k]["yes"]); put(f"Miss{nm}N", mr[k]["n"]); put(f"Miss{nm}Rate", pct(mr[k]["rate"]), "{}")
        put(f"Miss{nm}CI", f"{100*mr[k]['ci'][0]:.1f}--{100*mr[k]['ci'][1]:.1f}")
    em = jload(RES / "estimated_missed.json")
    for run, nm in (("plain_n0_qwen3emb_qwen3.5-latest_k5", "QPlain"), ("plain_n0_qwen3emb_gemma3-12b_k5", "GPlain"),
                    ("plain_n0_qwen3emb_phi4-14b_k5", "PPlain"), ("plain_n0_qwen3emb_qwen3-1.7b_k5", "SPlain"),
                    ("retriever_top1_qwen3emb_30k", "Ret")):
        x = em[run]
        put(f"Est{nm}", f"{100*x['est_total']:.1f}"); put(f"Est{nm}Range", f"{100*x['boot_range'][0]:.1f}--{100*x['boot_range'][1]:.1f}")
        put(f"Est{nm}AI", f"{100*x['sensitivity']['ai_adjudicated']:.1f}")
    for k, nm in (("selector", "Sel"), ("retriever", "Ret")):
        put(f"Miss{nm}Author", pct(mr[f"{k}_author"]["rate"]), "{}")
    for run, nm in (("plain_n0_qwen3emb_qwen3.5-latest_k5", "QPlain"), ("retriever_top1_qwen3emb_30k", "Ret")):
        put(f"Est{nm}Author", f"{100*em[run]['sensitivity']['author']:.1f}")
    put("IndFlagAgree", pct(ia["flagged"]["agree"]), "{}")
    put("IndFlagAuthorYes", ia["flagged"]["author_yes"]); put("IndFlagIndYes", ia["flagged"]["independent_yes"])
    from adjudication import review as _review
    from analyze import wilson
    eq = _review(PROC.parent / "labels" / "second_rater" / "export_equiv" / "ratings" / "rater_account.json")
    ey, en = sum(v == "yes" for v in eq.values()), sum(v in ("yes", "no") for v in eq.values())
    put("EquivYes", ey); put("EquivN", en); put("EquivRate", pct(ey / en), "{}")
    lo, hi = wilson(ey, en); put("EquivCI", f"{100*lo:.0f}--{100*hi:.0f}")
    qa = jload(RES / "query_audit_score.json")
    put("QAFits", pct(qa["gold_fits"]), "{}"); put("QAUnamb", pct(qa["unambiguous"]), "{}"); put("QAN", qa["audited"])
    import re as _re
    lines = [f"\\newcommand{{\\{_re.sub('[^A-Za-z]', '', k)}}}{{{v}\\xspace}}" for k, v in sorted(M.items())]
    open(ROOT / "paper" / "numbers.tex", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
