# ThermoQA — Project Handoff Document
## A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models
### Initiated 6 March 2026 · Updated 15 March 2026 (Session 5)

---

## One-Line Summary
ThermoQA is a comprehensive benchmark to evaluate LLM performance on engineering thermodynamics — from steam table lookups to multi-step exergy analysis and full cycle calculations. **v0.3 is published** with 293 questions (Tier 1 + Tier 2 + Tier 3), 3 tiers, 10 cycle types, 5 model evaluations on HuggingFace and GitHub.

---

## Who Is This For
This document is a **continuation prompt** for Claude. It contains all context needed to continue development of ThermoQA without re-explaining decisions already made.

**Owner:** Kemal Düzkar, chemical engineer / founder of Olivenet (KKTC). Built EntropyHunter v0.4 (92.7% adjusted accuracy, fine-tuned Qwen3-8B for exergy analysis, published on HuggingFace). Background: thermodynamics, heat transfer, IoT, MES (Accenture/Novartis/Takeda). Not a programmer — an engineer who measures physical reality. Thesis: magnetic nanoparticles/hyperthermia. First IoT project: heat exchanger efficiency via Arduino.

**Previous project:** EntropyHunter — the world's first open-source fine-tuned model for second-law thermodynamic (exergy) analysis. Search past chats for full history: v0.1 through v0.4, taxonomy design, data generation, training, benchmarking, HuggingFace release.

**Relationship to EntropyHunter:** ThermoQA is the natural evolution. EntropyHunter is a model — ThermoQA is the standard by which all models (including EntropyHunter) will be measured.

**Repository:** `github.com/olivenet-iot/ThermoQA`
**HuggingFace:** `huggingface.co/datasets/olivenet/thermoqa` (three configs: tier1_properties, tier2_components, tier3_cycles)
**HuggingFace (legacy):** `huggingface.co/datasets/olivenet/thermoqa-v0.1` (Tier 1 only, kept for backward compat)
**Development environment:** Claude Code on Ubuntu, `~/ThermoQA/`
**EntropyHunter taxonomy reference:** `~/entropy-hunter/taxonomy/`

---

## Current Status: Phase 3 — COMPLETE ✅

### v0.3 Published (13 March 2026)

**Three tiers complete. 293 questions total (110 + 101 + 82). 10 cycle types. 4-layer difficulty. 5 models evaluated. LLM extraction applied. HuggingFace published.**

### Final Leaderboard — Tier 1: Property Lookups (110 questions)

| Rank | Model | Provider | Score | Supercritical | Extraction |
|------|-------|----------|-------|---------------|------------|
| 🥇 | Gemini 3.1 Pro | Google | **97.3%** | 76.7% | LLM ✅ |
| 🥈 | GPT-5.4 | OpenAI | **96.9%** | 86.7% | LLM ✅ |
| 🥉 | Claude Opus 4.6 | Anthropic | **95.6%** | 48.3% | LLM ✅ |
| 4 | DeepSeek-R1 | DeepSeek | **89.5%** | 48.3% | Regex (LLM had regression) |
| 5 | MiniMax M2.5 | MiniMax | **84.5%** | 43.3% | LLM ✅ |

### Final Leaderboard — Tier 2: Component Analysis (101 questions, LLM re-extracted)

| Rank | Model | Provider | Score | Water | Air | R-134a | Depth A | Depth B | Depth C | Tok/Q |
|------|-------|----------|-------|-------|-----|--------|---------|---------|---------|-------|
| 🥇 | Claude Opus 4.6 | Anthropic | **92.0%** | 96.5% | 95.6% | 53.0% | 90.2% | 91.5% | 94.8% | 30,371 |
| 🥈 | GPT-5.4 | OpenAI | **91.0%** | 95.2% | 95.8% | 52.0% | 89.8% | 89.2% | 94.7% | 8,986 |
| 🥉 | Gemini 3.1 Pro | Google | **89.5%** | 97.4% | 81.3% | 44.6% | 87.8% | 88.8% | 92.2% | 1,310 |
| 4 | DeepSeek-R1 | DeepSeek | **86.9%** | 88.5% | 86.5% | 57.6% | 81.3% | 83.7% | 91.3% | 14,053 |
| 5 | MiniMax M2.5 | MiniMax | **73.4%** | 61.5% | 76.5% | 35.5% | 71.1% | 65.9% | 44.8% | 11,659 |

### Tier 2 — By Component

| Model | Turbine | Compressor | Pump | HX | Boiler | Mixer | Nozzle |
|-------|---------|-----------|------|-----|--------|-------|--------|
| Opus 4.6 | 96.9% | 76.3% | 100% | 88.7% | 98.2% | 92.0% | 94.1% |
| GPT-5.4 | 91.2% | 73.4% | 100% | 84.9% | 97.1% | 98.6% | 97.9% |
| Gemini 3.1 | 93.5% | 58.5% | 100% | 88.5% | 100% | 97.8% | 91.4% |
| DeepSeek-R1 | 86.8% | 61.4% | 93.3% | 89.9% | 93.5% | 95.7% | 77.0% |
| MiniMax M2.5 | 55.6% | 48.6% | 88.5% | 66.6% | 73.0% | 59.6% | 45.7% |

### Tier 1 → Tier 2 Degradation (multi-step penalty)

| Model | Tier 1 | Tier 2 | Drop | Interpretation |
|-------|--------|--------|------|----------------|
| Claude Opus 4.6 | 95.6% | 92.0% | -3.6pp | Best chaining — smallest drop |
| GPT-5.4 | 96.9% | 91.0% | -5.9pp | |
| Gemini 3.1 Pro | 97.3% | 89.5% | -7.8pp | Fast but fragile on multi-step |
| DeepSeek-R1 | 89.5% | 86.9% | -2.6pp | |
| MiniMax M2.5 | 84.5% | 73.4% | -11.1pp | Catastrophic — can't chain calculations |

### LLM Re-extraction Impact (Tier 2)

| Provider | Regex Score | LLM Score | Delta | Changed |
|----------|------------|-----------|-------|---------|
| Anthropic | 85.0% | 92.0% | +7.0pp | 20/101 questions |
| MiniMax | 61.5% | 73.4% | +11.9pp | 16/101 questions |
| DeepSeek | 85.1% | 86.9% | +1.8pp | 8/101 questions |
| Google | 88.9% | 89.5% | +0.6pp | 1/101 questions |
| OpenAI | 91.0% | 91.0% | +0.0pp | 0/101 questions |

### Final Leaderboard — Tier 3: Cycle Analysis (82 questions, 10 cycles, LLM re-extracted)

*Updated 15 March 2026: hrsg_balance_error scoring artifact removed from CCGT B/C questions (was always None).*

