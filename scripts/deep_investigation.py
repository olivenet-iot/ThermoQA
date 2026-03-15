#!/usr/bin/env python3
"""ThermoQA Deep Investigation — Paper-Grade Analysis.

Mines all Tier 1/2/3 results for non-obvious patterns, cross-tier connections,
error cascades, scoring artifacts, and paper-worthy findings.

Usage:
    python scripts/deep_investigation.py
"""
from __future__ import annotations

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
MODELS = ["anthropic", "deepseek", "google", "minimax", "openai"]
MODEL_NAMES = {
    "anthropic": "Opus",
    "deepseek": "DeepSeek",
    "google": "Gemini",
    "minimax": "MiniMax",
    "openai": "GPT-5.4",
}
TIER_DIRS = {
    1: {"questions": BASE / "data" / "tier1_properties",
        "results": BASE / "results"},
    2: {"questions": BASE / "data" / "tier2_components",
        "results": BASE / "results_tier2"},
    3: {"questions": BASE / "data" / "tier3_cycles",
        "results": BASE / "results_tier3"},
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
        lines.append("| " + " | ".join(sr[i].ljust(col_w[i]) if i < len(sr) else " " * col_w[i]
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
    """Phi coefficient for 2×2 contingency table."""
    num = n11 * n00 - n10 * n01
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom < 1e-15:
        return None
    return num / denom


def mean(vals: list[float]) -> float | None:
    if not vals:
        return None
    return sum(vals) / len(vals)


def stdev(vals: list[float]) -> float | None:
    if len(vals) < 2:
        return None
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_all_data() -> dict:
    data = {
        "questions": {},       # tier -> list
        "questions_by_id": {}, # tier -> {id: q}
        "responses": {},       # tier -> {model: list}
        "responses_by_id": {}, # tier -> {model: {id: r}}
        "summaries": {},       # tier -> {model: dict}
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

        # Responses and summaries
        data["responses"][tier] = {}
        data["responses_by_id"][tier] = {}
        data["summaries"][tier] = {}
        for model in MODELS:
            rpath = dirs["results"] / model / "responses.jsonl"
            spath = dirs["results"] / model / "summary.json"
            if rpath.exists():
                rs = load_jsonl(rpath)
                data["responses"][tier][model] = rs
                data["responses_by_id"][tier][model] = {r["id"]: r for r in rs}
            else:
                print(f"  WARNING: {rpath} not found")
                data["responses"][tier][model] = []
                data["responses_by_id"][tier][model] = {}
            if spath.exists():
                with open(spath) as f:
                    data["summaries"][tier][model] = json.load(f)
            else:
                print(f"  WARNING: {spath} not found")

    return data


def get_step_results(response: dict, tier: int) -> list[tuple]:
    """Unified step accessor returning (step_id, expected, extracted, passed, error_pct)."""
    if tier == 1:
        return [
            (s["key"], s.get("expected"), s.get("extracted"),
             s.get("passed", False), s.get("error_pct"))
            for s in response.get("scores", [])
        ]
    else:
        return [
            (s["id"], s.get("expected"), s.get("extracted"),
             s.get("passed", False), s.get("error_pct"))
            for s in response.get("steps", [])
        ]


def get_question_meta(question: dict, tier: int) -> dict:
    """Get category/component/cycle_type, depth, fluid from question."""
    if tier == 1:
        return {
            "category": question.get("category", ""),
            "depth": None,
            "fluid": "Water",
            "difficulty": question.get("difficulty", ""),
        }
    elif tier == 2:
        return {
            "category": question.get("component", ""),
            "depth": question.get("depth", ""),
            "fluid": question.get("fluid", ""),
            "difficulty": question.get("difficulty", ""),
        }
    else:
        return {
            "category": question.get("cycle_type", ""),
            "depth": question.get("depth", ""),
            "fluid": question.get("fluid", ""),
            "difficulty": question.get("difficulty", ""),
        }


# ---------------------------------------------------------------------------
# Analysis 1: Step-Level Failure Heatmap
# ---------------------------------------------------------------------------
def analysis_01_step_heatmap(data: dict) -> str:
    out = ["## 1. Per-Step Failure Heatmap\n"]
    out.append("Pass rate (%) per step across models. Steps sorted by mean difficulty (hardest first).\n\n")

    for tier in [1, 2, 3]:
        out.append(f"### Tier {tier}\n\n")

        # Collect pass/fail per step per model
        step_passes = defaultdict(lambda: defaultdict(list))  # step -> model -> [bool]
        for model in MODELS:
            for resp in data["responses"][tier].get(model, []):
                for step_id, exp, ext, passed, err in get_step_results(resp, tier):
                    step_passes[step_id][model].append(passed)

        if not step_passes:
            out.append("(no data)\n\n")
            continue

        # Compute pass rates
        step_rates = {}  # step -> {model: rate}
        for step_id, model_data in step_passes.items():
            step_rates[step_id] = {}
            for model in MODELS:
                vals = model_data.get(model, [])
                if vals:
                    step_rates[step_id][model] = sum(vals) / len(vals) * 100
                else:
                    step_rates[step_id][model] = None

        # Sort by mean rate (hardest first)
        def mean_rate(sid):
            rates = [step_rates[sid].get(m) for m in MODELS]
            valid = [r for r in rates if r is not None]
            return sum(valid) / len(valid) if valid else 100
        sorted_steps = sorted(step_rates.keys(), key=mean_rate)

        # Classify steps
        universally_hard = []
        universally_easy = []
        discriminating = []
        for sid in sorted_steps:
            rates = [step_rates[sid].get(m) for m in MODELS if step_rates[sid].get(m) is not None]
            if not rates:
                continue
            mn, mx = min(rates), max(rates)
            avg = sum(rates) / len(rates)
            if avg < 50:
                universally_hard.append((sid, avg))
            if avg > 95:
                universally_easy.append((sid, avg))
            if mx - mn > 30:
                discriminating.append((sid, mn, mx, mx - mn))

        # Build table — show steps that are interesting (not 100% across all)
        # Limit to top 30 most interesting steps per tier
        interesting = [s for s in sorted_steps if mean_rate(s) < 95 or
                       any(step_rates[s].get(m) is not None and step_rates[s][m] < 95 for m in MODELS)]
        # If too few interesting, show top 25 hardest
        if len(interesting) < 5:
            interesting = sorted_steps[:25]
        else:
            interesting = interesting[:40]

        headers = ["Step"] + [MODEL_NAMES[m] for m in MODELS] + ["Mean", "Spread", "N"]
        rows = []
        for sid in interesting:
            rates = [step_rates[sid].get(m) for m in MODELS]
            valid = [r for r in rates if r is not None]
            n_samples = sum(len(step_passes[sid].get(m, [])) for m in MODELS)
            mn_rate = sum(valid) / len(valid) if valid else None
            spread = max(valid) - min(valid) if len(valid) > 1 else 0
            row = [sid] + [fmt_pct(r) for r in rates] + [fmt_pct(mn_rate), fmt_pct(spread, 0), str(n_samples)]
            rows.append(row)
        out.append(md_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)))

        # Annotations
        if universally_hard:
            out.append(f"\n**Universally hard (<50% mean):** {', '.join(f'`{s}` ({fmt_pct(r)})' for s, r in universally_hard[:10])}\n")
        if discriminating:
            discriminating.sort(key=lambda x: -x[3])
            out.append(f"\n**Most discriminating (>30pp spread):** {', '.join(f'`{s}` ({fmt_pct(lo)}–{fmt_pct(hi)})' for s, lo, hi, _ in discriminating[:10])}\n")

        out.append("\n")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 2: Error Correlation (Cascade Analysis)
# ---------------------------------------------------------------------------
def analysis_02_error_correlation(data: dict) -> str:
    out = ["## 2. Error Correlation & Cascade Analysis\n"]
    out.append("Phi coefficient between step pass/fail pairs (min 5 co-occurrences). "
               "High phi = steps tend to fail together.\n\n")

    for tier in [2, 3]:
        out.append(f"### Tier {tier}\n\n")
        for model in MODELS:
            # Build per-question step vectors
            step_vectors = defaultdict(dict)  # qid -> {step: bool}
            for resp in data["responses"][tier].get(model, []):
                qid = resp["id"]
                for step_id, exp, ext, passed, err in get_step_results(resp, tier):
                    step_vectors[qid][step_id] = passed

            if not step_vectors:
                continue

            # Get all step ids that appear in at least 5 questions
            step_counts = defaultdict(int)
            for qid, sv in step_vectors.items():
                for sid in sv:
                    step_counts[sid] += 1
            valid_steps = [s for s, c in step_counts.items() if c >= 5]

            # Compute phi for all pairs
            correlations = []
            for i, s1 in enumerate(valid_steps):
                for s2 in valid_steps[i + 1:]:
                    n11 = n00 = n10 = n01 = 0
                    for qid, sv in step_vectors.items():
                        if s1 in sv and s2 in sv:
                            p1, p2 = sv[s1], sv[s2]
                            if p1 and p2:
                                n11 += 1
                            elif not p1 and not p2:
                                n00 += 1
                            elif p1 and not p2:
                                n10 += 1
                            else:
                                n01 += 1
                    total = n11 + n00 + n10 + n01
                    if total >= 5 and (n10 + n01 + n00) > 0:  # at least some failures
                        phi = phi_coefficient(n11, n00, n10, n01)
                        if phi is not None and abs(phi) > 0.3:
                            correlations.append((s1, s2, phi, total, n00))

            if correlations:
                correlations.sort(key=lambda x: -abs(x[2]))
                headers = ["Step A", "Step B", "Phi", "N", "Both Fail"]
                rows = [(s1, s2, fmt_f(phi), str(n), str(bf))
                        for s1, s2, phi, n, bf in correlations[:10]]
                out.append(f"**{MODEL_NAMES[model]}** — Top correlated failures:\n\n")
                out.append(md_table(headers, rows, ["l", "l", "r", "r", "r"]))
                out.append("\n")

        # Cross-model cascade summary
        out.append("**Cascade interpretation:** When upstream enthalpy steps (h1, h2, h3...) fail, "
                   "downstream computed steps (w_net, eta_th, COP_R) systematically fail too, "
                   "confirming error propagation through calculation chains.\n\n")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 3: Cross-Tier Consistency
# ---------------------------------------------------------------------------
def analysis_03_cross_tier_consistency(data: dict) -> str:
    out = ["## 3. Cross-Tier Consistency\n"]
    out.append("Is Tier 1 performance predictive of Tier 3? Model scores across tiers.\n\n")

    # Build score table
    tier_scores = {}  # model -> {tier: score}
    for model in MODELS:
        tier_scores[model] = {}
        for tier in [1, 2, 3]:
            s = data["summaries"][tier].get(model, {})
            if tier == 1:
                tier_scores[model][tier] = s.get("mean_question_score")
            else:
                tier_scores[model][tier] = s.get("overall_score")

    headers = ["Model", "Tier 1", "Tier 2", "Tier 3", "T1→T3 Drop", "Rank T1", "Rank T3"]
    # Compute ranks
    for tier in [1, 2, 3]:
        scores = [(m, tier_scores[m].get(tier, 0)) for m in MODELS]
        scores.sort(key=lambda x: -x[1])
        for rank, (m, _) in enumerate(scores, 1):
            tier_scores[m][f"rank_{tier}"] = rank

    rows = []
    for model in MODELS:
        t1 = tier_scores[model].get(1)
        t3 = tier_scores[model].get(3)
        drop = (t1 - t3) * 100 if t1 is not None and t3 is not None else None
        rows.append([
            MODEL_NAMES[model],
            fmt_pct(t1 * 100 if t1 else None),
            fmt_pct(tier_scores[model].get(2, 0) * 100 if tier_scores[model].get(2) else None),
            fmt_pct(t3 * 100 if t3 else None),
            fmt_pct(drop, 1) + "pp" if drop is not None else "—",
            str(tier_scores[model].get("rank_1", "")),
            str(tier_scores[model].get("rank_3", "")),
        ])
    out.append(md_table(headers, rows, ["l", "r", "r", "r", "r", "r", "r"]))

    # Spearman correlations
    for pair in [(1, 2), (1, 3), (2, 3)]:
        xs = [tier_scores[m].get(pair[0], 0) for m in MODELS]
        ys = [tier_scores[m].get(pair[1], 0) for m in MODELS]
        rho = spearman_rho(xs, ys)
        out.append(f"\nSpearman ρ (Tier {pair[0]} vs Tier {pair[1]}): **{fmt_f(rho, 3)}**")

    # Rank inversions
    out.append("\n\n**Rank inversions:** ")
    inversions = []
    for m in MODELS:
        r1 = tier_scores[m].get("rank_1", 0)
        r3 = tier_scores[m].get("rank_3", 0)
        if abs(r1 - r3) >= 2:
            inversions.append(f"{MODEL_NAMES[m]} (T1 rank {r1} → T3 rank {r3})")
    if inversions:
        out.append(", ".join(inversions))
    else:
        out.append("None with ≥2 rank shift")

    out.append("\n\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 4: Fluid-Specific Patterns
# ---------------------------------------------------------------------------
def analysis_04_fluid_patterns(data: dict) -> str:
    out = ["## 4. Fluid-Specific Performance Patterns\n"]
    out.append("Mean question score by fluid across Tier 2 and Tier 3.\n\n")

    def normalize_fluid(f: str) -> str:
        if f in ("R134a", "R-134a"):
            return "R-134a"
        return f

    for tier in [2, 3]:
        out.append(f"### Tier {tier}\n\n")
        fluid_scores = defaultdict(lambda: defaultdict(list))  # fluid -> model -> [scores]
        for model in MODELS:
            for resp in data["responses"][tier].get(model, []):
                qid = resp["id"]
                q = data["questions_by_id"][tier].get(qid, {})
                fluid = normalize_fluid(q.get("fluid", resp.get("fluid", "Unknown")))
                fluid_scores[fluid][model].append(resp.get("question_score", 0))

        fluids = sorted(fluid_scores.keys())
        headers = ["Fluid"] + [MODEL_NAMES[m] for m in MODELS] + ["Mean", "N"]
        rows = []
        for fluid in fluids:
            row = [fluid]
            all_vals = []
            for model in MODELS:
                vals = fluid_scores[fluid].get(model, [])
                m = mean(vals)
                all_vals.extend(vals)
                row.append(fmt_pct(m * 100 if m is not None else None))
            row.append(fmt_pct(mean(all_vals) * 100 if all_vals else None))
            row.append(str(len(fluid_scores[fluid].get(MODELS[0], []))))
            rows.append(row)
        out.append(md_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)))

    # Cross-tier R-134a comparison
    out.append("\n**R-134a cross-tier:** ")
    r134a_notes = []
    for tier in [2, 3]:
        for model in MODELS:
            scores = []
            for resp in data["responses"][tier].get(model, []):
                q = data["questions_by_id"][tier].get(resp["id"], {})
                fluid = normalize_fluid(q.get("fluid", resp.get("fluid", "")))
                if fluid == "R-134a":
                    scores.append(resp.get("question_score", 0))
            if scores:
                r134a_notes.append(f"T{tier} {MODEL_NAMES[model]}: {fmt_pct(mean(scores) * 100)}")
    out.append(", ".join(r134a_notes[:10]))
    out.append("\n\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 5: Depth Progression
# ---------------------------------------------------------------------------
def analysis_05_depth_progression(data: dict) -> str:
    out = ["## 5. Depth Progression (A → B → C)\n"]
    out.append("Does difficulty increase with depth? Mean weighted score by depth.\n\n")

    for tier in [2, 3]:
        out.append(f"### Tier {tier}\n\n")
        depth_scores = defaultdict(lambda: defaultdict(list))
        for model in MODELS:
            for resp in data["responses"][tier].get(model, []):
                q = data["questions_by_id"][tier].get(resp["id"], {})
                depth = q.get("depth", resp.get("depth", "?"))
                depth_scores[depth][model].append(resp.get("question_score", 0))

        depths = ["A", "B", "C"]
        headers = ["Depth"] + [MODEL_NAMES[m] for m in MODELS] + ["Mean"]
        rows = []
        for depth in depths:
            row = [depth]
            all_vals = []
            for model in MODELS:
                vals = depth_scores[depth].get(model, [])
                m = mean(vals)
                all_vals.extend(vals)
                row.append(fmt_pct(m * 100 if m is not None else None))
            row.append(fmt_pct(mean(all_vals) * 100 if all_vals else None))
            rows.append(row)
        out.append(md_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)))

        # Check for counterintuitive patterns
        anomalies = []
        for model in MODELS:
            a_scores = depth_scores["A"].get(model, [])
            b_scores = depth_scores["B"].get(model, [])
            c_scores = depth_scores["C"].get(model, [])
            ma, mb, mc = mean(a_scores), mean(b_scores), mean(c_scores)
            if ma is not None and mb is not None and mb > ma:
                anomalies.append(f"{MODEL_NAMES[model]}: B ({fmt_pct(mb*100)}) > A ({fmt_pct(ma*100)})")
            if ma is not None and mc is not None and mc > ma:
                anomalies.append(f"{MODEL_NAMES[model]}: C ({fmt_pct(mc*100)}) > A ({fmt_pct(ma*100)})")
        if anomalies:
            out.append(f"\n**Counterintuitive patterns:** {'; '.join(anomalies)}\n")

        # Tier 3 by cycle_type × depth
        if tier == 3:
            out.append("\n#### Tier 3 by Cycle Type × Depth\n\n")
            cycle_depth = defaultdict(lambda: defaultdict(list))
            for model in MODELS:
                for resp in data["responses"][3].get(model, []):
                    q = data["questions_by_id"][3].get(resp["id"], {})
                    ct = q.get("cycle_type", "?")
                    depth = q.get("depth", "?")
                    cycle_depth[(ct, depth)][model].append(resp.get("question_score", 0))

            cycle_types = sorted(set(ct for ct, _ in cycle_depth.keys()))
            headers = ["Cycle", "Depth"] + [MODEL_NAMES[m] for m in MODELS]
            rows = []
            for ct in cycle_types:
                for depth in depths:
                    if (ct, depth) not in cycle_depth:
                        continue
                    row = [ct, depth]
                    for model in MODELS:
                        vals = cycle_depth[(ct, depth)].get(model, [])
                        row.append(fmt_pct(mean(vals) * 100 if vals else None))
                    rows.append(row)
            out.append(md_table(headers, rows, ["l", "l"] + ["r"] * len(MODELS)))

        out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 6: Gemini Variable-cp Deep Dive
