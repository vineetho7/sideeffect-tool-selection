"""Figures and LaTeX tables for the paper from results/*.json."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import ROOT, RES, FIGS, jload

plt.rcParams.update({"font.size": 8, "font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200})
EMB_NAME = {"bm25": "BM25", "minilm": "MiniLM-L6", "bgebase": "BGE-base", "qwen3emb": "Qwen3-Emb-0.6B"}
COL = {"bm25": "#8c8c8c", "minilm": "#4c78a8", "bgebase": "#f58518", "qwen3emb": "#54a24b"}
PAPER = ROOT / "paper"


def fig_geometry():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.1))
    nn = jload(RES / "rq1_nearest_neighbour.json")
    embs = ["minilm", "bgebase", "qwen3emb"]
    xs = np.arange(len(embs))
    axes[0].bar(xs, [100 * nn[e]["nn_is_sibling"] for e in embs], color=[COL[e] for e in embs], width=0.6)
    axes[0].axhline(100 * nn["qwen3emb"]["chance"], color="k", ls="--", lw=0.8)
    axes[0].text(2.35, 100 * nn["qwen3emb"]["chance"] + 2, "chance", fontsize=7, ha="right")
    axes[0].set_xticks(xs, [EMB_NAME[e] for e in embs])
    axes[0].set_ylabel("nearest same-server tool\nis a sibling (%)")
    axes[0].set_ylim(0, 100)
    for emb in ("minilm", "bgebase", "qwen3emb"):
        m = np.load(RES / f"geometry_{emb}.npz")["margin"]
        xs = np.sort(m)
        axes[1].plot(xs, np.arange(1, len(xs) + 1) / len(xs), label=EMB_NAME[emb], color=COL[emb])
    axes[1].axvline(0, color="k", lw=0.6, ls=":")
    axes[1].set_xlabel("sim(request, target) $-$ max sim(request, sibling)")
    axes[1].set_ylabel("cumulative share of requests")
    axes[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGS / "geometry.pdf"); fig.savefig(FIGS / "geometry.png")


def fig_retrieval():
    r = jload(RES / "retrieval.json")["retrieval"]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.0))
    for name in ("bm25", "minilm", "bgebase", "qwen3emb"):
        rows = sorted([x for x in r if x["retriever"] == name], key=lambda x: x["N"])
        N = [x["N"] for x in rows]
        axes[0].plot(N, [100 * x["acc1"] for x in rows], marker="o", ms=3, label=EMB_NAME[name], color=COL[name])
        axes[1].plot(N, [100 * x["seer1"] for x in rows], marker="o", ms=3, color=COL[name], ls=":")
        axes[2].plot(N, [100 * x["exposure_k_read"] for x in rows], marker="o", ms=3, color=COL[name])
    g = [x for x in jload(RES / "guard_retrieval_qwen3.5-latest.json") if x["retriever"] == "qwen3emb" and x["guard"] == "none"]
    g = sorted(g, key=lambda x: x["N"] or 10 ** 9)
    Nmax = max(x["N"] for x in r)
    axes[1].plot([x["N"] or Nmax for x in g], [100 * x["seer_conf"] for x in g], marker="s", ms=3, color="k",
                 label="Qwen3-Emb, human-verified")
    axes[1].legend(frameon=False, fontsize=6)
    for ax, t in zip(axes, ("top-1 accuracy (%)", "SEER@1 (%), dotted = automatic", "read requests exposed@5 (%)")):
        ax.set_xscale("log"); ax.set_xlabel("catalog size (tools)"); ax.set_ylabel(t)
    axes[0].legend(frameon=False, fontsize=6.5)
    fig.tight_layout()
    fig.savefig(FIGS / "retrieval.pdf"); fig.savefig(FIGS / "retrieval.png")


def fig_tradeoff(summary):
    fig, ax = plt.subplots(figsize=(3.4, 3.1))
    pm = {"none": "o", "any_up": "^", "tau2": "v", "read_guard": "s", "destructive_guard": "D", "read_or_destructive": "P"}
    pl = {"none": "no guard", "any_up": "any increase", "tau2": "increase $\\geq$2", "read_guard": "read-guard",
          "destructive_guard": "destructive-guard", "read_or_destructive": "read- or destructive-guard"}
    series = []
    gr = jload(RES / "guard_retrieval_qwen3.5-latest.json")
    series.append(("retriever top-1", "#8c8c8c", {x["guard"]: (x["auto_correct"], x["seer_conf_exec"]) for x in gr
                                                   if x["retriever"] == "qwen3emb" and x["N"] == 0}))
    runs = [("plain_n0_qwen3emb_qwen3.5-latest_k5", "Qwen3.5 plain", "#4c78a8"),
            ("sibling_n0_qwen3emb_qwen3.5-latest_k5", "Qwen3.5 sibling", "#54a24b"),
            ("plain_n0_qwen3emb_qwen3-1.7b_k5", "Qwen3-1.7B plain", "#e45756"),
            ("sibling_n0_qwen3emb_qwen3-1.7b_k5", "Qwen3-1.7B sibling", "#f58518")]
    for run, lab, c in runs:
        d = {x["guard"]: (x["auto_correct"], x["seer_conf_exec"]) for x in summary if x["run"] == run}
        if d:
            nog = [x for x in summary if x["run"] == run][0]
            d["none"] = (nog["acc"], nog["seer_conf"])
            series.append((lab, c, d))
    for lab, c, d in series:
        pts = sorted(d.items(), key=lambda kv: -kv[1][0])
        ax.plot([100 * v[0] for _, v in pts], [100 * v[1] for _, v in pts], color=c, lw=0.6, alpha=0.5)
        for pol, v in pts:
            ax.scatter(100 * v[0], 100 * v[1], marker=pm[pol], color=c, s=16)
        ax.plot([], [], color=c, label=lab)
    for pol, m in pm.items():
        ax.scatter([], [], marker=m, color="k", s=12, label=pl[pol])
    ax.set_xlabel("correct and not held (%)")
    ax.set_ylabel("verified escalations let through (%)")
    ax.legend(frameon=False, fontsize=5.5, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    fig.savefig(FIGS / "tradeoff.pdf", bbox_inches="tight"); fig.savefig(FIGS / "tradeoff.png", bbox_inches="tight")


def tab_profiles():
    a = jload(RES / "profile_audit_score.json")
    c = jload(RES / "profile_compare.json")
    names = [("rules", "name rules"), ("system", "annot.\\,+\\,rules (system)"), ("qwen_llm", "Qwen3.5 LLM"),
             ("reference", "Gemma3\\,+\\,annot. (reference)")]
    rows = [(n, 100 * c[k]["exact"], c[k]["kappa"], 100 * c[k]["read_write"], 100 * c[k]["under"]) for k, n in names]
    body = "\n".join(f"{n} & {e:.1f} & {k:.2f} & {rw:.1f} & {u:.1f}\\\\" for n, e, k, rw, u in rows)
    tex = ("\\begin{table}[t]\\centering\\caption{Operation profilers against "
           f"{a['labeled']} tools labeled by an AI assistant, not human ground truth (\\%). Under = severity underestimated, the unsafe direction.}}"
           "\\label{tab:profiles}\n\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lrrrr}\\toprule\n"
           "profiler & exact & $\\kappa$ & read/write & under\\\\\\midrule\n" + body +
           "\n\\bottomrule\\end{tabular}\\end{table}\n")
    open(PAPER / "tab_profiles.tex", "w").write(tex)


VSHORT = {"expandtags": "exp.+tags", "expand": "expand", "matched": "matched"}


def tab_main(summary, N="n0"):
    order = ["plain", "matched", "native", "tags", "expand", "expandtags", "sibling"]
    models = [("qwen3.5-latest", "Qwen3.5-9B"), ("gemma3-12b", "Gemma3-12B"), ("phi4-14b", "Phi-4"), ("qwen3-1.7b", "Qwen3-1.7B")]
    xs_ = jload(RES / "cross_server.json") if N == "n0" else {}
    rows = []
    for mkey, mname in models:
        for k in (5, 10, 15):
            for v in order:
                run = f"{v}_{N}_qwen3emb_{mkey}_k{k}"
                xs = [x for x in summary if x["run"] == run and x["guard"] == "any_up"]
                if not xs:
                    continue
                x = xs[0]
                agn = f" & {100*xs_[run]['acc_server_agnostic']:.1f}" if N == "n0" else ""
                name = VSHORT.get(v, v) if k == 5 else f"top-{k}"
                rows.append(f"{mname} & {name} & {100*x['acc']:.1f}{agn} & "
                            f"{100*x['seer']:.2f} & {100*x['seer_conf']:.2f} & {100*x['seer_conf_exec']:.2f} & "
                            f"{100*x['held']:.1f} & {x['p_tok']:.0f} \\\\")
        rows.append("\\midrule")
    body = "\n".join(rows[:-1])
    big = N == "n0"
    size = "\\NumPoolTools{}" if big else "1,000"
    tex = ("\\begin{table}[t]\\centering\\caption{End-to-end selection at " + size + " tools over the Qwen3-Emb "
           "shortlist (top five unless stated; \\NumQueries{} requests). " + ("Acc.\\ any: correct, or an equivalent tool "
           "(same operation, resource and severity) on another server; diagnostic only. " if big else "") + "Esc.\\ auto: escalation by the automatic "
           "reference; verified: human-confirmed escalations; guard: verified escalations the "
           "any-increase guard would let through (it holds the share in \\emph{held}). Tok.: mean selector-prompt tokens (intent call excluded). exp.+tags: expand+tags; matched: count-matched plain shortlist.}"
           f"\\label{{tab:main{'' if big else '1k'}}}\n"
           "\\setlength{\\tabcolsep}{1.6pt}\\footnotesize\n"
           f"\\begin{{tabular}}{{ll{'rr' if big else 'r'}rrrrr}}\\toprule\n"
           " & & \\multicolumn{" + ("2" if big else "1") + "}{c}{accuracy} & \\multicolumn{3}{c}{escalation (\\%)} & & \\\\\n"
           "selector & variant & exact" + (" & any" if big else "") + " & auto & verified & guard & held & tok.\\\\\\midrule\n"
           f"{body}\n\\bottomrule\\end{{tabular}}\\end{{table}}\n")
    open(PAPER / f"tab_main{'' if big else '_1k'}.tex", "w").write(tex)


def tab_split():
    rows = jload(RES / "escalation_split.json")
    name = {"qwen3.5-latest": "Qwen3.5", "gemma3-12b": "Gemma3", "qwen3-1.7b": "Qwen3-1.7B"}
    body = "\n".join(
        f"{name[r['model']]}{', terse' if r['terse'] else ''} & {100*r['in_shortlist']:.1f} & "
        f"{100*r['acc_given_shortlisted']:.1f} & {100*r['acc_end_to_end']:.1f} & "
        + ("-- & -- & " if r["terse"] else f"{r['esc_target_present']} & {r['esc_target_missing']} & ")   # terse flags unlabeled
        + f"{100*r['none_when_missing']:.0f} \\\\" for r in rows)
    tex = ("\\begin{table}[t]\\centering\\caption{Retrieval versus selection at 30,000 tools (plain prompt). "
           "In list: target in the top five. Acc.\\,|\\,in: selector accuracy when it is. Escalations are verified "
           "counts with the target in or out of the list (terse: not human-labeled); NONE: share of missing-target requests the selector "
           "declined.}\\label{tab:split}\n\\footnotesize\\setlength{\\tabcolsep}{2.5pt}"
           "\\begin{tabular}{lrrrrrr}\\toprule\n"
           "selector & in list & acc.\\,|\\,in & acc. & esc.\\,in & esc.\\,out & NONE\\\\\\midrule\n"
           + body + "\n\\bottomrule\\end{tabular}\\end{table}\n")
    open(PAPER / "tab_split.tex", "w").write(tex)


if __name__ == "__main__":
    import sys
    summary = jload(RES / "summary.json") if (RES / "summary.json").exists() else []
    for f in (fig_geometry, fig_retrieval):
        try:
            f(); print("ok", f.__name__)
        except Exception as e:
            print("skip", f.__name__, e)
    tab_profiles()
    tab_split()
    if summary:
        fig_tradeoff(summary); tab_main(summary); tab_main(summary, "n1000"); print("ok tradeoff/table")