| Rank | Model | Provider | Score | Water | Air | R-134a | Air+Water | Depth A | Depth B | Depth C | Tok/Q |
|------|-------|----------|-------|-------|-----|--------|-----------|---------|---------|---------|-------|
| 🥇 | Claude Opus 4.6 | Anthropic | **91.3%** | 97.9% | 99.5% | 75.1% | 77.3% | 91.4% | 94.8% | 87.0% | ~53K |
| 🥈 | GPT-5.4 | OpenAI | **88.3%** | 91.5% | 97.4% | 79.2% | 71.7% | 89.9% | 89.9% | 84.6% | ~15K |
| 🥉 | Gemini 3.1 Pro | Google | **84.1%** | 93.9% | 81.3% | 88.6% | 62.9% | 81.3% | 87.6% | 83.1% | ~2.2K |
| 4 | DeepSeek-R1 | DeepSeek | **81.2%** | 89.0% | 90.4% | 63.7% | 64.3% | 76.4% | 87.8% | 79.6% | ~18K |
| 5 | MiniMax M2.5 | MiniMax | **40.2%** | 42.9% | 63.2% | 15.0% | 12.0% | 38.7% | 47.2% | 35.1% | ~15K |

### Tier 3 V2 — By Cycle Type

| Model | RNK (27q) | BRY (28q) | VCR (15q) | CCGT (12q) |
|-------|-----------|-----------|-----------|------------|
| Opus 4.6 | 97.9% | 99.5% | 75.1% | 77.3% |
| GPT-5.4 | 91.5% | 97.4% | 79.2% | 71.7% |
| Gemini 3.1 | 93.9% | 81.3% | 88.6% | 62.9% |
| DeepSeek-R1 | 89.0% | 90.4% | 63.7% | 64.3% |
| MiniMax M2.5 | 42.9% | 63.2% | 15.0% | 12.0% |

### Cross-Tier Comparison (T1 → T2 → T3)

| Model | Tier 1 | Tier 2 | Tier 3 | T1→T3 Drop | Interpretation |
|-------|--------|--------|--------|------------|----------------|
| Claude Opus 4.6 | 95.6% | 92.0% | 91.3% | -4.3pp | Best chaining — smallest drop across all 3 tiers |
| GPT-5.4 | 96.9% | 91.0% | 88.3% | -8.6pp | |
| Gemini 3.1 Pro | 97.3% | 89.5% | 84.1% | -13.2pp | Biggest frontier drop — struggles with multi-step |
| DeepSeek-R1 | 89.5% | 86.9% | 81.2% | -8.3pp | |
| MiniMax M2.5 | 84.5% | 73.4% | 40.2% | -44.3pp | Catastrophic collapse on cycle analysis |

### Session 5 Commits (13-15 March 2026)

| Commit | Description |
|--------|-------------|
| `1519b89` | fix: remove hrsg_balance_error from CCGT scored steps (always None) |
| `732230c` | feat: add deep investigation script with 12 paper-grade analyses |
| `d8dfea9` | docs: remove Tier 4 placeholder, move to future work |
| `9447601` | feat: add Tier 3 cycle analysis to HuggingFace publish script |
| `c2abc2d` | docs: update THERMOQA_HANDOFF.md with Session 4 — Tier 3 V2 results, 293 questions |

### Session 4 Commits (11-13 March 2026)

| Commit | Description |
|--------|-------------|
| `8342a77` | docs: update README with Tier 3 V2 results — 293 questions, 10 cycles, 5 models |
| `86ecbca` | fix: replace CoolProp real-gas air with NASA polynomial ideal gas for BRY-AV/BRY-RV ground truth |
| `affdbbf` | feat: harden Tier 3 to V2 — 6 changes, 10 cycles, 82 questions |
| `cedbf88` | fix: align Google Batch API with current docs — MIME type, snake_case, state handling |
| `d79f6ae` | fix: remove ref-state-dependent VCR-A steps and fix Unicode subscript extraction |
| `2462a50` | feat: add Tier 3 cycle analysis — 95 questions across 7 cycles × 3 depths |

### Session 3 Commits (8-10 March 2026)

| Commit | Description |
|--------|-------------|
| `3422a5a` | feat: implement Tier 2 component analysis — 101 questions across 7 devices |
| `167d0f8` | feat: add Tier 2 evaluation pipeline — sequential runner, batch APIs, LLM re-extraction |
| `8346cfc` | fix: save Tier 2 results incrementally to prevent data loss on interrupt |
| `9ef8715` | feat: add Google Gemini Batch API evaluation for Tier 2 |
| `72bbfa1` | fix: specify mime_type for Google batch file upload |

### Session 2 Commits (7-8 March 2026)

| Commit | Description |
|--------|-------------|
| `7503426` | fix: use explicit thinking with generous budget for Anthropic |
| `9d0e733` | fix: increase max_tokens to 64K for Anthropic adaptive thinking |
| `3f49e99` | feat: add Anthropic batch evaluation script for 50% cost reduction |
| — | feat: add --ids filter to batch script for selective re-runs |
| — | fix: correct Sonnet 4.6 model string in LLM extractor |
| — | fix: targeted LaTeX subscript normalization in extractor |
| — | feat: LLM-based extractor using Sonnet 4.6 for robust extraction |
| — | feat: add reextract.py CLI for re-extraction + re-scoring |
| — | feat: add OpenAI batch evaluation script + update to GPT-5.4 |
| — | fix: enable reasoning_effort for OpenAI GPT-5.4 |
| — | fix: set Gemini thinking_level to HIGH for fair comparison |
| — | feat: auto-load .env file for API keys (python-dotenv) |
| — | fix: rebuild summary from entry scores, not re-extraction (build_summary_from_entries) |
| — | feat: add HuggingFace dataset publishing script |
| — | docs: update README with v0.1 leaderboard and methodology |

---

## Key Findings (Session 2)

### 1. Supercritical is the discriminator
All models struggle above T_crit (373.95°C) and P_crit (22.064 MPa). Best: GPT-5.4 at 86.7%. Models memorize Çengel & Boles steam tables but don't know IAPWS-IF97 equations of state. Near the critical point, properties change violently — linear interpolation breaks down.

**Example:** At 402°C and 25.3 MPa, Opus interpolated from memory: h = 1887 kJ/kg. CoolProp (IAPWS-IF97): h = 2585.77 kJ/kg — 27% error. Same model with Python code execution: exact answer.

### 2. Tool use changes everything
Same model (Claude Opus 4.6), supercritical questions:
- Without tools (API, pure reasoning): **48%**
- With code execution (chat, installed IAPWS): **100%**
The gap isn't knowledge — it's methodology. Models know they need equation-of-state solvers.

### 3. Reasoning mode is critical
GPT-5.4 without reasoning_effort: **81%**. With reasoning_effort=high: **96.9%**. A 16-point jump. Reasoning enables cross-checking and self-correction.

### 4. Token efficiency ≠ accuracy
Gemini: 823 tokens/question, 97.3%. Opus: 12,981 tokens/question (16×), 95.6%. More thinking ≠ better answers for well-defined lookups.

### 5. Overthinking phenomenon
Gemini LOW thinking: 97.0%. Gemini HIGH thinking: 97.3%. Nearly identical — but individual supercritical questions changed in both directions. Non-deterministic. Single run insufficient for statistical claims.

---

## Key Findings (Session 3 — Tier 2)

### 1. Ranking reshuffles from Tier 1 to Tier 2
Tier 1: Gemini > GPT > Opus. Tier 2: Opus > GPT > Gemini. Multi-step component analysis tests a different skill than property lookups. Opus degrades least (-3.6pp), Gemini most (-7.8pp). The Tier 1→2 drop measures multi-step reasoning ability.

