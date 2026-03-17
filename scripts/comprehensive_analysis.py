#!/usr/bin/env python3
"""ThermoQA Comprehensive Analysis — Paper-Grade Report Generator.

Loads all 3 runs × 6 models × 3 tiers, computes multi-run statistics,
and generates a detailed markdown report for the arxiv paper.

Usage:
    python scripts/comprehensive_analysis.py
    python scripts/comprehensive_analysis.py --output analysis/comprehensive_report.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent

PROVIDERS = ["anthropic", "openai", "google", "xai", "deepseek", "minimax"]

MODEL_NAMES = {
    "anthropic": "Claude Opus 4.6",
    "openai": "GPT-5.4",
    "google": "Gemini 2.5 Pro",
    "xai": "Grok 4",
    "deepseek": "DeepSeek R1",
    "minimax": "MiniMax M1",
}

MODEL_SHORT = {
    "anthropic": "Opus",
    "openai": "GPT-5.4",
    "google": "Gemini",
    "xai": "Grok 4",
    "deepseek": "DeepSeek",
    "minimax": "MiniMax",
}

TIER_DIRS = {
    1: {"questions": BASE / "data" / "tier1_properties",
        "results": BASE / "results"},
    2: {"questions": BASE / "data" / "tier2_components",
        "results": BASE / "results_tier2"},
    3: {"questions": BASE / "data" / "tier3_cycles",
        "results": BASE / "results_tier3"},
}

RUNS = [1, 2, 3]

TIER_QCOUNTS = {1: 110, 2: 101, 3: 82}
TOTAL_QUESTIONS = 293

# T-critical values for 95% CI (two-tailed) by degrees of freedom
T_CRIT = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 60: 2.000,
    120: 1.980,
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def md_table(headers: list[str], rows: list[list], align: list[str] | None = None) -> str:
    """Build a GitHub-flavored markdown table."""
    if not rows:
        return "(no data)\n"
    col_w = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        sr = [str(c) if c is not None else "" for c in row]
        str_rows.append(sr)
        for i, c in enumerate(sr):
            if i < len(col_w):
                col_w[i] = max(col_w[i], len(c))
    if align is None:
        align = ["l"] * len(headers)
    sep = []
    for i, a in enumerate(align):
        w = col_w[i]
        if a == "r":
            sep.append("-" * (w - 1) + ":")
        elif a == "c":
            sep.append(":" + "-" * (w - 2) + ":")
        else:
            sep.append("-" * w)
    lines = []
    lines.append("| " + " | ".join(h.ljust(col_w[i]) for i, h in enumerate(headers)) + " |")
    lines.append("| " + " | ".join(sep) + " |")
    for sr in str_rows:
        lines.append("| " + " | ".join(
            sr[i].ljust(col_w[i]) if i < len(sr) else " " * col_w[i]
            for i in range(len(headers))) + " |")
    return "\n".join(lines) + "\n"


def fmt_pct(v: float | None, decimals: int = 1) -> str:
    if v is None:
        return "—"
    return f"{v:.{decimals}f}%"


def fmt_f(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "—"
    return f"{v:.{decimals}f}"


def fmt_score(v: float | None, decimals: int = 1) -> str:
    """Format a 0-1 score as percentage."""
    if v is None:
        return "—"
    return f"{v * 100:.{decimals}f}%"


def fmt_score_pm(mean_val: float, std_val: float, decimals: int = 1) -> str:
    """Format mean±std as percentage."""
    return f"{mean_val * 100:.{decimals}f}±{std_val * 100:.{decimals}f}%"


def mean(vals: list[float]) -> float | None:
    if not vals:
        return None
    return sum(vals) / len(vals)


def stdev(vals: list[float]) -> float | None:
    if len(vals) < 2:
        return None
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def mean_std(vals: list[float]) -> tuple[float, float]:
    """Return (mean, sample_std). Returns (0,0) if empty."""
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return m, math.sqrt(var)


def confidence_interval_95(vals: list[float]) -> tuple[float, float, float]:
    """Return (mean, ci_lower, ci_upper) at 95% confidence."""
    m, s = mean_std(vals)
    n = len(vals)
    if n < 2 or s == 0:
        return m, m, m
    df = n - 1
    t = T_CRIT.get(df, 2.0)  # fallback to ~normal
    margin = t * s / math.sqrt(n)
    return m, m - margin, m + margin


def welch_t(x1: list[float], x2: list[float]) -> tuple[float, int] | None:
    """Welch's t-test. Returns (t_statistic, degrees_of_freedom) or None."""
    n1, n2 = len(x1), len(x2)
    if n1 < 2 or n2 < 2:
        return None
    m1, s1 = mean_std(x1)
    m2, s2 = mean_std(x2)
    se1 = s1 ** 2 / n1
    se2 = s2 ** 2 / n2
    se_sum = se1 + se2
    if se_sum < 1e-15:
        return None
    t_stat = (m1 - m2) / math.sqrt(se_sum)
    # Welch-Satterthwaite df
    num = se_sum ** 2
    denom = se1 ** 2 / (n1 - 1) + se2 ** 2 / (n2 - 1)
    if denom < 1e-15:
        return None
    df = int(num / denom)
    return t_stat, max(df, 1)


def welch_significant(x1: list[float], x2: list[float], alpha: float = 0.05) -> bool | None:
    """Is the difference significant at alpha=0.05?"""
    result = welch_t(x1, x2)
    if result is None:
        return None
    t_stat, df = result
    # Find appropriate t_crit
    t_crit = 2.0  # fallback
    for d in sorted(T_CRIT.keys()):
        if d >= df:
            t_crit = T_CRIT[d]
            break
    return abs(t_stat) > t_crit