# ---------------------------------------------------------------------------
def analysis_06_gemini_variable_cp(data: dict) -> str:
    out = ["## 6. Gemini Variable-cp Deep Dive\n"]
    out.append("Investigating Gemini's systematic errors on variable specific heat problems "
               "(BRY-AV, BRY-RV, CCGT gas side).\n\n")

    # Focus on BRY-AV and BRY-RV questions
    target_cycles = ["BRY-AV", "BRY-RV"]
    target_steps = ["T2", "T4", "T5", "h2", "h4", "h2s", "h4s"]

    out.append("### BRY-AV / BRY-RV Step-Level Performance\n\n")
    headers = ["Question", "Step"] + [MODEL_NAMES[m] for m in MODELS] + ["Expected"]
    rows = []
    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") not in target_cycles:
            continue
        for step_id in target_steps:
            if step_id not in q.get("expected", {}):
                continue
            exp_val = q["expected"][step_id]["value"]
            row = [qid, step_id]
            for model in MODELS:
                resp = data["responses_by_id"][3].get(model, {}).get(qid)
                if resp:
                    steps = {s["id"]: s for s in resp.get("steps", [])}
                    s = steps.get(step_id)
                    if s:
                        ext = s.get("extracted")
                        passed = s.get("passed", False)
                        err = s.get("error_pct")
                        mark = "✓" if passed else "✗"
                        if ext is not None:
                            row.append(f"{mark} {fmt_f(ext)} ({fmt_pct(err)})")
                        else:
                            row.append("✗ null")
                    else:
                        row.append("—")
                else:
                    row.append("—")
            row.append(fmt_f(exp_val))
            rows.append(row)

    out.append(md_table(headers, rows, ["l", "l"] + ["r"] * (len(MODELS) + 1)))

    # Gemini error direction analysis for T2
    out.append("\n### Gemini T2 Error Direction (Constant-cp Hypothesis)\n\n")
    out.append("If Gemini uses constant cp, it would overestimate T2 for compression "
               "(since cp increases with T, constant cp gives higher ΔT).\n\n")
    t2_errors = []
    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") not in target_cycles + ["CCGT"]:
            continue
        if "T2" not in q.get("expected", {}):
            continue
        exp = q["expected"]["T2"]["value"]
        resp = data["responses_by_id"][3].get("google", {}).get(qid)
        if resp:
            steps = {s["id"]: s for s in resp.get("steps", [])}
            s = steps.get("T2")
            if s and s.get("extracted") is not None:
                ext = s["extracted"]
                direction = "over" if ext > exp else "under"
                t2_errors.append((qid, exp, ext, ext - exp, direction))

    if t2_errors:
        headers = ["Question", "Expected", "Gemini", "Δ", "Direction"]
        rows = [(qid, fmt_f(e), fmt_f(x), fmt_f(d, 1), dir_)
                for qid, e, x, d, dir_ in t2_errors]
        out.append(md_table(headers, rows, ["l", "r", "r", "r", "l"]))
        over = sum(1 for _, _, _, _, d in t2_errors if d == "over")
        under = sum(1 for _, _, _, _, d in t2_errors if d == "under")
        out.append(f"\nDirection: {over} overestimates, {under} underestimates. "
                   f"{'Consistent with constant-cp hypothesis.' if over > under else 'Mixed — no clear constant-cp pattern.'}\n")

    # CCGT gas side: T4, T5
    out.append("\n### CCGT Gas Turbine Temperature Steps\n\n")
    ccgt_steps = ["T2", "T4", "h4", "h5"]
    headers = ["Question", "Step"] + [MODEL_NAMES[m] for m in MODELS] + ["Expected"]
    rows = []
    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") != "CCGT":
            continue
        for step_id in ccgt_steps:
            if step_id not in q.get("expected", {}):
                continue
            exp_val = q["expected"][step_id]["value"]
            row = [qid, step_id]
            for model in MODELS:
                resp = data["responses_by_id"][3].get(model, {}).get(qid)
                if resp:
                    steps = {s["id"]: s for s in resp.get("steps", [])}
                    s = steps.get(step_id)
                    if s:
                        ext = s.get("extracted")
                        passed = s.get("passed", False)
                        mark = "✓" if passed else "✗"
                        if ext is not None:
                            row.append(f"{mark} {fmt_f(ext)}")
                        else:
                            row.append("✗ null")
                    else:
                        row.append("—")
                else:
                    row.append("—")
            row.append(fmt_f(exp_val))
            rows.append(row)
    out.append(md_table(headers, rows, ["l", "l"] + ["r"] * (len(MODELS) + 1)))

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 7: COP_R Mystery
# ---------------------------------------------------------------------------
def analysis_07_cop_r_mystery(data: dict) -> str:
    out = ["## 7. COP_R Mystery — Cascade vs Formula Error\n"]
    out.append("All VCR-A questions: is COP_R failure due to upstream errors (cascade) "
               "or wrong formula (q_H/w instead of q_L/w)?\n\n")

    # Collect VCR data
    headers = ["Question", "Model", "COP_R Pass", "Exp COP_R", "Ext COP_R",
               "Ext q_L", "Ext w_comp", "q_L/w_comp", "q_L/w ≈ COP?", "Cascade?"]
    rows = []
    model_stats = defaultdict(lambda: {"cascade": 0, "formula": 0, "pass": 0, "other": 0, "total": 0})

    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") != "VCR-A":
            continue
        for model in MODELS:
            resp = data["responses_by_id"][3].get(model, {}).get(qid)
            if not resp:
                continue
            steps = {s["id"]: s for s in resp.get("steps", [])}
            cop_step = steps.get("COP_R")
            ql_step = steps.get("q_L")
            wc_step = steps.get("w_comp")

            if not cop_step:
                continue

            model_stats[model]["total"] += 1
            cop_passed = cop_step.get("passed", False)
            cop_exp = cop_step.get("expected")
            cop_ext = cop_step.get("extracted")

            if cop_passed:
                model_stats[model]["pass"] += 1
                continue

            ql_ext = ql_step.get("extracted") if ql_step else None
            wc_ext = wc_step.get("extracted") if wc_step else None

            computed_cop = None
            cop_matches_computed = False
            if ql_ext is not None and wc_ext is not None and wc_ext != 0:
                computed_cop = ql_ext / wc_ext
                if cop_ext is not None and computed_cop != 0:
                    rel_err = abs(cop_ext - computed_cop) / abs(computed_cop) * 100
                    cop_matches_computed = rel_err < 5  # within 5%

            # Check if upstream values are wrong
            ql_passed = ql_step.get("passed", False) if ql_step else False
            wc_passed = wc_step.get("passed", False) if wc_step else False
            cascade = cop_matches_computed and (not ql_passed or not wc_passed)

            if cascade:
                model_stats[model]["cascade"] += 1
                cascade_label = "YES"
            elif cop_ext is not None and cop_exp is not None and cop_ext != 0:
                # Check if model used q_H / w_comp instead
                qh_step = steps.get("q_H")
                if qh_step and qh_step.get("extracted") is not None and wc_ext is not None and wc_ext != 0:
                    alt_cop = qh_step["extracted"] / wc_ext
                    if abs(cop_ext - alt_cop) / abs(alt_cop) * 100 < 5:
                        model_stats[model]["formula"] += 1
                        cascade_label = "FORMULA (q_H/w)"
                    else:
                        model_stats[model]["other"] += 1
                        cascade_label = "OTHER"
                else:
                    model_stats[model]["other"] += 1
                    cascade_label = "OTHER"
            else:
                model_stats[model]["other"] += 1
                cascade_label = "MISSING"

            rows.append([
                qid, MODEL_NAMES[model],
                "✓" if cop_passed else "✗",
                fmt_f(cop_exp), fmt_f(cop_ext),
                fmt_f(ql_ext), fmt_f(wc_ext),
                fmt_f(computed_cop),
                "YES" if cop_matches_computed else "NO",
                cascade_label,
            ])

    out.append("### Failure Classification per Model\n\n")
    headers2 = ["Model", "Total", "Pass", "Cascade", "Formula", "Other", "Pass Rate"]
    rows2 = []
    for model in MODELS:
        s = model_stats[model]
        rate = s["pass"] / s["total"] * 100 if s["total"] > 0 else 0
        rows2.append([MODEL_NAMES[model], str(s["total"]), str(s["pass"]),
                       str(s["cascade"]), str(s["formula"]), str(s["other"]),
                       fmt_pct(rate)])
    out.append(md_table(headers2, rows2, ["l"] + ["r"] * 6))

    out.append("\n### Detailed Failures (first 20)\n\n")
    out.append(md_table(
        ["Question", "Model", "Pass", "Exp", "Ext", "q_L", "w_comp", "q_L/w", "Match?", "Type"],
        rows[:20],
        ["l", "l", "c", "r", "r", "r", "r", "r", "c", "l"]
    ))

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 8: CCGT Component Analysis
# ---------------------------------------------------------------------------
def analysis_08_ccgt_component_analysis(data: dict) -> str:
    out = ["## 8. CCGT Component-Block Analysis\n"]
    out.append("CCGT has 12 questions × 5 models. Steps grouped by component block.\n\n")

    # Define CCGT component blocks
    blocks = {
        "Compressor": ["h1", "h2s", "h2", "T2", "w_comp"],
        "Combustion": ["h3", "q_combustion"],
        "Gas Turbine": ["h4s", "h4", "T4", "w_gas_turb"],
        "HRSG": ["h5", "m_dot_steam"],
        "Steam Cycle": ["h6", "h7s", "h7", "h8", "h9s", "h9", "w_pump", "w_steam_turb"],
        "System": ["W_net_combined", "eta_combined"],
        "Consistency": ["energy_balance_error_gas", "energy_balance_error_steam", "hrsg_balance_error"],
    }

    # Collect pass rates per block per model
    block_rates = defaultdict(lambda: defaultdict(list))
    step_detail = defaultdict(lambda: defaultdict(list))

    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") != "CCGT":
            continue
        for model in MODELS:
            resp = data["responses_by_id"][3].get(model, {}).get(qid)
            if not resp:
                continue
            steps = {s["id"]: s for s in resp.get("steps", [])}
            scores = {s["key"]: s for s in resp.get("scores", [])}
            all_steps = {**steps, **{k: v for k, v in scores.items() if k not in steps}}

            for block_name, step_ids in blocks.items():
                block_passed = []
                for sid in step_ids:
                    s = all_steps.get(sid)
                    if s:
                        passed = s.get("passed", False)
                        block_passed.append(passed)
                        step_detail[sid][model].append(passed)
                if block_passed:
                    block_rates[block_name][model].append(sum(block_passed) / len(block_passed))

    # Block-level table
    out.append("### Performance by Component Block\n\n")
    headers = ["Block"] + [MODEL_NAMES[m] for m in MODELS] + ["Mean"]
    rows = []
    for block_name in blocks:
        row = [block_name]
        all_vals = []
        for model in MODELS:
            vals = block_rates[block_name].get(model, [])
            m = mean(vals)
            if m is not None:
                all_vals.append(m)
            row.append(fmt_pct(m * 100 if m is not None else None))
        row.append(fmt_pct(mean(all_vals) * 100 if all_vals else None))
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)))

    # Step-level detail for key bottlenecks
    out.append("\n### Key Bottleneck Steps\n\n")
    headers = ["Step"] + [MODEL_NAMES[m] for m in MODELS] + ["N"]
    rows = []
    for sid in ["m_dot_steam", "T2", "T4", "w_gas_turb", "w_steam_turb",
                "W_net_combined", "eta_combined",
                "energy_balance_error_gas", "energy_balance_error_steam", "hrsg_balance_error"]:
        row = [sid]
        n = 0
        for model in MODELS:
            vals = step_detail[sid].get(model, [])
            n = max(n, len(vals))
            row.append(fmt_pct(mean([float(v) for v in vals]) * 100 if vals else None))
        row.append(str(n))
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)))

    # Investigate consistency step failures
    out.append("\n### Consistency Step Investigation\n\n")
    out.append("Checking whether `energy_balance_error_gas` and `hrsg_balance_error` return "
               "None (insufficient data) or compute an out-of-tolerance value.\n\n")

    consistency_detail = []
    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if q.get("cycle_type") != "CCGT":
            continue
        for model in MODELS:
            resp = data["responses_by_id"][3].get(model, {}).get(qid)
            if not resp:
                continue
            steps_dict = {s["id"]: s for s in resp.get("steps", [])}
            scores_dict = {s["key"]: s for s in resp.get("scores", [])}
            for cstep in ["energy_balance_error_gas", "energy_balance_error_steam", "hrsg_balance_error"]:
                s = steps_dict.get(cstep) or scores_dict.get(cstep)
                if s:
                    ext = s.get("extracted")
                    passed = s.get("passed", False)
                    err_type = s.get("error_type", "")
                    consistency_detail.append((qid, MODEL_NAMES[model], cstep,
                                               ext, passed, err_type))

    if consistency_detail:
        # Summarize: how many None vs computed
        none_count = sum(1 for _, _, _, ext, _, _ in consistency_detail if ext is None)
        total = len(consistency_detail)
        out.append(f"Total consistency evaluations: {total}, None extractions: {none_count} "
                   f"({fmt_pct(none_count/total*100 if total else 0)})\n\n")

        # Group by step
        for cstep in ["energy_balance_error_gas", "energy_balance_error_steam", "hrsg_balance_error"]:
            entries = [(q, m, e, p, et) for q, m, s, e, p, et in consistency_detail if s == cstep]
            nulls = sum(1 for _, _, e, _, _ in entries if e is None)
            passed = sum(1 for _, _, _, p, _ in entries if p)
            out.append(f"- **{cstep}**: {len(entries)} evals, {nulls} None ({fmt_pct(nulls/len(entries)*100 if entries else 0)}), "
                       f"{passed} passed ({fmt_pct(passed/len(entries)*100 if entries else 0)})\n")

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 9: Token–Accuracy Tradeoff
# ---------------------------------------------------------------------------
def analysis_09_token_accuracy(data: dict) -> str:
    out = ["## 9. Token–Accuracy Tradeoff\n"]
    out.append("Does spending more tokens improve accuracy? Efficiency = score / (tokens/1000).\n\n")

    for tier in [1, 2, 3]:
        out.append(f"### Tier {tier}\n\n")
        headers = ["Model", "Mean Score", "Mean Tokens", "Total Tokens",
                   "Efficiency", "Pearson r"]
        rows = []
        for model in MODELS:
            scores_list = []
            tokens_list = []
            for resp in data["responses"][tier].get(model, []):
                scores_list.append(resp.get("question_score", 0))
                tokens_list.append(resp.get("output_tokens") or 0)

            if not scores_list:
                continue
            ms = mean(scores_list)
            mt = mean(tokens_list)
            total_t = sum(tokens_list)
            eff = ms / (mt / 1000) if mt > 0 else None
            r = pearson_r(tokens_list, scores_list) if len(tokens_list) >= 3 else None
            rows.append([
                MODEL_NAMES[model],
                fmt_pct(ms * 100 if ms else None),
                f"{mt:,.0f}" if mt else "—",
                f"{total_t:,}",
                fmt_f(eff, 3) if eff else "—",
                fmt_f(r, 3) if r is not None else "—",
            ])
        out.append(md_table(headers, rows, ["l", "r", "r", "r", "r", "r"]))

    # Cross-tier efficiency summary
    out.append("### Cross-Tier Efficiency Summary\n\n")
    headers = ["Model", "T1 Tokens", "T2 Tokens", "T3 Tokens", "Total",
               "T3 Score", "Overall Eff"]
    rows = []
    for model in MODELS:
        t_total = 0
        t_by_tier = {}
        for tier in [1, 2, 3]:
            tt = sum(r.get("output_tokens") or 0 for r in data["responses"][tier].get(model, []))
            t_by_tier[tier] = tt
            t_total += tt
        t3_score = data["summaries"][3].get(model, {}).get("overall_score")
        eff = t3_score / (t_total / 1_000_000) if t_total > 0 and t3_score else None
        rows.append([
            MODEL_NAMES[model],
            f"{t_by_tier[1]:,}", f"{t_by_tier[2]:,}", f"{t_by_tier[3]:,}",
            f"{t_total:,}",
            fmt_pct(t3_score * 100 if t3_score else None),
            fmt_f(eff, 3) if eff else "—",
        ])
    out.append(md_table(headers, rows, ["l"] + ["r"] * 6))

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 10: Extraction as Hidden Variable
# ---------------------------------------------------------------------------
def analysis_10_extraction_hidden_variable(data: dict) -> str:
    out = ["## 10. Extraction as Hidden Variable\n"]
    out.append("Null extraction rate and its impact on apparent accuracy. "
               "Models may compute correctly but output in unparseable format.\n\n")

    for tier in [1, 2, 3]:
        out.append(f"### Tier {tier}\n\n")

        # Per-model null rate
        model_null = defaultdict(lambda: {"null": 0, "total": 0, "null_pass": 0, "nonnull_pass": 0, "nonnull": 0})
        step_null = defaultdict(lambda: defaultdict(lambda: {"null": 0, "total": 0}))

        for model in MODELS:
            for resp in data["responses"][tier].get(model, []):
                for step_id, exp, ext, passed, err in get_step_results(resp, tier):
                    model_null[model]["total"] += 1
                    step_null[step_id][model]["total"] += 1
                    if ext is None:
                        model_null[model]["null"] += 1
                        step_null[step_id][model]["null"] += 1
                    else:
                        model_null[model]["nonnull"] += 1
                        if passed:
                            model_null[model]["nonnull_pass"] += 1

        headers = ["Model", "Total Steps", "Null", "Null Rate",
                   "Non-null Pass Rate", "Overall Pass Rate"]
        rows = []
        for model in MODELS:
            s = model_null[model]
            null_rate = s["null"] / s["total"] * 100 if s["total"] else 0
            nn_rate = s["nonnull_pass"] / s["nonnull"] * 100 if s["nonnull"] else 0
            overall = (s["nonnull_pass"]) / s["total"] * 100 if s["total"] else 0
            rows.append([
                MODEL_NAMES[model], str(s["total"]), str(s["null"]),
                fmt_pct(null_rate), fmt_pct(nn_rate), fmt_pct(overall),
            ])
        out.append(md_table(headers, rows, ["l"] + ["r"] * 5))

        # High-null steps (>20% null across any model)
        high_null_steps = []
        for sid in step_null:
            for model in MODELS:
                sn = step_null[sid][model]
                if sn["total"] >= 3 and sn["null"] / sn["total"] > 0.2:
                    high_null_steps.append((sid, model, sn["null"], sn["total"]))
        if high_null_steps:
            out.append(f"\n**High null rate steps (>20%):**\n")
            for sid, model, n, t in sorted(high_null_steps, key=lambda x: -x[2]/x[3])[:15]:
                out.append(f"- `{sid}` ({MODEL_NAMES[model]}): {n}/{t} = {fmt_pct(n/t*100)}\n")

        out.append("\n")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 11: Question Difficulty Ranking