### 2. R-134a is the Tier 2 discriminator
Analogous to supercritical in Tier 1. All models collapse: 35–58% on R-134a vs 62–97% on Water. Models memorize Çengel & Boles steam tables but lack equivalent refrigerant property knowledge. CMP-AR-001 has P2=1.98 MPa — beyond the standard Çengel superheated R-134a table (max 1.6 MPa). Same mechanism as Tier 1 supercritical: beyond memorized tables, models can't interpolate.

### 3. Compressor is the hardest component
Even best model (Opus) only 76.3%. Three factors compound: (a) division formula h₂=h₁+(h₂s-h₁)/η_s is less intuitive than turbine's multiplication, (b) isentropic exit h₂s requires double interpolation (s, P) — very hard from tables, (c) most R-134a questions are compressor questions → double penalty.

### 4. Depth C > Depth A for frontier models (counter-intuitive)
Top 4 models score higher on full exergy analysis (Depth C) than basic energy balance (Depth A). More calculation steps provide more opportunities for cross-checking and self-correction. Exception: MiniMax — C(44.8%) << A(71.1%), cannot chain multi-step calculations.

### 5. Boiler Carnot factor is NOT a discriminator
All frontier models (97–100%) correctly apply s_gen = (s_out - s_in) - q_in/T_source and η_II via (1 - T₀/T_source). Our hypothesis that this would be the key discriminator was wrong — frontier models understand heat exergy well.

### 6. Token efficiency varies 23×
Gemini: 1,310 tok/Q → 89.5% (14.6 tok/%). GPT: 8,986 → 91.0% (98.7 tok/%). Opus: 30,371 → 92.0% (330 tok/%). Opus pays 3.4× more tokens than GPT for 1pp gain.

### 7. Three performance tiers emerge
Frontier (89–92%): Opus, GPT, Gemini. Mid-tier (87%): DeepSeek. Below (73%): MiniMax. MiniMax's -11.1pp Tier 1→2 drop is catastrophic. Tier 2 creates clearer separation than Tier 1.

### 8. Output format is a hidden variable
LLM re-extraction impact: MiniMax +11.9pp, Opus +7.0pp, DeepSeek +1.8pp, Gemini +0.6pp, GPT +0.0pp. GPT-5.4 writes perfectly regex-friendly structured answers. Opus writes LaTeX that breaks regex. The extraction method is as important as model capability for fair benchmarking.

---

## Key Findings (Session 5 — Deep Investigation + Scoring Fix)

### 1. hrsg_balance_error was a scoring artifact, not a model failure
`_compute_consistency()` for `hrsg_balance_error` always returned None because it requires `m_dot_air` and `m_dot_steam` which aren't available in extracted values. This unfairly penalized all 5 providers on 8 CCGT B/C questions (weight=3 in denominator, always scored as "missing"). Removing it raised CCGT scores by +0.9% to +2.8% per question. The HRSG coupling is already tested via the `m_dot_steam` step.

### 2. energy_balance_error_gas is a genuine failure
Unlike hrsg_balance_error, `energy_balance_error_gas` is NOT an artifact — models have all upstream values (h1-h5, w_comp, w_gt, q_combustion) but produce 10-20% energy balance errors on the gas side. 85% of evaluations have data but 0% pass the 2% tolerance. This is a real discriminator that stays in scoring.

### 3. Deep investigation produced 12 paper-grade analyses
`scripts/deep_investigation.py` generates a comprehensive 1200-line report (`analysis/deep_investigation_report.md`) covering: per-step accuracy heatmaps, hardest/easiest steps, consistency check forensics, error propagation analysis, per-cycle-type breakdowns, depth progression, provider-specific failure modes, and actionable recommendations. This forms the analytical backbone for the arxiv paper.

### 4. Step-level difficulty hierarchy validated
Universally hard steps (<50% mean across all models): `energy_balance_error_gas` (0%), `x_dest_HRSG` (15%), `x_dest_steam_turb` (15%), `x_dest_throttle` (16%), `COP_R` (31%). Universally easy (>90%): basic state properties (h, s, T, P), simple cycle efficiencies for power cycles.

---

## Key Findings (Session 4 — Tier 3 V1→V2)

### 1. V1 was too easy (93-96% for frontier)
30 ideal cycle free points + constant cp Air + R-134a absolute h/s removed from scoring. V2 fixes all three.

### 2. CoolProp "Air" ≠ textbook air tables
CoolProp models Air as real gas mixture (N₂/O₂/Ar). Textbook "variable specific heats" uses ideal gas with NASA polynomial cp(T). ~126 kJ/kg offset on absolute h, 5-24% on derived quantities. Fixed by implementing NASA 7-coefficient polynomials matching Çengel Table A-17.

### 3. abs_tolerance=0.5 was broken for dimensionless quantities
eta_th=0.19 vs 0.24 passed because |0.05| < 0.5. Fixed: 0.02 for eta_th, eta_II, COP_R, COP_Carnot.

### 4. Variable cp is the new discriminator
Gemini scores 53% on variable cp Brayton (uses constant-cp isentropic formula despite "variable specific heats" instruction). Opus 99%, GPT 93%. Distinguishes models that know Pr-method from those that don't.

### 5. CCGT combined cycle = future-proof
Best model 77%. 9 states, 2 fluids, HRSG coupling. Should remain challenging for years.

### 6. R-134a IIR reference state specified in question text
Models must use IIR (h=200, s=1.0 at 0°C sat liquid). Restores absolute h/s scoring fairly.

### 7. OpenAI max_completion_tokens=16000 was too low
Complex V2 questions (32-60 steps) consumed all tokens in reasoning, empty response. Fixed to 65536.

### 8. Consistency scoring works
energy_balance_error step checks model's own internal consistency. Only 25% of models pass (their own numbers don't close energy balance).

### 9. Token efficiency: Gemini 23× cheaper than Opus
Gemini: ~2.2K tok/Q → 84.1%. Opus: ~53K tok/Q → 91.3%. Diminishing returns on thinking tokens.

### 10. MiniMax below benchmark threshold
40.2% overall, VCR Depth C mostly 0%, CCGT mostly 0%. Not competitive on engineering thermodynamics.

---

## Decisions Resolved (Session 5)

| Question | Decision | Reasoning |
|----------|----------|-----------|
| hrsg_balance_error always None | **Remove from scoring** | `_compute_consistency()` needs m_dot_air + m_dot_steam, not available in extracted values. Always fails as "missing". HRSG coupling already tested via `m_dot_steam` step (weight=3). Removal eliminates double-penalty without losing coverage |
| energy_balance_error_gas 0% pass rate | **Keep in scoring** | Unlike hrsg, models HAVE all upstream values (h1-h5, w_comp, w_gt, q_combustion) but produce 10-20% balance errors. Genuine failure, not artifact. Real discriminator |
| Patch questions.jsonl or regenerate? | **Patch in-place** | Same as V1→V2 strategy. Preserves all existing model responses. Remove from `expected`, `steps`, and question text |

---

## Lessons Learned (Session 5)