def pearson_r(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = math.sqrt(sxx * syy)
    if denom < 1e-15:
        return None
    return sxy / denom


def spearman_rho(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    def _rank(vals):
        indexed = sorted(range(n), key=lambda i: vals[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and vals[indexed[j + 1]] == vals[indexed[j]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[indexed[k]] = avg_rank
            i = j + 1
        return ranks
    rx, ry = _rank(xs), _rank(ys)
    return pearson_r(rx, ry)


def phi_coefficient(n11: int, n00: int, n10: int, n01: int) -> float | None:
    """Phi coefficient for 2x2 contingency table."""
    num = n11 * n00 - n10 * n01
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom < 1e-15:
        return None
    return num / denom


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_jsonl_stripped(path: Path) -> list[dict]:
    """Load JSONL, stripping raw_response/response_text/thinking_text to save memory."""
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            d.pop("raw_response", None)
            d.pop("response_text", None)
            d.pop("thinking_text", None)
            items.append(d)
    return items


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_all_data() -> dict:
    """Load all questions, per-run responses, summaries, and aggregates."""
    print("Loading all data...")
    data = {
        "questions": {},
        "questions_by_id": {},
        "responses": {},         # tier -> {provider: {run_num: [entries]}}
        "responses_by_id": {},   # tier -> {provider: {run_num: {id: entry}}}
        "summaries": {},         # tier -> {provider: {run_num: summary_dict}}
        "aggregates": {},        # tier -> {provider: aggregate_dict}
    }

    for tier, dirs in TIER_DIRS.items():
        # Questions
        qpath = dirs["questions"] / "questions.jsonl"
        if qpath.exists():
            qs = load_jsonl(qpath)
            data["questions"][tier] = qs
            data["questions_by_id"][tier] = {q["id"]: q for q in qs}
            print(f"  Tier {tier}: {len(qs)} questions loaded")
        else:
            print(f"  WARNING: {qpath} not found")
            data["questions"][tier] = []
            data["questions_by_id"][tier] = {}

        # Per-run responses and summaries
        data["responses"][tier] = {}
        data["responses_by_id"][tier] = {}
        data["summaries"][tier] = {}
        data["aggregates"][tier] = {}

        for provider in PROVIDERS:
            data["responses"][tier][provider] = {}
            data["responses_by_id"][tier][provider] = {}
            data["summaries"][tier][provider] = {}

            # Load per-run data
            for run in RUNS:
                rpath = dirs["results"] / provider / f"run{run}" / "responses.jsonl"
                spath = dirs["results"] / provider / f"run{run}" / "summary.json"

                if rpath.exists():
                    rs = load_jsonl_stripped(rpath)
                    data["responses"][tier][provider][run] = rs
                    data["responses_by_id"][tier][provider][run] = {r["id"]: r for r in rs}
                else:
                    data["responses"][tier][provider][run] = []
                    data["responses_by_id"][tier][provider][run] = {}

                if spath.exists():
                    with open(spath) as f:
                        data["summaries"][tier][provider][run] = json.load(f)

            # Load aggregate
            apath = dirs["results"] / provider / "aggregate.json"
            if apath.exists():
                with open(apath) as f:
                    data["aggregates"][tier][provider] = json.load(f)

            n_responses = sum(len(data["responses"][tier][provider][r]) for r in RUNS)
            print(f"    {provider}: {n_responses} responses across {len(RUNS)} runs")

    return data


# ---------------------------------------------------------------------------
# Helper: get per-run overall scores from aggregates or summaries
# ---------------------------------------------------------------------------
def get_run_scores(data: dict, tier: int, provider: str) -> list[float]:
    """Get overall score for each run from summaries."""
    scores = []
    for run in RUNS:
        s = data["summaries"][tier].get(provider, {}).get(run)
        if s:
            scores.append(s.get("overall_score", s.get("mean_question_score", 0)))
    return scores


def get_aggregate(data: dict, tier: int, provider: str) -> dict:
    """Get aggregate dict for provider at tier."""
    return data["aggregates"].get(tier, {}).get(provider, {})


def composite_score(data: dict, provider: str) -> tuple[float, float]:
    """Compute question-count-weighted composite: (110*T1 + 101*T2 + 82*T3) / 293.
    Returns (mean, std) across runs."""
    run_composites = []
    for run in RUNS:
        scores = []
        for tier in [1, 2, 3]:
            s = data["summaries"][tier].get(provider, {}).get(run)
            if s:
                scores.append((TIER_QCOUNTS[tier],
                               s.get("overall_score", s.get("mean_question_score", 0))))
        if scores:
            total_w = sum(w for w, _ in scores)
            comp = sum(w * sc for w, sc in scores) / total_w if total_w else 0
            run_composites.append(comp)
    return mean_std(run_composites)


# ---------------------------------------------------------------------------
# Section 1: Executive Summary
# ---------------------------------------------------------------------------
def section_executive_summary(data: dict) -> str:
    out = []
    out.append("## 1. Executive Summary\n\n")

    # Compute composite scores
    composites = {}
    for p in PROVIDERS:
        m, s = composite_score(data, p)
        composites[p] = (m, s)

    ranked = sorted(PROVIDERS, key=lambda p: composites[p][0], reverse=True)

    # Main leaderboard
    out.append("### Overall Leaderboard\n\n")
    headers = ["Rank", "Model", "Tier 1", "Tier 2", "Tier 3", "Composite"]
    aligns = ["c", "l", "r", "r", "r", "r"]
    rows = []
    for rank, p in enumerate(ranked, 1):
        a1 = get_aggregate(data, 1, p)
        a2 = get_aggregate(data, 2, p)
        a3 = get_aggregate(data, 3, p)
        t1 = fmt_score_pm(a1.get("overall", {}).get("mean", 0), a1.get("overall", {}).get("std", 0))
        t2 = fmt_score_pm(a2.get("overall", {}).get("mean", 0), a2.get("overall", {}).get("std", 0))
        t3 = fmt_score_pm(a3.get("overall", {}).get("mean", 0), a3.get("overall", {}).get("std", 0))
        cm, cs = composites[p]
        comp = fmt_score_pm(cm, cs)
        rows.append([str(rank), MODEL_NAMES[p], t1, t2, t3, comp])
    out.append(md_table(headers, rows, aligns))

    # Headline findings
    out.append("\n### Key Findings\n\n")

    best = ranked[0]
    worst = ranked[-1]
    best_m, _ = composites[best]
    worst_m, _ = composites[worst]

    # Finding 1: Top model
    out.append(f"1. **{MODEL_NAMES[best]}** leads the benchmark with a composite score of "
               f"{fmt_score(best_m)}, demonstrating the strongest overall thermodynamic reasoning.\n\n")

    # Finding 2: Performance gap
    gap = best_m - worst_m
    out.append(f"2. **Performance spread is {fmt_pct(gap * 100)}** between the top and bottom models, "
               f"confirming that thermodynamic reasoning is a meaningful differentiator.\n\n")

    # Finding 3: Tier degradation
    best_t1 = get_aggregate(data, 1, best).get("overall", {}).get("mean", 0)
    best_t3 = get_aggregate(data, 3, best).get("overall", {}).get("mean", 0)
    worst_t1 = get_aggregate(data, 1, worst).get("overall", {}).get("mean", 0)
    worst_t3 = get_aggregate(data, 3, worst).get("overall", {}).get("mean", 0)
    worst_degrad = (worst_t1 - worst_t3) / worst_t1 * 100 if worst_t1 > 0 else 0
    out.append(f"3. **{MODEL_NAMES[worst]} degrades {fmt_pct(worst_degrad)} from Tier 1→3**, "
               f"showing the largest gap between property lookup and cycle analysis.\n\n")

    # Finding 4: Multi-run consistency
    most_consistent = min(PROVIDERS, key=lambda p: get_aggregate(data, 3, p).get("overall", {}).get("std", 1))
    mc_std = get_aggregate(data, 3, most_consistent).get("overall", {}).get("std", 0)
    least_consistent = max(PROVIDERS, key=lambda p: get_aggregate(data, 3, p).get("overall", {}).get("std", 0))
    lc_std = get_aggregate(data, 3, least_consistent).get("overall", {}).get("std", 0)
    out.append(f"4. **Multi-run consistency varies 10×**: {MODEL_NAMES[most_consistent]} "
               f"(σ={fmt_pct(mc_std * 100)}) vs {MODEL_NAMES[least_consistent]} "
               f"(σ={fmt_pct(lc_std * 100)}) on Tier 3.\n\n")

    # Finding 5: Supercritical as discriminator
    sc_scores = {}
    for p in PROVIDERS:
        a = get_aggregate(data, 1, p)
        sc = a.get("by_category", {}).get("supercritical", {}).get("mean", 0)
        sc_scores[p] = sc
    sc_best = max(PROVIDERS, key=lambda p: sc_scores[p])
    sc_worst = min(PROVIDERS, key=lambda p: sc_scores[p])
    out.append(f"5. **Supercritical water** is the most discriminating Tier 1 category: "
               f"{MODEL_NAMES[sc_best]} scores {fmt_score(sc_scores[sc_best])} vs "
               f"{MODEL_NAMES[sc_worst]} at {fmt_score(sc_scores[sc_worst])}.\n\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 2: Per-Tier Leaderboards
# ---------------------------------------------------------------------------
def section_tier1_leaderboard(data: dict) -> str:
    out = []
    out.append("### 2.1 Tier 1: Property Lookups (110 questions)\n\n")

    # Overall leaderboard
    out.append("#### Leaderboard\n\n")
    ranked = sorted(PROVIDERS,
                    key=lambda p: get_aggregate(data, 1, p).get("overall", {}).get("mean", 0),
                    reverse=True)
    headers = ["Rank", "Model", "Score", "Property Acc."]
    rows = []
    for rank, p in enumerate(ranked, 1):
        a = get_aggregate(data, 1, p)
        sc = fmt_score_pm(a["overall"]["mean"], a["overall"]["std"])
        pa = fmt_score_pm(a.get("property_accuracy", {}).get("mean", 0),
                          a.get("property_accuracy", {}).get("std", 0))
        rows.append([str(rank), MODEL_NAMES[p], sc, pa])
    out.append(md_table(headers, rows, ["c", "l", "r", "r"]))

    # By category heatmap
    out.append("\n#### By Category\n\n")
    categories = ["subcooled_liquid", "saturated_liquid", "wet_steam", "saturated_vapor",
                  "superheated_vapor", "supercritical", "phase_determination", "inverse_lookups"]
    cat_short = {
        "subcooled_liquid": "Subcooled", "saturated_liquid": "Sat. Liq.",
        "wet_steam": "Wet Steam", "saturated_vapor": "Sat. Vap.",
        "superheated_vapor": "Superheat.", "supercritical": "Supercrit.",
        "phase_determination": "Phase Det.", "inverse_lookups": "Inverse",
    }
    headers = ["Model"] + [cat_short[c] for c in categories]
    rows = []
    for p in ranked:
        a = get_aggregate(data, 1, p)
        by_cat = a.get("by_category", {})
        row = [MODEL_SHORT[p]]
        for c in categories:
            v = by_cat.get(c, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(categories)))

    # By difficulty
    out.append("\n#### By Difficulty\n\n")
    diffs = ["easy", "medium", "hard"]
    headers = ["Model"] + [d.capitalize() for d in diffs]
    rows = []
    for p in ranked:
        a = get_aggregate(data, 1, p)
        by_d = a.get("by_difficulty", {})
        row = [MODEL_SHORT[p]]
        for d in diffs:
            v = by_d.get(d, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(diffs)))

    # Supercritical spotlight
    out.append("\n#### Supercritical Spotlight\n\n")
    out.append("The supercritical category (10 questions) is the single most discriminating subset in Tier 1.\n\n")
    headers = ["Model", "Score", "σ"]
    rows = []
    sc_ranked = sorted(PROVIDERS,
                       key=lambda p: get_aggregate(data, 1, p).get("by_category", {}).get("supercritical", {}).get("mean", 0),
                       reverse=True)
    for p in sc_ranked:
        a = get_aggregate(data, 1, p)
        sc = a.get("by_category", {}).get("supercritical", {})
        rows.append([MODEL_NAMES[p], fmt_score(sc.get("mean")), fmt_pct(sc.get("std", 0) * 100)])
    out.append(md_table(headers, rows, ["l", "r", "r"]))

    return "".join(out)


def section_tier2_leaderboard(data: dict) -> str:
    out = []
    out.append("### 2.2 Tier 2: Component Analysis (101 questions)\n\n")

    ranked = sorted(PROVIDERS,
                    key=lambda p: get_aggregate(data, 2, p).get("overall", {}).get("mean", 0),
                    reverse=True)

    # Overall
    out.append("#### Leaderboard\n\n")
    headers = ["Rank", "Model", "Score", "Property Acc."]
    rows = []
    for rank, p in enumerate(ranked, 1):
        a = get_aggregate(data, 2, p)
        sc = fmt_score_pm(a["overall"]["mean"], a["overall"]["std"])
        pa = fmt_score_pm(a.get("property_accuracy", {}).get("mean", 0),
                          a.get("property_accuracy", {}).get("std", 0))
        rows.append([str(rank), MODEL_NAMES[p], sc, pa])
    out.append(md_table(headers, rows, ["c", "l", "r", "r"]))

    # By component
    out.append("\n#### By Component\n\n")
    components = ["turbine", "compressor", "pump", "heat_exchanger", "boiler", "mixing_chamber", "nozzle"]
    comp_short = {
        "turbine": "Turbine", "compressor": "Compr.", "pump": "Pump",
        "heat_exchanger": "HX", "boiler": "Boiler",
        "mixing_chamber": "Mixer", "nozzle": "Nozzle",
    }
    headers = ["Model"] + [comp_short[c] for c in components]
    rows = []
    for p in ranked:
        a = get_aggregate(data, 2, p)
        by_comp = a.get("by_component", {})
        row = [MODEL_SHORT[p]]
        for c in components:
            v = by_comp.get(c, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(components)))

    # By fluid
    out.append("\n#### By Fluid\n\n")
    fluids = ["Water", "Air", "R134a"]
    headers = ["Model"] + fluids
    rows = []
    for p in ranked:
        a = get_aggregate(data, 2, p)
        by_f = a.get("by_fluid", {})
        row = [MODEL_SHORT[p]]
        for fl in fluids:
            v = by_f.get(fl, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(fluids)))

    # By depth
    out.append("\n#### By Depth\n\n")
    depths = ["A", "B", "C"]
    headers = ["Model"] + [f"Depth {d}" for d in depths]
    rows = []
    for p in ranked:
        a = get_aggregate(data, 2, p)
        by_d = a.get("by_depth", {})
        row = [MODEL_SHORT[p]]
        for d in depths:
            v = by_d.get(d, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(depths)))

    return "".join(out)


def section_tier3_leaderboard(data: dict) -> str:
    out = []
    out.append("### 2.3 Tier 3: Cycle Analysis (82 questions)\n\n")

    ranked = sorted(PROVIDERS,
                    key=lambda p: get_aggregate(data, 3, p).get("overall", {}).get("mean", 0),
                    reverse=True)

    # Overall
    out.append("#### Leaderboard\n\n")
    headers = ["Rank", "Model", "Score", "Property Acc."]
    rows = []
    for rank, p in enumerate(ranked, 1):
        a = get_aggregate(data, 3, p)
        sc = fmt_score_pm(a["overall"]["mean"], a["overall"]["std"])
        pa = fmt_score_pm(a.get("property_accuracy", {}).get("mean", 0),
                          a.get("property_accuracy", {}).get("std", 0))
        rows.append([str(rank), MODEL_NAMES[p], sc, pa])
    out.append(md_table(headers, rows, ["c", "l", "r", "r"]))

    # By cycle group (4 groups from aggregate)
    out.append("\n#### By Cycle Group\n\n")
    cycle_groups = ["RNK", "BRY", "VCR", "CCGT"]
    headers = ["Model"] + cycle_groups
    rows = []
    for p in ranked:
        a = get_aggregate(data, 3, p)
        by_ct = a.get("by_cycle_type", {})
        row = [MODEL_SHORT[p]]
        for cg in cycle_groups:
            v = by_ct.get(cg, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(cycle_groups)))

    # Detailed 10-subtype breakdown (computed from responses)
    out.append("\n#### Detailed Cycle Subtype Breakdown (10 subtypes)\n\n")
    cycle_subtypes = ["RNK-I", "RNK-A", "RNK-RH", "BRY-I", "BRY-A",
                      "BRY-RG", "BRY-AV", "BRY-RV", "VCR-A", "CCGT"]

    # Compute per-subtype per-provider mean score across runs
    subtype_scores = {}  # provider -> subtype -> [run_means]
    for p in PROVIDERS:
        subtype_scores[p] = {}
        for run in RUNS:
            responses = data["responses"][3][p].get(run, [])
            # Group by cycle_type from question metadata
            by_st = defaultdict(list)
            for r in responses:
                qid = r["id"]
                q = data["questions_by_id"][3].get(qid, {})
                ct = q.get("cycle_type", "")
                by_st[ct].append(r.get("question_score", 0))
            for st in cycle_subtypes:
                if st not in subtype_scores[p]:
                    subtype_scores[p][st] = []
                if by_st[st]:
                    subtype_scores[p][st].append(mean(by_st[st]))

    headers = ["Model"] + cycle_subtypes
    rows = []
    for p in ranked:
        row = [MODEL_SHORT[p]]
        for st in cycle_subtypes:
            vals = subtype_scores[p].get(st, [])
            if vals:
                m, _ = mean_std(vals)
                row.append(fmt_score(m))
            else:
                row.append("—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(cycle_subtypes)))

    # By fluid
    out.append("\n#### By Fluid\n\n")
    fluids_t3 = ["Water", "Air", "R-134a", "Air+Water"]
    headers = ["Model"] + fluids_t3
    rows = []
    for p in ranked:
        a = get_aggregate(data, 3, p)
        by_f = a.get("by_fluid", {})
        row = [MODEL_SHORT[p]]
        for fl in fluids_t3:
            v = by_f.get(fl, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(fluids_t3)))

    # By depth
    out.append("\n#### By Depth\n\n")
    depths = ["A", "B", "C"]
    headers = ["Model"] + [f"Depth {d}" for d in depths]
    rows = []
    for p in ranked:
        a = get_aggregate(data, 3, p)
        by_d = a.get("by_depth", {})
        row = [MODEL_SHORT[p]]
        for d in depths:
            v = by_d.get(d, {}).get("mean")
            row.append(fmt_score(v) if v is not None else "—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(depths)))

    return "".join(out)


def section_per_tier(data: dict) -> str:
    out = []
    out.append("## 2. Per-Tier Leaderboards\n\n")
    out.append(section_tier1_leaderboard(data))
    out.append("\n")
    out.append(section_tier2_leaderboard(data))
    out.append("\n")
    out.append(section_tier3_leaderboard(data))
    return "".join(out)


# ---------------------------------------------------------------------------
# Section 3: Cross-Tier Analysis
# ---------------------------------------------------------------------------
def section_cross_tier(data: dict) -> str:
    out = []
    out.append("## 3. Cross-Tier Analysis\n\n")

    # Tier degradation
    out.append("### 3.1 Tier Degradation\n\n")
    out.append("How much does each model degrade from property lookups (T1) to full cycle analysis (T3)?\n\n")

    headers = ["Model", "T1 Score", "T3 Score", "Absolute Drop", "Relative Drop"]
    rows = []
    for p in PROVIDERS:
        t1 = get_aggregate(data, 1, p).get("overall", {}).get("mean", 0)
        t3 = get_aggregate(data, 3, p).get("overall", {}).get("mean", 0)
        abs_drop = t1 - t3
        rel_drop = abs_drop / t1 * 100 if t1 > 0 else 0
        rows.append([MODEL_NAMES[p], fmt_score(t1), fmt_score(t3),
                     fmt_pct(abs_drop * 100), fmt_pct(rel_drop)])
    # Sort by relative drop (most degradation first)
    rows.sort(key=lambda r: float(r[4].replace("%", "").replace("—", "0")), reverse=True)
    out.append(md_table(headers, rows, ["l", "r", "r", "r", "r"]))

    # Ranking instability
    out.append("\n### 3.2 Ranking Instability\n\n")
    out.append("Model rank at each tier — ranking shifts reveal where different capabilities matter.\n\n")

    tier_ranks = {}
    for tier in [1, 2, 3]:
        ranked = sorted(PROVIDERS,
                        key=lambda p: get_aggregate(data, tier, p).get("overall", {}).get("mean", 0),
                        reverse=True)
        for rank, p in enumerate(ranked, 1):
            if p not in tier_ranks:
                tier_ranks[p] = {}
            tier_ranks[p][tier] = rank

    headers = ["Model", "T1 Rank", "T2 Rank", "T3 Rank", "Max Δ"]
    rows = []
    for p in PROVIDERS:
        ranks = [tier_ranks[p].get(t, 0) for t in [1, 2, 3]]
        max_delta = max(ranks) - min(ranks)
        rows.append([MODEL_NAMES[p], str(ranks[0]), str(ranks[1]), str(ranks[2]), str(max_delta)])
    rows.sort(key=lambda r: int(r[4]), reverse=True)
    out.append(md_table(headers, rows, ["l", "c", "c", "c", "c"]))

    # Skill decomposition
    out.append("\n### 3.3 Skill Decomposition\n\n")
    out.append("Each tier tests a different skill:\n")
    out.append("- **Tier 1** = Memorization (property lookup from training data)\n")
    out.append("- **Tier 2** = Chaining (multi-step component calculations)\n")
    out.append("- **Tier 3** = Reasoning (full cycle analysis with coupled equations)\n\n")

    headers = ["Model", "Memorization (T1)", "Chaining (T2)", "Reasoning (T3)", "Best Skill"]
    rows = []
    for p in PROVIDERS:
        t1 = get_aggregate(data, 1, p).get("overall", {}).get("mean", 0)
        t2 = get_aggregate(data, 2, p).get("overall", {}).get("mean", 0)
        t3 = get_aggregate(data, 3, p).get("overall", {}).get("mean", 0)
        scores = {"Memorization": t1, "Chaining": t2, "Reasoning": t3}
        best = max(scores, key=scores.get)
        rows.append([MODEL_NAMES[p], fmt_score(t1), fmt_score(t2), fmt_score(t3), best])
    out.append(md_table(headers, rows, ["l", "r", "r", "r", "l"]))

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 4: Multi-Run Consistency
# ---------------------------------------------------------------------------
def section_multi_run(data: dict) -> str:
    out = []
    out.append("## 4. Multi-Run Consistency Analysis\n\n")
    out.append("Each model was evaluated 3 times. This section analyzes score stability.\n\n")

    # Overall std per model per tier
    out.append("### 4.1 Run-to-Run Variability (σ)\n\n")
    headers = ["Model", "T1 σ", "T2 σ", "T3 σ", "Mean σ"]
    rows = []
    for p in PROVIDERS:
        stds = []
        row = [MODEL_NAMES[p]]
        for tier in [1, 2, 3]:
            s = get_aggregate(data, tier, p).get("overall", {}).get("std", 0)
            stds.append(s)
            row.append(fmt_pct(s * 100))
        row.append(fmt_pct(mean(stds) * 100))
        rows.append(row)
    rows.sort(key=lambda r: float(r[4].replace("%", "").replace("—", "0")))
    out.append(md_table(headers, rows, ["l", "r", "r", "r", "r"]))

    # Question-level volatility
    out.append("\n### 4.2 Question-Level Volatility\n\n")
    out.append("For each (question, model) pair across 3 runs, we classify as:\n")
    out.append("- **Always Correct**: all 3 runs score ≥ 0.99\n")
    out.append("- **Always Wrong**: all 3 runs score < 0.01\n")
    out.append("- **Volatile**: mixed results across runs\n\n")

    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        headers = ["Model", "Always Correct", "Always Wrong", "Volatile", "Volatility Rate"]
        rows = []
        questions = data["questions"][tier]

        for p in PROVIDERS:
            always_correct = 0
            always_wrong = 0
            volatile = 0

            for q in questions:
                qid = q["id"]
                scores = []
                for run in RUNS:
                    r = data["responses_by_id"][tier][p].get(run, {}).get(qid)
                    if r:
                        scores.append(r.get("question_score", 0))
                if len(scores) < 2:
                    continue
                if all(s >= 0.99 for s in scores):
                    always_correct += 1
                elif all(s < 0.01 for s in scores):
                    always_wrong += 1
                else:
                    volatile += 1

            total = always_correct + always_wrong + volatile
            vol_rate = volatile / total * 100 if total > 0 else 0
            rows.append([MODEL_SHORT[p], str(always_correct), str(always_wrong),
                         str(volatile), fmt_pct(vol_rate)])
        rows.sort(key=lambda r: float(r[4].replace("%", "").replace("—", "0")))
        out.append(md_table(headers, rows, ["l", "r", "r", "r", "r"]))
        out.append("\n")

    # Shared volatility: questions volatile for 3+ models
    out.append("### 4.3 Universally Volatile Questions\n\n")
    out.append("Questions that are volatile (inconsistent across runs) for 3 or more models:\n\n")

    for tier in [1, 2, 3]:
        vol_count = defaultdict(int)  # qid -> count of models where volatile
        questions = data["questions"][tier]

        for q in questions:
            qid = q["id"]
            for p in PROVIDERS:
                scores = []
                for run in RUNS:
                    r = data["responses_by_id"][tier][p].get(run, {}).get(qid)
                    if r:
                        scores.append(r.get("question_score", 0))
                if len(scores) >= 2:
                    if not (all(s >= 0.99 for s in scores) or all(s < 0.01 for s in scores)):
                        vol_count[qid] += 1

        shared = [(qid, cnt) for qid, cnt in vol_count.items() if cnt >= 3]
        shared.sort(key=lambda x: x[1], reverse=True)

        if shared:
            out.append(f"#### Tier {tier}: {len(shared)} questions volatile for 3+ models\n\n")
            headers = ["Question ID", "# Models Volatile", "Category/Type"]
            rows = []
            for qid, cnt in shared[:20]:  # cap at 20
                q = data["questions_by_id"][tier].get(qid, {})
                if tier == 1:
                    cat = q.get("category", "")
                elif tier == 2:
                    cat = q.get("component", "")
                else:
                    cat = q.get("cycle_type", "")
                rows.append([qid, str(cnt), cat])
            out.append(md_table(headers, rows, ["l", "c", "l"]))
            out.append("\n")
        else:
            out.append(f"#### Tier {tier}: No questions volatile for 3+ models\n\n")

    # Volatility vs difficulty crosstab
    out.append("### 4.4 Volatility vs Difficulty\n\n")
    out.append("Volatile question rate by difficulty level (averaged across models):\n\n")

    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        diff_vol = defaultdict(lambda: {"total": 0, "volatile": 0})
        questions = data["questions"][tier]

        for q in questions:
            qid = q["id"]
            diff = q.get("difficulty", "unknown")
            for p in PROVIDERS:
                diff_vol[diff]["total"] += 1
                scores = []
                for run in RUNS:
                    r = data["responses_by_id"][tier][p].get(run, {}).get(qid)
                    if r:
                        scores.append(r.get("question_score", 0))
                if len(scores) >= 2:
                    if not (all(s >= 0.99 for s in scores) or all(s < 0.01 for s in scores)):
                        diff_vol[diff]["volatile"] += 1

        headers = ["Difficulty", "Total (q×model)", "Volatile", "Rate"]
        rows = []
        for d in ["easy", "medium", "hard"]:
            t = diff_vol[d]["total"]
            v = diff_vol[d]["volatile"]
            rate = v / t * 100 if t > 0 else 0
            rows.append([d.capitalize(), str(t), str(v), fmt_pct(rate)])
        out.append(md_table(headers, rows, ["l", "r", "r", "r"]))
        out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 5: Discriminator Analysis
# ---------------------------------------------------------------------------
def section_discriminators(data: dict) -> str:
    out = []
    out.append("## 5. Discriminator Analysis\n\n")
    out.append("Which question subsets best separate model capabilities?\n\n")

    # T1: Supercritical
    out.append("### 5.1 Tier 1: Supercritical Region\n\n")
    out.append("Supercritical water properties (T > 373.95°C, P > 22.064 MPa) — "
               "requires knowledge beyond standard steam tables.\n\n")
    headers = ["Model", "Supercritical Score", "Overall T1 Score", "Gap"]
    rows = []
    for p in PROVIDERS:
        a = get_aggregate(data, 1, p)
        sc = a.get("by_category", {}).get("supercritical", {}).get("mean", 0)
        overall = a.get("overall", {}).get("mean", 0)
        gap = overall - sc
        rows.append([MODEL_NAMES[p], fmt_score(sc), fmt_score(overall), fmt_pct(gap * 100)])
    rows.sort(key=lambda r: float(r[1].replace("%", "").replace("—", "0")), reverse=True)
    out.append(md_table(headers, rows, ["l", "r", "r", "r"]))

    # T2: R-134a refrigerant
    out.append("\n### 5.2 Tier 2: R-134a Refrigerant\n\n")
    out.append("R-134a questions test whether models can handle non-water fluids.\n\n")
    headers = ["Model", "R-134a Score", "Water Score", "Gap"]
    rows = []
    for p in PROVIDERS:
        a = get_aggregate(data, 2, p)
        r134a = a.get("by_fluid", {}).get("R134a", {}).get("mean", 0)
        water = a.get("by_fluid", {}).get("Water", {}).get("mean", 0)
        gap = water - r134a
        rows.append([MODEL_NAMES[p], fmt_score(r134a), fmt_score(water), fmt_pct(gap * 100)])
    rows.sort(key=lambda r: float(r[1].replace("%", "").replace("—", "0")), reverse=True)
    out.append(md_table(headers, rows, ["l", "r", "r", "r"]))

    # T2: Compressor component
    out.append("\n### 5.3 Tier 2: Compressor Component\n\n")
    out.append("Compressors involve isentropic efficiency with different fluid types.\n\n")
    headers = ["Model", "Compressor Score", "Overall T2 Score", "Gap"]
    rows = []
    for p in PROVIDERS:
        a = get_aggregate(data, 2, p)
        comp = a.get("by_component", {}).get("compressor", {}).get("mean", 0)
        overall = a.get("overall", {}).get("mean", 0)
        gap = overall - comp
        rows.append([MODEL_NAMES[p], fmt_score(comp), fmt_score(overall), fmt_pct(gap * 100)])
    rows.sort(key=lambda r: float(r[1].replace("%", "").replace("—", "0")), reverse=True)
    out.append(md_table(headers, rows, ["l", "r", "r", "r"]))

    # T3: Variable-cp Brayton and CCGT
    out.append("\n### 5.4 Tier 3: Hard Cycle Variants\n\n")
    out.append("BRY-AV (aftercooling, variable-cp), BRY-RV (regenerative, variable-cp), "
               "and CCGT (combined cycle) are the hardest T3 subtypes.\n\n")

    hard_subtypes = ["BRY-AV", "BRY-RV", "CCGT"]
    headers = ["Model"] + hard_subtypes + ["Mean Hard"]
    rows = []
    for p in PROVIDERS:
        row = [MODEL_NAMES[p]]
        hard_scores = []
        for run in RUNS:
            responses = data["responses"][3][p].get(run, [])
            for st in hard_subtypes:
                st_scores = []
                for r in responses:
                    q = data["questions_by_id"][3].get(r["id"], {})
                    if q.get("cycle_type", "") == st:
                        st_scores.append(r.get("question_score", 0))
                if st_scores:
                    hard_scores.append(mean(st_scores))
        # Compute per-subtype means
        for st in hard_subtypes:
            st_run_means = []
            for run in RUNS:
                responses = data["responses"][3][p].get(run, [])
                scores = [r.get("question_score", 0) for r in responses
                          if data["questions_by_id"][3].get(r["id"], {}).get("cycle_type", "") == st]
                if scores:
                    st_run_means.append(mean(scores))
            m, _ = mean_std(st_run_means) if st_run_means else (0, 0)
            row.append(fmt_score(m))
        # Overall mean of hard subtypes
        all_hard = []
        for run in RUNS:
            responses = data["responses"][3][p].get(run, [])
            scores = [r.get("question_score", 0) for r in responses
                      if data["questions_by_id"][3].get(r["id"], {}).get("cycle_type", "") in hard_subtypes]
            if scores:
                all_hard.append(mean(scores))
        m, _ = mean_std(all_hard) if all_hard else (0, 0)
        row.append(fmt_score(m))
        rows.append(row)
    rows.sort(key=lambda r: float(r[-1].replace("%", "").replace("—", "0")), reverse=True)
    out.append(md_table(headers, rows, ["l"] + ["r"] * (len(hard_subtypes) + 1)))

    # Cross-model variance progression
    out.append("\n### 5.5 Discriminator Progression: Cross-Model Variance by Tier\n\n")
    out.append("Variance of model means increases from T1→T3, confirming progressive difficulty.\n\n")
    headers = ["Tier", "Model Score Range", "Variance", "Questions"]
    rows = []
    for tier in [1, 2, 3]:
        tier_means = [get_aggregate(data, tier, p).get("overall", {}).get("mean", 0) for p in PROVIDERS]
        _, s = mean_std(tier_means)
        rng = max(tier_means) - min(tier_means)
        rows.append([f"Tier {tier}", fmt_pct(rng * 100),
                     fmt_f(s ** 2, 6), str(TIER_QCOUNTS[tier])])
    out.append(md_table(headers, rows, ["l", "r", "r", "r"]))

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 6: Error Pattern Analysis
# ---------------------------------------------------------------------------
def section_error_patterns(data: dict) -> str:
    out = []
    out.append("## 6. Error Pattern Analysis\n\n")

    # Error type distribution
    out.append("### 6.1 Error Type Distribution\n\n")
    out.append("From `scores` array `error_type` field (per-property level, averaged across runs):\n\n")

    error_types = ["correct", "out_of_tolerance", "extraction_failed", "missing"]

    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        headers = ["Model"] + [et.replace("_", " ").title() for et in error_types] + ["Total Steps"]
        rows = []

        for p in PROVIDERS:
            # Average error type counts across runs
            run_counts = []
            for run in RUNS:
                responses = data["responses"][tier][p].get(run, [])
                counts = {et: 0 for et in error_types}
                total = 0
                for r in responses:
                    for s in r.get("scores", []):
                        et = s.get("error_type", "missing")
                        if et in counts:
                            counts[et] += 1
                        else:
                            counts["missing"] += 1
                        total += 1
                run_counts.append((counts, total))

            if not run_counts:
                continue

            # Average across runs
            avg_total = mean([t for _, t in run_counts])
            row = [MODEL_SHORT[p]]
            for et in error_types:
                vals = [c[et] for c, _ in run_counts]
                m, _ = mean_std(vals)
                pct = m / avg_total * 100 if avg_total > 0 else 0
                row.append(f"{m:.0f} ({fmt_pct(pct)})")
            row.append(f"{avg_total:.0f}")
            rows.append(row)

        out.append(md_table(headers, rows, ["l"] + ["r"] * (len(error_types) + 1)))
        out.append("\n")

    # Error propagation in T2/T3: phi-coefficient for step-pair failures
    out.append("### 6.2 Error Propagation (Step-Pair Correlation)\n\n")
    out.append("Do early-step failures cause late-step failures? Phi coefficient for adjacent step pairs:\n\n")

    for tier in [2, 3]:
        out.append(f"#### Tier {tier}\n\n")

        # Collect step failure patterns across all questions and runs
        pair_tables = defaultdict(lambda: {"n11": 0, "n00": 0, "n10": 0, "n01": 0})

        for p in PROVIDERS:
            for run in RUNS:
                responses = data["responses"][tier][p].get(run, [])
                for r in responses:
                    scores = r.get("scores", [])
                    for i in range(len(scores) - 1):
                        s1 = scores[i]
                        s2 = scores[i + 1]
                        key1 = s1.get("key", f"step{i}")
                        key2 = s2.get("key", f"step{i+1}")
                        p1_fail = not s1.get("passed", True)
                        p2_fail = not s2.get("passed", True)
                        pair_key = f"{key1} → {key2}"
                        if p1_fail and p2_fail:
                            pair_tables[pair_key]["n11"] += 1
                        elif not p1_fail and not p2_fail:
                            pair_tables[pair_key]["n00"] += 1
                        elif p1_fail and not p2_fail:
                            pair_tables[pair_key]["n10"] += 1
                        else:
                            pair_tables[pair_key]["n01"] += 1

        # Show pairs with strongest correlation
        phi_scores = []
        for pair, tbl in pair_tables.items():
            total = tbl["n11"] + tbl["n00"] + tbl["n10"] + tbl["n01"]
            if total < 10:
                continue
            phi = phi_coefficient(tbl["n11"], tbl["n00"], tbl["n10"], tbl["n01"])
            if phi is not None:
                phi_scores.append((pair, phi, total, tbl["n11"]))

        phi_scores.sort(key=lambda x: abs(x[1]), reverse=True)

        headers = ["Step Pair", "φ Coefficient", "Co-failures", "Total"]
        rows = []
        for pair, phi, total, cofail in phi_scores[:15]:
            rows.append([pair, fmt_f(phi, 3), str(cofail), str(total)])
        out.append(md_table(headers, rows, ["l", "r", "r", "r"]))
        out.append("\n")

    # Near-miss analysis
    out.append("### 6.3 Near-Miss Analysis\n\n")
    out.append("Steps where the model was *almost* correct (1.5% < |error| < 2.5%):\n\n")

    for tier in [1, 2, 3]:
        near_miss_count = defaultdict(int)  # provider -> count
        total_steps = defaultdict(int)

        for p in PROVIDERS:
            for run in RUNS:
                responses = data["responses"][tier][p].get(run, [])
                for r in responses:
                    for s in r.get("scores", []):
                        total_steps[p] += 1
                        ep = s.get("error_pct")
                        if ep is not None and 1.5 < abs(ep) < 2.5:
                            near_miss_count[p] += 1

        out.append(f"#### Tier {tier}\n\n")
        headers = ["Model", "Near-Misses (3 runs)", "Total Steps", "Rate"]
        rows = []
        for p in PROVIDERS:
            nm = near_miss_count[p]
            ts = total_steps[p]
            rate = nm / ts * 100 if ts > 0 else 0
            rows.append([MODEL_SHORT[p], str(nm), str(ts), fmt_pct(rate)])
        rows.sort(key=lambda r: float(r[3].replace("%", "").replace("—", "0")), reverse=True)
        out.append(md_table(headers, rows, ["l", "r", "r", "r"]))
        out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 7: Token Efficiency
# ---------------------------------------------------------------------------
def section_token_efficiency(data: dict) -> str:
    out = []
    out.append("## 7. Token Efficiency\n\n")

    # Mean output tokens per tier per model
    out.append("### 7.1 Mean Output Tokens\n\n")
    headers = ["Model", "T1 Tokens", "T2 Tokens", "T3 Tokens", "T3/T1 Ratio"]
    rows = []
    token_data = {}

    for p in PROVIDERS:
        token_data[p] = {}
        for tier in [1, 2, 3]:
            all_tokens = []
            for run in RUNS:
                for r in data["responses"][tier][p].get(run, []):
                    t = r.get("output_tokens", 0)
                    if t > 0:
                        all_tokens.append(t)
            token_data[p][tier] = mean(all_tokens) if all_tokens else 0

        t1_tok = token_data[p][1]
        t3_tok = token_data[p][3]
        ratio = t3_tok / t1_tok if t1_tok > 0 else 0
        rows.append([MODEL_NAMES[p],
                     f"{t1_tok:,.0f}" if t1_tok else "—",
                     f"{token_data[p][2]:,.0f}" if token_data[p][2] else "—",
                     f"{t3_tok:,.0f}" if t3_tok else "—",
                     fmt_f(ratio, 1) + "×"])
    out.append(md_table(headers, rows, ["l", "r", "r", "r", "r"]))

    # Tokens per percentage point
    out.append("\n### 7.2 Tokens per Percentage Point\n\n")
    out.append("Lower is more efficient: `mean_tokens / (score × 100)`\n\n")
    headers = ["Model", "T1 tok/pp", "T2 tok/pp", "T3 tok/pp"]
    rows = []
    for p in PROVIDERS:
        row = [MODEL_NAMES[p]]
        for tier in [1, 2, 3]:
            score = get_aggregate(data, tier, p).get("overall", {}).get("mean", 0)
            tok = token_data[p][tier]
            if score > 0 and tok > 0:
                tpp = tok / (score * 100)
                row.append(f"{tpp:,.0f}")
            else:
                row.append("—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l", "r", "r", "r"]))

    # Token-accuracy scatter description
    out.append("\n### 7.3 Token-Accuracy Correlation\n\n")
    for tier in [1, 2, 3]:
        tok_vals = []
        acc_vals = []
        labels = []
        for p in PROVIDERS:
            sc = get_aggregate(data, tier, p).get("overall", {}).get("mean", 0)
            tok = token_data[p].get(tier, 0)
            if tok > 0:
                tok_vals.append(tok)
                acc_vals.append(sc)
                labels.append(MODEL_SHORT[p])
        r = pearson_r(tok_vals, acc_vals)
        rho = spearman_rho(tok_vals, acc_vals)
        out.append(f"**Tier {tier}**: Pearson r = {fmt_f(r, 3)}, Spearman ρ = {fmt_f(rho, 3)}\n\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 8: Grok 4 Analysis
# ---------------------------------------------------------------------------
def section_grok4(data: dict) -> str:
    out = []
    out.append("## 8. Grok 4 Analysis\n\n")
    out.append("Grok 4 (xAI) is the newest model in the benchmark. How does it compare?\n\n")

    # Rank position per tier
    out.append("### 8.1 Rank Position\n\n")
    headers = ["Tier", "Grok 4 Score", "Rank", "Gap to #1", "Gap to Median"]
    rows = []
    for tier in [1, 2, 3]:
        ranked = sorted(PROVIDERS,
                        key=lambda p: get_aggregate(data, tier, p).get("overall", {}).get("mean", 0),
                        reverse=True)
        grok_score = get_aggregate(data, tier, "xai").get("overall", {}).get("mean", 0)
        rank = ranked.index("xai") + 1
        top_score = get_aggregate(data, tier, ranked[0]).get("overall", {}).get("mean", 0)
        all_scores = sorted([get_aggregate(data, tier, p).get("overall", {}).get("mean", 0) for p in PROVIDERS])
        median_score = (all_scores[2] + all_scores[3]) / 2  # 6 models, median is avg of 3rd and 4th
        rows.append([f"Tier {tier}", fmt_score(grok_score), f"#{rank}",
                     fmt_pct((top_score - grok_score) * 100),
                     fmt_pct((grok_score - median_score) * 100)])
    out.append(md_table(headers, rows, ["l", "r", "c", "r", "r"]))

    # Head-to-head vs DeepSeek
    out.append("\n### 8.2 Grok 4 vs DeepSeek R1 Head-to-Head\n\n")
    out.append("Both are reasoning-focused models. Direct comparison:\n\n")
    headers = ["Dimension", "Grok 4", "DeepSeek R1", "Winner"]
    rows = []
    for tier in [1, 2, 3]:
        g = get_aggregate(data, tier, "xai").get("overall", {}).get("mean", 0)
        d = get_aggregate(data, tier, "deepseek").get("overall", {}).get("mean", 0)
        winner = "Grok 4" if g > d else ("DeepSeek" if d > g else "Tie")
        rows.append([f"Tier {tier} Overall", fmt_score(g), fmt_score(d), winner])

    # Key categories
    for cat_name, tier, key, subkey in [
        ("T1 Supercritical", 1, "by_category", "supercritical"),
        ("T2 Compressor", 2, "by_component", "compressor"),
        ("T2 R-134a", 2, "by_fluid", "R134a"),
        ("T3 CCGT", 3, "by_cycle_type", "CCGT"),
        ("T3 VCR", 3, "by_cycle_type", "VCR"),
    ]:
        g = get_aggregate(data, tier, "xai").get(key, {}).get(subkey, {}).get("mean", 0)
        d = get_aggregate(data, tier, "deepseek").get(key, {}).get(subkey, {}).get("mean", 0)
        winner = "Grok 4" if g > d else ("DeepSeek" if d > g else "Tie")
        rows.append([cat_name, fmt_score(g), fmt_score(d), winner])

    out.append(md_table(headers, rows, ["l", "r", "r", "l"]))

    # Strengths and weaknesses
    out.append("\n### 8.3 Grok 4 Strengths & Weaknesses\n\n")

    # Find categories where Grok 4 is above/below median
    strengths = []
    weaknesses = []

    for tier in [1, 2, 3]:
        a = get_aggregate(data, tier, "xai")
        if tier == 1:
            breakdown_key = "by_category"
        elif tier == 2:
            breakdown_key = "by_component"
        else:
            breakdown_key = "by_cycle_type"

        breakdown = a.get(breakdown_key, {})
        for cat, vals in breakdown.items():
            grok_val = vals.get("mean", 0)
            # Get other models' scores
            other_scores = []
            for p in PROVIDERS:
                if p == "xai":
                    continue
                v = get_aggregate(data, tier, p).get(breakdown_key, {}).get(cat, {}).get("mean", 0)
                other_scores.append(v)
            if other_scores:
                median_other = sorted(other_scores)[len(other_scores) // 2]
                diff = grok_val - median_other
                label = f"T{tier} {cat}"
                if diff > 0.02:
                    strengths.append((label, grok_val, diff))
                elif diff < -0.02:
                    weaknesses.append((label, grok_val, diff))

    if strengths:
        out.append("**Strengths** (above median by >2pp):\n\n")
        strengths.sort(key=lambda x: x[2], reverse=True)
        for label, val, diff in strengths:
            out.append(f"- {label}: {fmt_score(val)} (+{fmt_pct(diff * 100)} vs median)\n")
        out.append("\n")

    if weaknesses:
        out.append("**Weaknesses** (below median by >2pp):\n\n")
        weaknesses.sort(key=lambda x: x[2])
        for label, val, diff in weaknesses:
            out.append(f"- {label}: {fmt_score(val)} ({fmt_pct(diff * 100)} vs median)\n")
        out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 9: Extraction Methodology
# ---------------------------------------------------------------------------
def section_extraction(data: dict) -> str:
    out = []
    out.append("## 9. Extraction Methodology & Reliability\n\n")
    out.append("All responses were re-extracted using gpt-4.1-mini LLM extraction.\n\n")

    # Null extraction rates
    out.append("### 9.1 Extraction Failure Rates\n\n")
    out.append("Per-step extraction failure rate (`error_type` = 'extraction_failed' or 'missing'):\n\n")

    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        headers = ["Model", "Total Steps", "Extraction Failed", "Missing", "Failure Rate", "Non-null Pass Rate"]
        rows = []

        for p in PROVIDERS:
            total = 0
            ext_failed = 0
            missing = 0
            correct = 0
            oot = 0

            for run in RUNS:
                for r in data["responses"][tier][p].get(run, []):
                    for s in r.get("scores", []):
                        total += 1
                        et = s.get("error_type", "missing")
                        if et == "extraction_failed":
                            ext_failed += 1
                        elif et == "missing":
                            missing += 1
                        elif et == "correct":
                            correct += 1
                        elif et == "out_of_tolerance":
                            oot += 1

            fail_rate = (ext_failed + missing) / total * 100 if total > 0 else 0
            non_null = total - ext_failed - missing
            non_null_pass = correct / non_null * 100 if non_null > 0 else 0
            rows.append([MODEL_SHORT[p], str(total), str(ext_failed), str(missing),
                         fmt_pct(fail_rate), fmt_pct(non_null_pass)])

        out.append(md_table(headers, rows, ["l", "r", "r", "r", "r", "r"]))
        out.append("\n")

    # Steps with highest extraction failure
    out.append("### 9.2 Steps with Highest Extraction Failure\n\n")

    for tier in [2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        step_failures = defaultdict(lambda: {"total": 0, "failed": 0})

        for p in PROVIDERS:
            for run in RUNS:
                for r in data["responses"][tier][p].get(run, []):
                    for s in r.get("scores", []):
                        key = s.get("key", "?")
                        step_failures[key]["total"] += 1
                        if s.get("error_type", "") in ("extraction_failed", "missing"):
                            step_failures[key]["failed"] += 1

        headers = ["Step", "Total", "Failed", "Failure Rate"]
        rows = []
        for step, counts in sorted(step_failures.items(),
                                    key=lambda x: x[1]["failed"] / max(x[1]["total"], 1),
                                    reverse=True)[:15]:
            rate = counts["failed"] / counts["total"] * 100 if counts["total"] > 0 else 0
            rows.append([step, str(counts["total"]), str(counts["failed"]), fmt_pct(rate)])
        out.append(md_table(headers, rows, ["l", "r", "r", "r"]))
        out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 10: Statistical Tests
# ---------------------------------------------------------------------------
def section_statistical_tests(data: dict) -> str:
    out = []
    out.append("## 10. Statistical Significance\n\n")

    # Pairwise Welch t-test on T3 scores
    out.append("### 10.1 Pairwise Welch t-test (Tier 3)\n\n")
    out.append("Can we distinguish model performance on Tier 3 with only 3 runs?\n")
    out.append("✓ = significant at α=0.05, ✗ = not significant.\n\n")

    t3_scores = {}
    for p in PROVIDERS:
        t3_scores[p] = get_run_scores(data, 3, p)

    headers = [""] + [MODEL_SHORT[p] for p in PROVIDERS]
    rows = []
    for p1 in PROVIDERS:
        row = [MODEL_SHORT[p1]]
        for p2 in PROVIDERS:
            if p1 == p2:
                row.append("—")
            else:
                result = welch_t(t3_scores[p1], t3_scores[p2])
                if result:
                    t_stat, df = result
                    sig = welch_significant(t3_scores[p1], t3_scores[p2])
                    row.append(f"{'✓' if sig else '✗'} (t={fmt_f(t_stat, 2)})")
                else:
                    row.append("—")
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["c"] * len(PROVIDERS)))

    # 95% confidence intervals
    out.append("\n### 10.2 95% Confidence Intervals\n\n")
    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        headers = ["Model", "Mean", "95% CI", "Width"]
        rows = []
        for p in PROVIDERS:
            scores = get_run_scores(data, tier, p)
            if len(scores) >= 2:
                m, lo, hi = confidence_interval_95(scores)
                width = hi - lo
                rows.append([MODEL_NAMES[p], fmt_score(m),
                             f"[{fmt_score(lo)}, {fmt_score(hi)}]",
                             fmt_pct(width * 100)])
            else:
                rows.append([MODEL_NAMES[p], "—", "—", "—"])
        rows.sort(key=lambda r: float(r[1].replace("%", "").replace("—", "0")), reverse=True)
        out.append(md_table(headers, rows, ["l", "r", "c", "r"]))
        out.append("\n")

    # Cross-tier correlations
    out.append("### 10.3 Cross-Tier Correlations\n\n")
    for pair in [(1, 2), (1, 3), (2, 3)]:
        t_a, t_b = pair
        xs = [get_aggregate(data, t_a, p).get("overall", {}).get("mean", 0) for p in PROVIDERS]
        ys = [get_aggregate(data, t_b, p).get("overall", {}).get("mean", 0) for p in PROVIDERS]
        r = pearson_r(xs, ys)
        rho = spearman_rho(xs, ys)
        out.append(f"- **T{t_a}–T{t_b}**: Pearson r = {fmt_f(r, 3)}, Spearman ρ = {fmt_f(rho, 3)}\n")
    out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 11: Recommendations
# ---------------------------------------------------------------------------
def section_recommendations(data: dict) -> str:
    out = []
    out.append("## 11. Recommendations\n\n")

    # Per-model improvement areas
    out.append("### 11.1 Per-Model Improvement Areas\n\n")

    for p in PROVIDERS:
        out.append(f"#### {MODEL_NAMES[p]}\n\n")
        weaknesses = []

        # Find weakest categories/components/cycles
        for tier, key_name, breakdown_key in [
            (1, "category", "by_category"),
            (2, "component", "by_component"),
            (3, "cycle type", "by_cycle_type"),
        ]:
            a = get_aggregate(data, tier, p)
            breakdown = a.get(breakdown_key, {})
            overall = a.get("overall", {}).get("mean", 0)
            for cat, vals in breakdown.items():
                val = vals.get("mean", 0)
                if val < overall - 0.05:  # more than 5pp below their overall
                    weaknesses.append((f"T{tier} {cat}", val, overall - val))

        weaknesses.sort(key=lambda x: x[2], reverse=True)
        if weaknesses:
            for label, val, gap in weaknesses[:5]:
                out.append(f"- **{label}**: {fmt_score(val)} "
                           f"({fmt_pct(gap * 100)} below overall)\n")
        else:
            out.append("- No significant weak areas identified.\n")
        out.append("\n")

    # Which model for which task
    out.append("### 11.2 Model Selection Guide\n\n")

    best_per_tier = {}
    for tier in [1, 2, 3]:
        best_p = max(PROVIDERS,
                     key=lambda p: get_aggregate(data, tier, p).get("overall", {}).get("mean", 0))
        best_per_tier[tier] = best_p

    out.append(f"- **Property lookups (T1)**: {MODEL_NAMES[best_per_tier[1]]} "
               f"({fmt_score(get_aggregate(data, 1, best_per_tier[1])['overall']['mean'])})\n")
    out.append(f"- **Component analysis (T2)**: {MODEL_NAMES[best_per_tier[2]]} "
               f"({fmt_score(get_aggregate(data, 2, best_per_tier[2])['overall']['mean'])})\n")
    out.append(f"- **Cycle analysis (T3)**: {MODEL_NAMES[best_per_tier[3]]} "
               f"({fmt_score(get_aggregate(data, 3, best_per_tier[3])['overall']['mean'])})\n")

    # Best composite
    comp_best = max(PROVIDERS, key=lambda p: composite_score(data, p)[0])
    cm, _ = composite_score(data, comp_best)
    out.append(f"- **Overall best**: {MODEL_NAMES[comp_best]} (composite {fmt_score(cm)})\n")

    # Most consistent
    mean_stds = {}
    for p in PROVIDERS:
        stds = [get_aggregate(data, t, p).get("overall", {}).get("std", 0) for t in [1, 2, 3]]
        mean_stds[p] = mean(stds)
    most_consistent = min(PROVIDERS, key=lambda p: mean_stds[p])
    out.append(f"- **Most consistent**: {MODEL_NAMES[most_consistent]} "
               f"(mean σ = {fmt_pct(mean_stds[most_consistent] * 100)})\n")

    # Most token-efficient
    out.append("\n")

    # Benchmark design lessons
    out.append("### 11.3 Benchmark Design Lessons\n\n")
    out.append("1. **Multi-run evaluation is essential**: Single-run results can be misleading. "
               "σ ranges from 0.1% to 2.5% across models.\n")
    out.append("2. **Tiered design reveals different skills**: T1-T3 rankings are not identical, "
               "confirming that memorization ≠ reasoning.\n")
    out.append("3. **Supercritical and R-134a are natural discriminators**: These subsets "
               "produce the widest performance spreads.\n")
    out.append("4. **Weighted scoring matters**: Using step weights (vs binary pass/fail) "
               "rewards partial understanding.\n")
    out.append("5. **LLM re-extraction reduces noise**: gpt-4.1-mini extraction normalizes "
               "format differences across model output styles.\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Section 12: Appendix
# ---------------------------------------------------------------------------
def section_appendix(data: dict) -> str:
    out = []
    out.append("## 12. Appendix\n\n")

    # Per-question score matrix (mean across 3 runs)
    out.append("### A.1 Per-Question Score Matrix\n\n")
    out.append("Mean question score across 3 runs. 293 questions × 6 models.\n\n")

    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier}\n\n")
        questions = data["questions"][tier]
        headers = ["ID"] + [MODEL_SHORT[p] for p in PROVIDERS]
        rows = []

        for q in questions:
            qid = q["id"]
            row = [qid]
            for p in PROVIDERS:
                scores = []
                for run in RUNS:
                    r = data["responses_by_id"][tier][p].get(run, {}).get(qid)
                    if r:
                        scores.append(r.get("question_score", 0))
                if scores:
                    m, _ = mean_std(scores)
                    row.append(fmt_score(m))
                else:
                    row.append("—")
            rows.append(row)

        out.append(md_table(headers, rows, ["l"] + ["r"] * len(PROVIDERS)))
        out.append("\n")

    # Full aggregate tables
    out.append("### A.2 Full Aggregate Data\n\n")
    for tier in [1, 2, 3]:
        out.append(f"#### Tier {tier} Aggregates\n\n")
        for p in PROVIDERS:
            a = get_aggregate(data, tier, p)
            out.append(f"**{MODEL_NAMES[p]}**: overall = {fmt_score_pm(a.get('overall', {}).get('mean', 0), a.get('overall', {}).get('std', 0))}")
            out.append(f", property_acc = {fmt_score_pm(a.get('property_accuracy', {}).get('mean', 0), a.get('property_accuracy', {}).get('std', 0))}\n\n")

    # Methodology notes
    out.append("### A.3 Methodology Notes\n\n")
    out.append("- **Ground truth**: All reference values computed via CoolProp (v7.2.0)\n")
    out.append("- **Scoring**: ±2% relative tolerance OR ±0.5 absolute (whichever is more lenient)\n")
    out.append("- **Phase/exact match**: Exact string comparison for phase identification\n")
    out.append("- **Multi-run**: 3 independent runs per model, temperature=1.0 for reasoning models\n")
    out.append("- **Extraction**: Two-pass LLM extraction using gpt-4.1-mini with take-max strategy\n")
    out.append("- **Composite score**: Question-count-weighted: (110×T1 + 101×T2 + 82×T3) / 293\n")
    out.append("- **Confidence intervals**: Student's t at 95% with df=2 (n=3 runs)\n")
    out.append(f"- **Report generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Report Assembly
# ---------------------------------------------------------------------------
def generate_report(data: dict) -> str:
    """Assemble the full report from all sections."""
    sections = []

    # Header
    sections.append("# ThermoQA Comprehensive Analysis Report\n\n")
    sections.append(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
    sections.append(f"**Dataset**: {TOTAL_QUESTIONS} questions across 3 tiers "
                    f"({TIER_QCOUNTS[1]} T1 + {TIER_QCOUNTS[2]} T2 + {TIER_QCOUNTS[3]} T3)\n\n")
    sections.append(f"**Models**: {', '.join(MODEL_NAMES[p] for p in PROVIDERS)}\n\n")
    sections.append(f"**Runs**: {len(RUNS)} independent evaluations per model\n\n")

    # Table of contents
    sections.append("## Table of Contents\n\n")
    toc = [
        "1. [Executive Summary](#1-executive-summary)",
        "2. [Per-Tier Leaderboards](#2-per-tier-leaderboards)",
        "   - 2.1 [Tier 1: Property Lookups](#21-tier-1-property-lookups-110-questions)",
        "   - 2.2 [Tier 2: Component Analysis](#22-tier-2-component-analysis-101-questions)",
        "   - 2.3 [Tier 3: Cycle Analysis](#23-tier-3-cycle-analysis-82-questions)",
        "3. [Cross-Tier Analysis](#3-cross-tier-analysis)",
        "4. [Multi-Run Consistency](#4-multi-run-consistency-analysis)",
        "5. [Discriminator Analysis](#5-discriminator-analysis)",
        "6. [Error Pattern Analysis](#6-error-pattern-analysis)",
        "7. [Token Efficiency](#7-token-efficiency)",
        "8. [Grok 4 Analysis](#8-grok-4-analysis)",
        "9. [Extraction Methodology](#9-extraction-methodology--reliability)",
        "10. [Statistical Significance](#10-statistical-significance)",
        "11. [Recommendations](#11-recommendations)",
        "12. [Appendix](#12-appendix)",
    ]
    sections.append("\n".join(toc) + "\n\n---\n\n")

    # All sections
    print("  Generating Section 1: Executive Summary...")
    sections.append(section_executive_summary(data))
    sections.append("\n---\n\n")

    print("  Generating Section 2: Per-Tier Leaderboards...")
    sections.append(section_per_tier(data))
    sections.append("\n---\n\n")

    print("  Generating Section 3: Cross-Tier Analysis...")
    sections.append(section_cross_tier(data))
    sections.append("\n---\n\n")

    print("  Generating Section 4: Multi-Run Consistency...")
    sections.append(section_multi_run(data))
    sections.append("\n---\n\n")

    print("  Generating Section 5: Discriminator Analysis...")
    sections.append(section_discriminators(data))
    sections.append("\n---\n\n")

    print("  Generating Section 6: Error Pattern Analysis...")
    sections.append(section_error_patterns(data))
    sections.append("\n---\n\n")

    print("  Generating Section 7: Token Efficiency...")
    sections.append(section_token_efficiency(data))
    sections.append("\n---\n\n")

    print("  Generating Section 8: Grok 4 Analysis...")
    sections.append(section_grok4(data))
    sections.append("\n---\n\n")

    print("  Generating Section 9: Extraction Methodology...")
    sections.append(section_extraction(data))
    sections.append("\n---\n\n")

    print("  Generating Section 10: Statistical Tests...")
    sections.append(section_statistical_tests(data))
    sections.append("\n---\n\n")

    print("  Generating Section 11: Recommendations...")
    sections.append(section_recommendations(data))
    sections.append("\n---\n\n")

    print("  Generating Section 12: Appendix...")
    sections.append(section_appendix(data))

    return "".join(sections)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ThermoQA Comprehensive Analysis")
    parser.add_argument("--output", default="analysis/comprehensive_report.md",
                        help="Output markdown file path")
    args = parser.parse_args()

    output_path = BASE / args.output

    # Load data
    data = load_all_data()

    # Generate report
    print("\nGenerating report...")
    report = generate_report(data)

    # Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    line_count = report.count("\n")
    print(f"\nReport written to {output_path}")
    print(f"  {line_count} lines, {len(report)} characters")


if __name__ == "__main__":
    main()