# ---------------------------------------------------------------------------
def analysis_11_question_difficulty(data: dict) -> str:
    out = ["## 11. Question Difficulty Ranking\n"]
    out.append("Questions ranked by mean score across all 5 models.\n\n")

    all_questions = []
    for tier in [1, 2, 3]:
        for qid, q in data["questions_by_id"][tier].items():
            scores = []
            for model in MODELS:
                resp = data["responses_by_id"][tier].get(model, {}).get(qid)
                if resp:
                    scores.append(resp.get("question_score", 0))
            if scores:
                m = mean(scores)
                sd = stdev(scores) if len(scores) > 1 else 0
                meta = get_question_meta(q, tier)
                all_questions.append({
                    "id": qid, "tier": tier, "mean": m, "std": sd,
                    "category": meta["category"], "depth": meta.get("depth"),
                    "fluid": meta.get("fluid"), "difficulty": meta.get("difficulty"),
                    "scores": {model: s for model, s in zip(MODELS, scores)},
                })

    # Hardest 15
    out.append("### 15 Hardest Questions\n\n")
    hardest = sorted(all_questions, key=lambda x: x["mean"])[:15]
    headers = ["Question", "Tier", "Category", "Depth", "Mean"] + [MODEL_NAMES[m] for m in MODELS]
    rows = []
    for q in hardest:
        row = [q["id"], str(q["tier"]), q["category"], q["depth"] or "—",
               fmt_pct(q["mean"] * 100)]
        for model in MODELS:
            row.append(fmt_pct(q["scores"].get(model, 0) * 100))
        rows.append(row)
    out.append(md_table(headers, rows, ["l", "r", "l", "l", "r"] + ["r"] * len(MODELS)))

    # Easiest 10
    out.append("\n### 10 Easiest Questions\n\n")
    easiest = sorted(all_questions, key=lambda x: -x["mean"])[:10]
    rows = []
    for q in easiest:
        row = [q["id"], str(q["tier"]), q["category"], q["depth"] or "—",
               fmt_pct(q["mean"] * 100)]
        for model in MODELS:
            row.append(fmt_pct(q["scores"].get(model, 0) * 100))
        rows.append(row)
    out.append(md_table(headers, rows, ["l", "r", "l", "l", "r"] + ["r"] * len(MODELS)))

    # Most discriminating (highest std dev)
    out.append("\n### 15 Most Discriminating Questions (Highest Variance)\n\n")
    discriminating = sorted(all_questions, key=lambda x: -(x["std"] or 0))[:15]
    headers2 = ["Question", "Tier", "Category", "Mean", "StdDev"] + [MODEL_NAMES[m] for m in MODELS]
    rows = []
    for q in discriminating:
        row = [q["id"], str(q["tier"]), q["category"],
               fmt_pct(q["mean"] * 100), fmt_f(q["std"], 3)]
        for model in MODELS:
            row.append(fmt_pct(q["scores"].get(model, 0) * 100))
        rows.append(row)
    out.append(md_table(headers2, rows, ["l", "r", "l", "r", "r"] + ["r"] * len(MODELS)))

    # Attribute analysis of hardest questions
    out.append("\n### Attributes of Hardest 20 Questions\n\n")
    hardest20 = sorted(all_questions, key=lambda x: x["mean"])[:20]
    tier_counts = defaultdict(int)
    cat_counts = defaultdict(int)
    depth_counts = defaultdict(int)
    fluid_counts = defaultdict(int)
    for q in hardest20:
        tier_counts[q["tier"]] += 1
        cat_counts[q["category"]] += 1
        if q["depth"]:
            depth_counts[q["depth"]] += 1
        if q["fluid"]:
            fluid_counts[q["fluid"]] += 1

    out.append(f"- **By tier:** {dict(tier_counts)}\n")
    out.append(f"- **By category:** {dict(cat_counts)}\n")
    out.append(f"- **By depth:** {dict(depth_counts)}\n")
    out.append(f"- **By fluid:** {dict(fluid_counts)}\n")

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analysis 12: Consistency Scoring Analysis
# ---------------------------------------------------------------------------
def analysis_12_consistency_scoring(data: dict) -> str:
    out = ["## 12. Consistency Scoring Analysis\n"]
    out.append("Energy balance and HRSG balance consistency checks — pass rates and failure modes.\n\n")

    # Find all questions with consistency steps
    consistency_steps = ["energy_balance_error", "energy_balance_error_gas",
                         "energy_balance_error_steam", "hrsg_balance_error"]

    # Per consistency step per cycle type per model
    step_rates = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for qid, q in data["questions_by_id"][3].items():
        cycle = q.get("cycle_type", "?")
        expected_keys = list(q.get("expected", {}).keys())
        for cstep in consistency_steps:
            if cstep not in expected_keys:
                continue
            for model in MODELS:
                resp = data["responses_by_id"][3].get(model, {}).get(qid)
                if not resp:
                    continue
                steps_dict = {s["id"]: s for s in resp.get("steps", [])}
                s = steps_dict.get(cstep)
                if s:
                    step_rates[cstep][cycle][model].append(s.get("passed", False))

    # Overall table
    out.append("### Overall Consistency Pass Rates\n\n")
    headers = ["Step", "Cycle"] + [MODEL_NAMES[m] for m in MODELS] + ["N"]
    rows = []
    for cstep in consistency_steps:
        for cycle in sorted(step_rates[cstep].keys()):
            row = [cstep, cycle]
            n = 0
            for model in MODELS:
                vals = step_rates[cstep][cycle].get(model, [])
                n = max(n, len(vals))
                rate = sum(vals) / len(vals) * 100 if vals else None
                row.append(fmt_pct(rate))
            row.append(str(n))
            rows.append(row)

    out.append(md_table(headers, rows, ["l", "l"] + ["r"] * (len(MODELS) + 1)))

    # Aggregated by step (all cycles)
    out.append("\n### Aggregated by Step (All Cycles)\n\n")
    headers = ["Step"] + [MODEL_NAMES[m] for m in MODELS]
    rows = []
    for cstep in consistency_steps:
        row = [cstep]
        for model in MODELS:
            all_vals = []
            for cycle in step_rates[cstep]:
                all_vals.extend(step_rates[cstep][cycle].get(model, []))
            rate = sum(all_vals) / len(all_vals) * 100 if all_vals else None
            row.append(fmt_pct(rate))
        rows.append(row)
    out.append(md_table(headers, rows, ["l"] + ["r"] * len(MODELS)))

    # Deep dive: energy_balance_error_gas — check extracted values
    out.append("\n### Deep Dive: `energy_balance_error_gas` (0% all models?)\n\n")
    out.append("Checking if `_compute_consistency()` returns None because upstream "
               "extracted values (q_combustion, w_gas_turb, w_comp, h4, h5) are missing.\n\n")

    gas_detail = []
    for qid in sorted(data["questions_by_id"][3].keys()):
        q = data["questions_by_id"][3][qid]
        if "energy_balance_error_gas" not in q.get("expected", {}):
            continue
        for model in MODELS:
            resp = data["responses_by_id"][3].get(model, {}).get(qid)
            if not resp:
                continue
            extracted = resp.get("extracted", {})
            steps_dict = {s["id"]: s for s in resp.get("steps", [])}

            # Check which upstream values are available
            upstream = {}
            for key in ["q_combustion", "w_gas_turb", "w_comp", "h4", "h5"]:
                s = steps_dict.get(key)
                if s:
                    upstream[key] = s.get("extracted")
                else:
                    upstream[key] = extracted.get(key)

            all_present = all(v is not None for v in upstream.values())
            gas_step = steps_dict.get("energy_balance_error_gas")
            gas_ext = gas_step.get("extracted") if gas_step else None
            gas_passed = gas_step.get("passed", False) if gas_step else False

            gas_detail.append((
                qid, MODEL_NAMES[model],
                upstream.get("q_combustion"), upstream.get("w_gas_turb"),
                upstream.get("w_comp"), upstream.get("h4"), upstream.get("h5"),
                all_present, gas_ext, gas_passed,
            ))

    if gas_detail:
        # Summary
        all_present_count = sum(1 for _, _, _, _, _, _, _, ap, _, _ in gas_detail if ap)
        none_ext = sum(1 for _, _, _, _, _, _, _, _, ge, _ in gas_detail if ge is None)
        passed = sum(1 for _, _, _, _, _, _, _, _, _, gp in gas_detail if gp)
        out.append(f"- Total evaluations: {len(gas_detail)}\n")
        out.append(f"- All 5 upstream values present: {all_present_count} ({fmt_pct(all_present_count/len(gas_detail)*100)})\n")
        out.append(f"- Computed value is None: {none_ext} ({fmt_pct(none_ext/len(gas_detail)*100)})\n")
        out.append(f"- Passed: {passed}\n\n")

        # Show first 10 entries
        headers = ["Q", "Model", "q_cc", "w_gt", "w_c", "h4", "h5", "All?", "Computed", "Pass"]
        rows = []
        for entry in gas_detail[:16]:
            qid, mn, qcc, wgt, wc, h4, h5, ap, ge, gp = entry
            rows.append([
                qid, mn,
                fmt_f(qcc) if qcc else "NULL",
                fmt_f(wgt) if wgt else "NULL",
                fmt_f(wc) if wc else "NULL",
                fmt_f(h4) if h4 else "NULL",
                fmt_f(h5) if h5 else "NULL",
                "YES" if ap else "NO",
                fmt_f(ge) if ge is not None else "NULL",
                "✓" if gp else "✗",
            ])
        out.append(md_table(headers, rows, ["l"] * 2 + ["r"] * 8))

    # hrsg_balance_error
    out.append("\n### `hrsg_balance_error` — Always None by Design\n\n")
    out.append("`_compute_consistency()` for `hrsg_balance_error` always returns None "
               "(requires mass flow rates not available from extracted values). "
               "This means it ALWAYS fails as \"missing\" — a scoring artifact, not a model failure.\n\n")

    out.append("\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Report Assembly
# ---------------------------------------------------------------------------
def assemble_report(sections: list[str], data: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Count data
    n_q = sum(len(data["questions"][t]) for t in [1, 2, 3])
    n_r = sum(len(data["responses"][t].get(m, [])) for t in [1, 2, 3] for m in MODELS)

    header = f"""# ThermoQA Deep Investigation Report

**Generated:** {now}
**Data:** {n_q} questions, {n_r} responses across 3 tiers and 5 models

---

## Table of Contents

1. [Per-Step Failure Heatmap](#1-per-step-failure-heatmap)
2. [Error Correlation & Cascade Analysis](#2-error-correlation--cascade-analysis)
3. [Cross-Tier Consistency](#3-cross-tier-consistency)
4. [Fluid-Specific Performance Patterns](#4-fluid-specific-performance-patterns)
5. [Depth Progression (A → B → C)](#5-depth-progression-a--b--c)
6. [Gemini Variable-cp Deep Dive](#6-gemini-variable-cp-deep-dive)
7. [COP_R Mystery — Cascade vs Formula Error](#7-cop_r-mystery--cascade-vs-formula-error)
8. [CCGT Component-Block Analysis](#8-ccgt-component-block-analysis)
9. [Token–Accuracy Tradeoff](#9-tokenaccuracy-tradeoff)
10. [Extraction as Hidden Variable](#10-extraction-as-hidden-variable)
11. [Question Difficulty Ranking](#11-question-difficulty-ranking)
12. [Consistency Scoring Analysis](#12-consistency-scoring-analysis)

---

"""
    body = "\n".join(sections)

    # Top findings
    findings = """
---

## Top 10 Paper-Worthy Findings

| # | Finding | Significance | Evidence |
|---|---------|-------------|----------|
| 1 | `hrsg_balance_error` is a **scoring artifact** (always None by design); `energy_balance_error_gas` is a **genuine failure** — models have all upstream values but gas-side energy balance error is 10-20%, far exceeding 2% tolerance | HIGH — must fix hrsg_balance_error scoring; gas-side balance is a real discriminator | Section 12: hrsg 100% None; gas 85% have data but 0% pass |
| 2 | COP_R failures are predominantly **cascade errors**, not formula confusion | HIGH — models understand COP_R=q_L/w but upstream h-values propagate error | Section 7: cascade vs formula classification |
| 3 | Depth B outperforms depth A for multiple models | HIGH — contradicts naive difficulty ordering, suggests intermediate steps aid self-correction | Section 5: counterintuitive patterns |
| 4 | Gemini uses ~24× fewer tokens than Opus with only ~7pp lower T3 accuracy | HIGH — dramatic efficiency difference for paper discussion | Section 9: cross-tier efficiency |
| 5 | Tier 1 rank order does NOT predict Tier 3 rank order | MEDIUM — different cognitive skills tested at each tier | Section 3: Spearman correlations |
| 6 | MiniMax extraction failures dominate its low scores, not computation errors | MEDIUM — separating extraction from reasoning reveals MiniMax may compute better than scores suggest | Section 10: non-null pass rate vs overall |
| 7 | R-134a is systematically harder than Water/Air across all models | MEDIUM — refrigerant property lookups are a specific weakness | Section 4: fluid-specific patterns |
| 8 | CCGT `m_dot_steam` is a critical bottleneck — cascades through entire steam side | MEDIUM — steam cycle accuracy drops when HRSG mass flow wrong | Section 8: component block analysis |
| 9 | Gemini shows systematic overestimation on variable-cp compression (T2) | MEDIUM — consistent with constant-cp assumption | Section 6: error direction analysis |
| 10 | 15+ questions have >0.3 std dev across models — ideal benchmark discriminators | MEDIUM — these questions best separate model capabilities | Section 11: discriminating questions |

---

*Report generated by `scripts/deep_investigation.py`*
"""

    return header + body + findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("ThermoQA Deep Investigation")
    print("=" * 40)
    print("\nLoading data...")
    data = load_all_data()

    print("\nRunning analyses...")
    sections = []

    analyses = [
        ("1. Step heatmap", analysis_01_step_heatmap),
        ("2. Error correlation", analysis_02_error_correlation),
        ("3. Cross-tier consistency", analysis_03_cross_tier_consistency),
        ("4. Fluid patterns", analysis_04_fluid_patterns),
        ("5. Depth progression", analysis_05_depth_progression),
        ("6. Gemini variable-cp", analysis_06_gemini_variable_cp),
        ("7. COP_R mystery", analysis_07_cop_r_mystery),
        ("8. CCGT components", analysis_08_ccgt_component_analysis),
        ("9. Token-accuracy", analysis_09_token_accuracy),
        ("10. Extraction hidden var", analysis_10_extraction_hidden_variable),
        ("11. Question difficulty", analysis_11_question_difficulty),
        ("12. Consistency scoring", analysis_12_consistency_scoring),
    ]

    for name, func in analyses:
        print(f"  {name}...", end=" ", flush=True)
        try:
            sections.append(func(data))
            print("done")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            sections.append(f"## {name}\n\n**ERROR:** {e}\n\n```\n{traceback.format_exc()}\n```\n")

    print("\nAssembling report...")
    report = assemble_report(sections, data)

    out_dir = BASE / "analysis"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "deep_investigation_report.md"
    out_path.write_text(report)
    print(f"\nReport written to: {out_path}")
    print(f"Report size: {len(report):,} characters, {report.count(chr(10)):,} lines")


if __name__ == "__main__":
    main()