| Lesson | Detail |
|--------|--------|
| **Distinguish scoring artifacts from model failures** | hrsg_balance_error (100% None) vs energy_balance_error_gas (85% have data, 0% pass). Same 0% pass rate, completely different root causes. Always check the None rate |
| **Deep investigation before publication** | The 12-analysis script caught a scoring bug that would have been embarrassing in a paper. Automated analysis > manual spot-checking |
| **Consistency steps need feasibility audit** | A scored step that requires values not available in the extraction pipeline will always fail. Audit all consistency steps against what the extractor can actually provide |
| **Weight removal changes denominators, not numerators** | Removing a weight=3 step that always scored 0 increases scores because the denominator shrinks. The impact varies by provider (0% to +2.8%) depending on how many other steps they got right |

---

## Decisions Resolved (Session 4)

| Question | Decision | Reasoning |
|----------|----------|-----------|
| V1 too easy? | Yes — 6 changes to harden | 93-96% ceiling, no room for future models |
| Ideal cycles | 30→5 | Free 100%, no discrimination value |
| Variable cp backend | NASA polynomial, not CoolProp "Air" | CoolProp = real gas, textbook = ideal gas with cp(T). 126 kJ/kg discrepancy |
| R-134a scoring | Restore absolute h/s, specify IIR in question | Convention mismatch fixed by explicit instruction |
| Weight scheme | 6-tier (1,2,3,4,5,6) | Emphasize engineering outcomes over intermediate values |
| Combined cycle | CCGT with variable cp Air + Water | Crown jewel, 9 states, 2 fluids, future-proof |
| Consistency scoring | Energy balance closure as scored step | Tests self-consistency, not just accuracy |
| abs_tolerance for η | 0.5→0.02 | 0.5 let 22% errors pass on dimensionless quantities |
| OpenAI max_tokens | 16000→65536 | Complex questions exhausted reasoning budget |
| CCGT ground truth | CoolProp "Air" (not NASA) | CCGT gas side still uses real gas — TODO for future fix |

---

## Lessons Learned (Session 4)

| Lesson | Detail |
|--------|--------|
| **Smoke test before full run** | 10-question test caught max_tokens bug, ground truth mismatch, tolerance issues before spending on 82×5 runs |
| **Ground truth source matters** | CoolProp "Air" vs NASA polynomial = 126 kJ/kg offset. Same function name, different physics model. Always verify against canonical textbook values |
| **Tolerance design is non-trivial** | abs_tolerance=0.5 seemed safe but broke dimensionless scoring. Different quantity types need different tolerances |
| **V1→V2 iteration is normal** | First version always reveals design flaws. Build, test, analyze, fix. Don't try to get it perfect first time |
| **Patch > Regenerate** | When ground truth changes but parameters don't, patch in-place. Saves all existing model responses |
| **4-layer difficulty = sustainable benchmark** | Layer 1 for sanity, Layer 4 for ceiling. Benchmark stays relevant as models improve |

---

## What Was Built (Session 5 — Deep Investigation + Scoring Fix)

### Deep Investigation Script (`scripts/deep_investigation.py`)
- Generates `analysis/deep_investigation_report.md` — 1200+ line report with 12 paper-grade analyses
- Analyses: per-step accuracy heatmap, hardest/easiest steps, consistency check forensics, error propagation, per-cycle-type breakdown, depth progression, provider failure modes, step correlation, weight sensitivity
- Discovered `hrsg_balance_error` scoring artifact (100% None rate across all providers)
- Confirmed `energy_balance_error_gas` is genuine failure (85% have data, 0% pass)

### hrsg_balance_error Scoring Fix
- Removed `hrsg_balance_error` step from CCGT template (`generation/templates/tier3_cycles.py`)
- Removed from scorer `consistency_steps` set and dead `_compute_consistency()` branch
- Removed from extractor patterns (`evaluation/extractor.py`, `evaluation/llm_extractor.py`)
- Removed from question generator format hints (`generation/question_generator.py`)
- Patched `data/tier3_cycles/questions.jsonl` — 8 CCGT B/C questions (expected, steps, question text)
- Rescored all 5 providers via `scripts/rescore_tier3.py`
- Updated `scripts/verify_tier3_prepublish.py` consistency checks

### HuggingFace Publishing
- `scripts/publish_huggingface.py` updated for three-tier publishing (was two-tier)
- Dynamic commit messages per tier

---

## What Was Built (Session 4 — Tier 3 Pipeline)

### Tier 3 Generation Pipeline
- `generation/cycle_state_generator.py` — full cycle state point generator for 10 cycle types (RNK-I, RNK-A, RNK-RH, BRY-I, BRY-A, BRY-RG, BRY-AV, BRY-RV, VCR-A, CCGT). CoolProp for Water/R-134a, NASA polynomial for variable-cp Air. 4-layer difficulty (easy/medium/hard/expert).
- `generation/templates/tier3_cycles.py` — parametric cycle templates with step definitions and weights (6-tier: 1,2,3,4,5,6).
- `taxonomy/tier3_cycles.yaml` — 10 cycle types, parameter ranges, fluid assignments.
- `scripts/generate_tier3.py` — CLI entry point for Tier 3 question generation.

### Tier 3 Evaluation Scripts
- `scripts/run_evaluation_tier3.py` — sequential runner for Tier 3.
- `scripts/run_batch_anthropic_tier3.py` — Anthropic batch API.
- `scripts/run_batch_openai_tier3.py` — OpenAI batch API (max_completion_tokens=65536).
- `scripts/run_batch_google_tier3.py` — Google sequential/batch.
- `scripts/reextract_tier3.py` — LLM re-extraction for Tier 3.
- `scripts/rescore_tier3.py` — re-score existing responses with updated ground truth/tolerances.

### V1→V2 Hardening Scripts
- `scripts/patch_variable_cp_ground_truth.py` — patch BRY-AV/BRY-RV ground truth from CoolProp real-gas Air to NASA polynomial ideal gas.
- `scripts/verify_tier3_prepublish.py` — pre-publication validation of Tier 3 dataset.

### Evaluation Module Extensions
- `evaluation/scorer.py` — `score_tier3_question()` with 6-tier weighted scoring, abs_tolerance=0.02 for dimensionless quantities (eta_th, eta_II, COP_R, COP_Carnot).
- `evaluation/extractor.py` — Tier 3 property pattern extensions, Unicode subscript extraction fix.
- `evaluation/llm_extractor.py` — `extract_tier3()` with Tier 3 step ID hints.

### NASA Polynomial Implementation
- Variable-cp air properties via NASA 7-coefficient polynomials matching Çengel Table A-17. Replaces CoolProp "Air" (real gas mixture) for BRY-AV and BRY-RV cycle types where textbook ideal-gas air tables are the expected reference.

### Design Docs
- `TIER3_DESIGN.md` — V1 design document.
- `TIER3_DESIGN_V2.md` — V2 hardening design: 6 changes, rationale, implementation plan.

---

## Known Issues / TODO

- CCGT gas side still uses CoolProp "Air" (real gas), not NASA polynomial. Should be patched for consistency with BRY-AV/BRY-RV. Impact: CCGT scores may shift when fixed.
- Google batch API still unreliable for preview models. Sequential preferred.
- MiniMax re-extraction has ~24 JSON parse failures (garbage model responses).
- Multi-run consistency analysis not yet done (single run only).
- HuggingFace dataset viewer may show "UnexpectedError" for nested JSON.
- ~~hrsg_balance_error always returned None — scoring artifact~~ **FIXED** (Session 5, commit `1519b89`)

---

## What Was Built (Session 2 — New Infrastructure)

### LLM-Based Extractor (`evaluation/llm_extractor.py`)
**Critical design decision:** Regex extraction had 5-15% failure rate depending on model output format (LaTeX subscripts, prose answers, thinking block contamination). Replaced with LLM-based extraction using Sonnet 4.6 (temperature=0).

**How it works:**
- Takes full response text (including thinking) + expected property keys
- Sonnet extracts ONLY final answer values, ignoring intermediate calculations
- Returns same dict format as regex extractor
- Cost: ~$0.10-0.20 per 110 questions

**Results by provider:**
| Provider | Regex Score | LLM Score | Delta | Changed |
|----------|------------|-----------|-------|---------|
| Google | 95.5% | 97.3% | +1.8% | 2 questions |
| Anthropic | 93.5% | 95.6% | +2.1% | 2 questions |
| MiniMax | 82.1% | 84.5% | +2.3% | 4 questions |
| OpenAI | 96.9% | 96.9% | 0% | 0 questions |
| DeepSeek | 89.5% | 89.3% | -0.2% | 3 questions (regression!) |

**Lesson:** LLM extractor is not always better. DeepSeek had regression — Sonnet misextracted 2 questions that regex got right. For DeepSeek, regex results kept.

**Recommendation for future:** Use LLM extractor as primary, but compare with regex. Take the better result per question if needed. Or implement "take max of regex vs LLM" logic.

### Reextract CLI (`scripts/reextract.py`)
```bash
python scripts/reextract.py --provider google --dry-run  # preview
python scripts/reextract.py --provider google             # apply
python scripts/reextract.py --all                          # all providers
```
Re-extracts from existing responses.jsonl without re-calling model APIs. Critical for pipeline iterations.

### Batch Evaluation Scripts
**Anthropic (`scripts/run_batch_anthropic.py`):**
- 50% cost reduction via Message Batches API
- `--submit`, `--status`, `--collect` subcommands
- `--ids` flag for selective re-runs (merge/replace logic)
- Handles adaptive thinking + empty response_text fallback

**OpenAI (`scripts/run_batch_openai.py`):**
- 50% cost reduction via Batch API (file upload → batch create → download results)
- Same 3 subcommands + `--ids` support
- Uses `reasoning_effort: "high"` (not `reasoning` param — Chat Completions vs Responses API difference)

### Summary Rebuild Fix (`evaluation/scorer.py`)
**Bug found:** `score_dataset()` was re-extracting from response_text using regex, discarding LLM extraction results in summary.json. Fixed by adding `build_summary_from_entries()` that reads pre-scored entry data directly. Applied to all 4 files: reextract.py, run_batch_anthropic.py, run_batch_openai.py, runner.py.

### LaTeX Subscript Fix (`evaluation/extractor.py`)
Opus writes `T_{sat}` (LaTeX) instead of `T_sat`. Regex couldn't match. Fix: `re.sub(r'([A-Za-z])_\{([A-Za-z0-9]+)\}', r'\1_\2', text)` — targeted, doesn't break `\frac{}{}` math.

### dotenv Support
All scripts auto-load `.env` file via python-dotenv. No more `export API_KEY=xxx` every session.

---

## What Was Built (Session 3 — Tier 2 Pipeline)

### Tier 2 Generation Pipeline
- `generation/state_generator.py` (~430 lines) — anchor-derive physics engine for 7 components. CoolProp for Water/R-134a, analytical for Air (cp=1.005, R=0.287, k=1.4). Dead state caching, 10-point validation.
- `generation/templates/tier2_components.py` (~550 lines) — 36 ComponentTemplate dataclasses (component × depth × fluid), step definitions with weights, 1-2 question phrasings each.
- `generation/param_sampler.py` (+350 lines) — 12 new samplers with physics validation (superheated inlet, liquid HX, T_c_out < T_sat).
- `generation/question_generator.py` (+200 lines) — `generate_tier2_questions()` with validation filtering.
- `scripts/generate_tier2.py` (~80 lines) — CLI entry point.
- `taxonomy/tier2_components.yaml` — 7 components, parameter ranges, step weights, anchor-derive sequences.

### Tier 2 Evaluation Scripts
- `scripts/run_evaluation_tier2.py` (~600 lines) — sequential runner, incremental save (flush after every question, Ctrl+C safe), `--ids`, `--reextract`, `--report`.
- `scripts/run_batch_anthropic_tier2.py` (~270 lines) — same submit/status/collect pattern.
- `scripts/run_batch_openai_tier2.py` (~280 lines) — same.
- `scripts/run_batch_google_tier2.py` (~434 lines) — NEW provider. google.genai SDK, Files API upload with `UploadFileConfig(mime_type="application/jsonl")`, `key` (not custom_id), `thought` field for thinking.
- `scripts/reextract_tier2.py` (~220 lines) — LLM re-extraction using `extract_tier2()`.

### Evaluation Module Extensions
- `evaluation/scorer.py` (+100 lines) — `score_tier2_question()` with weighted scoring: score = Σ(w_i × passed_i) / Σ(w_i). `StepScoreResult`, `Tier2QuestionResult` dataclasses. `score_question_auto()` router by tier.
- `evaluation/extractor.py` (+200 lines) — `TIER2_PROPERTY_PATTERNS`, `extract_tier2_properties()`, auto-convert eta_II percentage→fraction.
- `evaluation/llm_extractor.py` (+50 lines) — `extract_tier2()` with unit hints for all step IDs (h1, s_gen, Q_dot, X_dest_dot, etc.).

### Tier 2 Design Docs
- `TIER2_DESIGN.md` — comprehensive design: 7 components, 3 depths, anchor-derive pattern, scoring weights, question ID convention, implementation plan.
- `taxonomy/tier2_components.yaml` — machine-readable taxonomy with parameter ranges and step definitions.

### HuggingFace Update
- `scripts/publish_huggingface.py` — updated for multi-config (tier1_properties + tier2_components). Strips thinking_text/raw_response from results. Auto-inferred features (no explicit schema — `Json` type causes ValueError).
- Dataset: `olivenet/thermoqa` with two configs.
- Known issue: HF viewer shows "UnexpectedError" for nested JSON, but `load_dataset()` works.

---

## Decisions Resolved (Session 2)

| Question | Decision | Reasoning |
|----------|----------|-----------|
| Anthropic thinking mode | `adaptive` + `max_tokens=64000` | `enabled` is deprecated. Adaptive with generous max_tokens ensures text block output. Fallback extraction from thinking_text if empty. |
| Opus empty response_text | Fallback to thinking_text for extraction | 10/110 responses had empty text block. Re-running reduced to 3. LLM extractor handles remaining via thinking text. |
| OpenAI reasoning parameter | `reasoning_effort: "high"` in Chat Completions | NOT `reasoning: {"effort": "high"}` — that's Responses API. Batch uses `/v1/chat/completions`. Without reasoning: 81%. With: 96.9%. |
| GPT model | gpt-5.4 (not 5.3) | GPT-5.4 released 5 March 2026. Updated from handoff's gpt-5.3. |
| Gemini thinking level | HIGH (was LOW) | LOW gave 97.0% with 525 tokens. HIGH gives 97.3% with 823 tokens. Fair comparison requires all models at full reasoning. |
| LLM vs regex extraction | LLM primary, regex as quick preview | LLM extractor (Sonnet 4.6) is model-agnostic, handles LaTeX/prose/thinking. Regex kept in runner for live progress bar. |
| DeepSeek LLM extraction | Kept regex (LLM had -0.2% regression) | LLM extractor not always better. PD-004 went from 100%→0% with Sonnet. |
| Multiple runs | Single run for v0.1, multi-run planned for v0.2 | Non-deterministic behavior observed (Gemini LOW vs HIGH had different individual SC results despite same aggregate). 3 runs + mean±std needed. |
| HuggingFace features | Auto-infer (no explicit schema) | Explicit feature typing caused cast errors for nested JSON (given, expected). Removed features, HF auto-infers correctly. |

---

## Lessons Learned (Session 2)

| Lesson | Detail |
|--------|--------|
| **LLM extraction > regex for robustness** | Regex failed on LaTeX subscripts, prose format, thinking block contamination. LLM extractor (Sonnet) solved all these model-agnostically. But NOT always better — can regress on some questions. |
| **Batch APIs save 50% cost** | Anthropic and OpenAI both have batch APIs. Different interfaces: Anthropic streams results, OpenAI uses file upload/download. Both ~30-60 min for 110 questions. |
| **Reasoning mode is not optional** | GPT-5.4 without reasoning: 81%. With: 97%. Must enable for fair comparison. Each provider has different parameter: `reasoning_effort` (OpenAI), `thinking` (Anthropic), `thinking_config` (Google). |
| **Summary rebuild must use entry scores** | Original `score_dataset()` re-extracts from response_text — discards LLM extraction. Fixed with `build_summary_from_entries()`. |
| **Adaptive thinking is non-deterministic** | Same model, same question, different runs → different individual results. Gemini LOW vs HIGH: aggregate similar but individual SC questions flipped. Single run is a snapshot, not ground truth. |
| **Tool use vs pure reasoning is a separate axis** | Claude scored 48% on supercritical without tools, 100% with Python. This is a different capability than thermodynamic knowledge. v0.2 should have separate tracks. |
| **API differences between providers are treacherous** | OpenAI `reasoning` (Responses API) vs `reasoning_effort` (Chat Completions). Anthropic `enabled` deprecated → `adaptive`. Google `thinking_level` enum. MiniMax inline `<think>` tags. Each provider has unique quirks. |
| **Supercritical = equation-of-state test** | Models interpolate from memorized Çengel tables. Works for subcooled/saturated/superheated. Breaks at supercritical where IAPWS-IF97 equations are needed and properties are highly nonlinear. |

---

## Decisions Resolved (Session 3)

| Question | Decision | Reasoning |
|----------|----------|-----------|
| Throttle valve vs Boiler | **Boiler** | Throttle has no useful output → η_II undefined. Boiler has massive exergy destruction, clear η_II via Carnot factor. |
| HX phase change | **Liquid-only** | Both streams remain liquid. No condenser/evaporator. Saves phase-change for Tier 3 VCR. |
| R-134a scope | **Compressor + HX** | Where thermodynamically appropriate. Not in turbine/pump/boiler/mixer. |
| Dead state | **Always 25°C/0.1 MPa** | Varying T₀ doesn't test reasoning — just "plug in the right number." Reduces noise. |
| Unit system | **SI only** | Clean, consistent. No BTU/lbm. |
| Scoring approach | **Ground truth at each step** | No error propagation credit. Score each step independently vs CoolProp. |
| HuggingFace dataset name | **olivenet/thermoqa** (no version suffix) | v0.1 kept for backward compat. New dataset is versionless, updated with each tier. |
| Google batch API reliability | **Sequential preferred** | Batch sat in JOB_STATE_RUNNING with start_time=None for hours. Sequential more reliable for preview models. |
| Google batch mime_type | **UploadFileConfig(mime_type="application/jsonl")** | SDK doesn't accept direct kwarg for files.upload(). |
| Tier 2 incremental save | **Flush after every question** | Original script buffered all results — Ctrl+C lost progress. Fixed with append+flush pattern. |
| Air temperature field | **T1_C contains Kelvin** | Air sampler puts K values in T1_C field. Question text says "K". Calculations correct. Field name misleading but not a bug. |
| Air dead state h0 | **Latent bug — deferred** | `get_dead_state("Air")` uses cp×25 instead of cp×298.15. Not called by current code (Air Level C doesn't use flow exergy). Fix when needed. |

---

## Lessons Learned (Session 3)

| Lesson | Detail |
|--------|--------|
| **R-134a = beyond-table test** | Same mechanism as Tier 1 supercritical. P2=1.98 MPa exceeds Çengel superheated R-134a table (max 1.6 MPa). Models can't interpolate what they haven't memorized. |
| **Compressor formula confusion** | h₂=h₁+(h₂s-h₁)/η_s (division) vs turbine h₂=h₁-η_s(h₁-h₂s) (multiplication). Models sometimes apply the wrong one. |
| **Output format = hidden variable** | GPT: +0pp re-extraction (clean output). Opus: +7pp (LaTeX). MiniMax: +11.9pp. Fair benchmarking requires robust extraction. |
| **Incremental save is essential** | Original Tier 2 runner lost all progress on Ctrl+C. Must append+flush after every question. |
| **Google batch unreliable for preview models** | Job sat in PENDING/RUNNING for hours without processing. Sequential fallback needed. |
| **Depth C > Depth A for frontier models** | More steps = more self-correction. But MiniMax reverses: can't chain calculations. Genuine finding about capability tiers. |
| **Boiler hypothesis was wrong** | Expected Carnot factor to be discriminator. All frontier models got it right. Real discriminators: R-134a properties + compressor division formula. |
| **Spot-checking prevents false conclusions** | Independently verified all 101 questions with CoolProp. Confirmed low R-134a scores are real model errors, not question bugs. |
| **HuggingFace features bug recurred** | Explicit `Json` feature type not supported. Same lesson from Tier 1 — must use auto-infer. |

---

## Evaluation Pipeline (Final Architecture)

```
Question (JSONL)
    ↓
LLM API call (provider-specific: Anthropic/OpenAI/Google/DeepSeek/MiniMax/Ollama)
    ↓
Raw response → responses.jsonl (thinking + text preserved)
    ↓
Quick regex extraction (live progress bar in runner)
    ↓
LLM Extractor (Sonnet 4.6, temperature=0) via reextract.py
    ↓
Scorer (±2% relative OR ±0.5 absolute tolerance)
    ↓
Summary (build_summary_from_entries → summary.json)
    ↓
Leaderboard (run_evaluation.py --report)
```

### Tier 2 Evaluation Pipeline

```
Question (data/tier2_components/questions.jsonl)
    ↓
LLM API call (same 6 providers)
    ↓
Raw response → results_tier2/{provider}/responses.jsonl (incremental flush)
    ↓
Quick regex (extract_tier2_properties) in runner — live progress bar
    ↓
LLM Extractor (extract_tier2, Sonnet 4.6) via reextract_tier2.py
    ↓
Step-level Scorer (score_tier2_question, weighted partial credit)
    ↓
Summary (by_component, by_depth, by_fluid, by_step_type → summary.json)
    ↓
Leaderboard (run_evaluation_tier2.py --report)
```

### Provider Configuration (Final)

| Provider | Model | API String | Thinking Config | Batch Script |
|----------|-------|-----------|----------------|--------------|
| Google | Gemini 3.1 Pro | `gemini-3.1-pro-preview` | `thinking_level="HIGH"` | `run_batch_google_tier2.py` / `_tier3.py` (unreliable) |
| OpenAI | GPT-5.4 | `gpt-5.4` | `reasoning_effort="high"`, `max_completion_tokens=65536` | `run_batch_openai.py` / `_tier2.py` / `_tier3.py` |
| Anthropic | Claude Opus 4.6 | `claude-opus-4-6` | `adaptive`, `max_tokens=64000` | `run_batch_anthropic.py` / `_tier2.py` / `_tier3.py` |
| DeepSeek | DeepSeek-R1 | `deepseek-reasoner` | Native (always reasoning) | Sequential only |
| MiniMax | MiniMax M2.5 | `MiniMax-M2.5` | Inline `<think>` tags | Sequential only |
| Ollama | (any local) | configurable | varies | Sequential only |

### Token Usage — Tier 1

| Model | Mean Input | Mean Output | Score | Tokens per % |
|-------|-----------|-------------|-------|-------------|
| Gemini 3.1 Pro | 311 | 823 | 97.3% | 8.5 |
| GPT-5.4 | 273 | 10,798 | 96.9% | 111.4 |
| Claude Opus 4.6 | 341 | 12,981 | 95.6% | 135.8 |
| DeepSeek-R1 | 257 | 7,476 | 89.5% | 83.5 |
| MiniMax M2.5 | 277 | 7,551 | 84.5% | 89.4 |

### Token Usage — Tier 2

| Model | Mean Input | Mean Output | Score | Tokens per % |
|-------|-----------|-------------|-------|-------------|
| Gemini 3.1 Pro | 416 | 1,310 | 89.5% | 14.6 |
| GPT-5.4 | 373 | 8,986 | 91.0% | 98.7 |
| Claude Opus 4.6 | 465 | 30,371 | 92.0% | 330.1 |
| DeepSeek-R1 | 352 | 14,053 | 86.9% | 161.7 |
| MiniMax M2.5 | 373 | 11,659 | 73.4% | 158.8 |

### Token Usage — Tier 3

| Model | Mean Input | Mean Output | Score | Tokens per % |
|-------|-----------|-------------|-------|-------------|
| Gemini 3.1 Pro | 734 | 2,242 | 84.1% | 26.7 |
| GPT-5.4 | 680 | 14,896 | 88.3% | 168.7 |
| Claude Opus 4.6 | 838 | 53,439 | 91.3% | 585.3 |
| DeepSeek-R1 | 649 | 18,019 | 81.2% | 221.9 |
| MiniMax M2.5 | 682 | 15,203 | 40.2% | 378.2 |

---

## Project Structure (Updated)

```
ThermoQA/
├── CLAUDE.md                              # Claude Code instructions
├── THERMOQA_HANDOFF.md                    # This document
├── TIER2_DESIGN.md                        # Tier 2 design document
├── TIER3_DESIGN.md                        # NEW: Tier 3 V1 design document
├── TIER3_DESIGN_V2.md                     # NEW: Tier 3 V2 hardening design
├── README.md                              # Public-facing (all 3 leaderboards)
├── .env                                   # API keys (gitignored)
├── env.example                            # Template (includes HF_TOKEN)
├── .gitignore
├── pyproject.toml
├── requirements.txt
│
├── taxonomy/
│   ├── tier1_properties.yaml              # 8 categories, param ranges, scoring config
│   ├── tier2_components.yaml              # 7 components, depths, step weights
│   └── tier3_cycles.yaml                  # NEW: 10 cycle types, param ranges, fluid assignments
│
├── generation/
│   ├── __init__.py
│   ├── cycle_state_generator.py            # NEW: Tier 3 cycle state point generator
│   ├── state_generator.py                 # Tier 2 anchor-derive physics (~430 lines)
│   ├── param_sampler.py                   # Extended: +12 Tier 2 samplers (+350 lines)
│   ├── ground_truth.py                    # Extended: Tier 2 dispatch
│   ├── question_generator.py              # Extended: generate_tier2_questions() (+200 lines)
│   └── templates/
│       ├── __init__.py
│       ├── tier1_properties.py            # 29 parametric templates
│       ├── tier2_components.py            # 36 ComponentTemplates (~550 lines)
│       └── tier3_cycles.py                # NEW: Tier 3 cycle templates with step weights
│
├── evaluation/
│   ├── __init__.py
│   ├── extractor.py                       # Extended: extract_tier2_properties() (+200 lines)
│   ├── llm_extractor.py                   # Extended: extract_tier2() with unit hints (+50 lines)
│   ├── scorer.py                          # Extended: score_tier2_question(), weighted (+100 lines)
│   ├── runner.py                          # 6 providers, dotenv support
│   └── report.py                          # Leaderboard generator
│
├── data/
│   ├── tier1_properties/
│   │   ├── questions.jsonl                # 110 questions
│   │   └── metadata.json
│   ├── tier2_components/
│   │   ├── questions.jsonl                # 101 questions
│   │   └── metadata.json
│   └── tier3_cycles/                      # NEW
│       ├── questions.jsonl                # 82 questions (10 cycle types)
│       └── metadata.json
│
├── results/                               # Tier 1 per-provider results (gitignored)
│   ├── google/                            # 97.3%
│   ├── openai/                            # 96.9%
│   ├── anthropic/                         # 95.6%
│   ├── deepseek/                          # 89.5%
│   └── minimax/                           # 84.5%
│
├── results_tier2/                         # Tier 2 per-provider results (gitignored)
│   ├── google/                            # 89.5%
│   ├── openai/                            # 91.0%
│   ├── anthropic/                         # 92.0%
│   ├── deepseek/                          # 86.9%
│   └── minimax/                           # 73.4%
│
├── results_tier3/                         # Tier 3 V2 per-provider results (gitignored)
│   ├── google/                            # 84.1%
│   ├── openai/                            # 88.3%
│   ├── anthropic/                         # 91.3%
│   ├── deepseek/                          # 81.2%
│   └── minimax/                           # 40.2%
│
├── results_tier3_v1/                      # Tier 3 V1 results (backup)
│
├── analysis/
│   └── deep_investigation_report.md       # 1200-line report: 12 paper-grade analyses
│
├── scripts/
│   ├── validate_coolprop.py
│   ├── generate_tier1.py
│   ├── generate_tier2.py
│   ├── generate_tier3.py                  # NEW: Tier 3 cycle question generation
│   ├── run_evaluation.py                  # Tier 1 sequential evaluation CLI
│   ├── run_evaluation_tier2.py            # Tier 2 sequential + report
│   ├── run_evaluation_tier3.py            # NEW: Tier 3 sequential + report
│   ├── run_batch_anthropic.py             # Tier 1 Anthropic batch
│   ├── run_batch_anthropic_tier2.py       # Tier 2 Anthropic batch
│   ├── run_batch_anthropic_tier3.py       # NEW: Tier 3 Anthropic batch
│   ├── run_batch_openai.py               # Tier 1 OpenAI batch
│   ├── run_batch_openai_tier2.py          # Tier 2 OpenAI batch
│   ├── run_batch_openai_tier3.py          # NEW: Tier 3 OpenAI batch
│   ├── run_batch_google_tier2.py          # Tier 2 Google batch
│   ├── run_batch_google_tier3.py          # NEW: Tier 3 Google batch/sequential
│   ├── reextract.py                       # Tier 1 LLM re-extraction
│   ├── reextract_tier2.py                 # Tier 2 LLM re-extraction
│   ├── reextract_tier3.py                 # NEW: Tier 3 LLM re-extraction
│   ├── rescore_tier3.py                   # NEW: re-score with updated ground truth
│   ├── patch_variable_cp_ground_truth.py  # NEW: NASA polynomial patch for Air
│   ├── verify_tier3_prepublish.py         # Pre-publication validation
│   ├── deep_investigation.py              # 12 paper-grade analyses → analysis/ report
│   ├── publish_huggingface.py             # Updated: three tiers, multi-config
│   └── test_scorer.py
│
└── paper/                                 # arxiv paper drafts (Phase 4)
```

---

## Roadmap (Updated)

### Phase 1 — Tier 1: Property Lookups ✅ COMPLETE
- ✅ 110 questions generated with CoolProp ground truth
- ✅ 5 frontier models evaluated (Gemini, GPT-5.4, Opus, DeepSeek-R1, MiniMax M2.5)
- ✅ LLM-based extraction pipeline (Sonnet 4.6)
- ✅ Batch evaluation scripts (Anthropic + OpenAI)
- ✅ Published on HuggingFace: `olivenet/thermoqa-v0.1`
- ✅ README with leaderboard, methodology, findings

### Phase 2 — Tier 2: Component Analysis ✅ COMPLETE
- ✅ 7 components: turbine, compressor, pump, HX, boiler, mixer, nozzle
- ✅ 3 depths: A (energy), B (entropy), C (exergy)
- ✅ 3 fluids: Water (74), Air/ideal gas (17), R-134a (10)
- ✅ 101 questions generated, CoolProp validated (748 steps)
- ✅ Anchor-derive state generation with physics validation
- ✅ Step-level weighted scoring with partial credit
- ✅ 5 models evaluated with LLM re-extraction
- ✅ Google Batch API script added (but unreliable for preview models)
- ✅ Published on HuggingFace: `olivenet/thermoqa` (two configs)
- ✅ README updated with both leaderboards

### Phase 3 — Tier 3: Cycle Analysis ✅ COMPLETE
- ✅ 10 cycle types: RNK-I, RNK-A, RNK-RH, BRY-I, BRY-A, BRY-RG, BRY-AV, BRY-RV, VCR-A, CCGT
- ✅ 82 questions with 4-layer difficulty (easy/medium/hard/expert)
- ✅ 3 depths: A (energy), B (entropy), C (exergy)
- ✅ 4 fluid contexts: Water (27), Air (28), R-134a (15), Air+Water (12)
- ✅ NASA polynomial implementation for variable-cp air (Çengel Table A-17)
- ✅ V1→V2 hardening: 6 changes (ideal reduction, variable cp, IIR ref state, abs_tolerance, consistency scoring, weight scheme)
- ✅ 6-tier weighted scoring with abs_tolerance=0.02 for dimensionless quantities
- ✅ 5 models evaluated with LLM re-extraction
- ✅ Published on HuggingFace: `olivenet/thermoqa` (three configs)
- ✅ README updated with all 3 leaderboards

### Phase 3.5 — Improvements (optional, before publication)
- ⏳ CCGT gas side: patch from CoolProp "Air" to NASA polynomial for consistency
- ⏳ EntropyHunter v0.4 evaluation via Ollama (Tier 1 + Tier 2 + Tier 3)
- ⏳ Multi-run consistency analysis (3 runs, mean ± std)
- ⏳ "Take max of regex vs LLM" extraction logic

### Phase 4 — Publication
- arxiv paper: Tier 1 + Tier 2 + Tier 3 combined (293 questions)
- Potential venues: Energy and AI (Elsevier), MDPI Entropy, NeurIPS Benchmark Workshop
- Affiliation: Independent Researcher / Olivenet, KKTC

---

## Key References

### Directly Relevant
- UTQA: arXiv:2508.21452, HuggingFace: `herteltm/UTQA` (50 MCQ)
- Loubet et al.: arXiv:2502.05195 (22 calculation problems, ideal gas only)
- EngTrace: arXiv:2511.01650 (template-based dynamic generation pattern)
- ABench-Physics: arXiv:2507.04766 (22.5% drop on value alteration)
- Shahid & Walmsley: MDPI Information (Feb 2026) — Bloom's taxonomy in ChemE

### EntropyHunter (Predecessor)
- Model: `olivenet/entropy-hunter-8b-gguf` on HuggingFace
- Dataset preview: `olivenet/entropy-hunter-dataset-preview`
- Full handoff: ENTROPY_HUNTER_HANDOFF.md

---

## Technical Notes

### CoolProp Ground Truth Validation
CoolProp 7.2.0 uses IAPWS-IF97 (same as NIST Webbook). Validated:
- 13-point saturation table: max deviation 0.037% vs reference
- Supercritical confirmed accurate: same results as NIST at 402°C, 25.3 MPa
- Cross-verified: forward + inverse computation agreement within 0.01%

### Scoring Tolerance
- Numerical: ±2% relative OR ±0.5 absolute (whichever more lenient) — Tier 1 and Tier 2
- Quality (x): abs_tolerance = 0.03 (x ∈ [0,1]) — Tier 1 only
- Phase: exact match against acceptable_aliases (case-insensitive) — Tier 1 only
- Tier 2 step-level scoring: score = Σ(weight_i × passed_i) / Σ(weight_i)
- Tier 3 step-level scoring: same weighted formula, 6-tier weights (1,2,3,4,5,6)
- Tier 3 dimensionless quantities: abs_tolerance = 0.02 for eta_th, eta_II, COP_R, COP_Carnot (0.5 was too lenient — let 22% errors pass)
- Dead state (Tier 2/3): always T₀ = 25°C (298.15 K), P₀ = 0.1 MPa

### API Key Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
DEEPSEEK_API_KEY=sk-...
MINIMAX_API_KEY=...
HF_TOKEN=hf_...
```
All loaded automatically via python-dotenv from `.env` file.
