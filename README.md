# ThermoQA — A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models

ThermoQA evaluates how well large language models can solve
engineering thermodynamics problems — from steam table property
lookups to multi-step component analysis with exergy destruction.
**293 questions** across three tiers, all grounded in CoolProp 7.2.0
(IAPWS-IF97 + Helmholtz EOS). No other benchmark covers applied
engineering thermodynamics at this depth.

## Leaderboard (v0.3)

### Tier 1: Property Lookups

110 questions · Water/steam only · CoolProp 7.2.0 ground truth (IAPWS-IF97) · ±2% tolerance

| Rank | Model | Provider | Score | Easy | Medium | Hard |
|------|-------|----------|-------|------|--------|------|
| 🥇 | Gemini 3.1 Pro | Google | **97.3%** | 100% | 98.9% | 87.5% |
| 🥈 | GPT-5.4 | OpenAI | **96.9%** | 100% | 93.9% | 94.4% |
| 🥉 | Claude Opus 4.6 | Anthropic | **95.6%** | 88.5% | 94.4% | 75.0% |
| 4 | DeepSeek-R1 | DeepSeek | **89.5%** | 97.4% | 96.1% | 67.6% |
| 5 | MiniMax M2.5 | MiniMax | **84.5%** | 90.1% | 78.9% | 70.8% |

#### Per-Category Breakdown

| Category | Questions | Gemini | GPT-5.4 | Opus 4.6 | DeepSeek | MiniMax |
|----------|-----------|--------|---------|----------|----------|---------|
| Subcooled Liquid | 10 | 100% | 100% | 80.0% | 100% | 76.7% |
| Saturated Liquid | 12 | 100% | 100% | 100% | 91.7% | 97.9% |
| Wet Steam | 18 | 100% | 100% | 90.7% | 90.7% | 92.6% |
| Saturated Vapor | 10 | 100% | 100% | 100% | 100% | 87.5% |
| Superheated Vapor | 20 | 98.3% | 98.3% | 78.3% | 95.0% | 83.3% |
| **Supercritical** | **10** | **76.7%** | **86.7%** | **48.3%** | **48.3%** | **43.3%** |
| Phase Determination | 15 | 100% | 100% | 93.3% | 86.7% | 100% |
| Inverse Lookups | 15 | 100% | 88.3% | 96.7% | 95.0% | 63.3% |

### Tier 2: Component Analysis

101 questions · 7 components · 3 fluids (Water, Air, R-134a) · 3 analysis depths · Weighted step-level scoring

| Rank | Model | Provider | Score | Water | Air | R-134a | Tok/Q |
|------|-------|----------|-------|-------|-----|--------|-------|
| 🥇 | Claude Opus 4.6 | Anthropic | **92.0%** | 96.5% | 95.6% | 53.0% | 30,371 |
| 🥈 | GPT-5.4 | OpenAI | **91.0%** | 95.2% | 95.8% | 52.0% | 8,986 |
| 🥉 | Gemini 3.1 Pro | Google | **89.5%** | 97.4% | 81.3% | 44.6% | 1,310 |
| 4 | DeepSeek-R1 | DeepSeek | **86.9%** | 89.6% | 92.4% | 57.6% | 14,053 |
| 5 | MiniMax M2.5 | MiniMax | **73.4%** | 71.2% | 97.2% | 49.5% | 11,659 |

### Tier 3: Cycle Analysis

82 questions · 10 cycle types · 4 fluids (Water, Air, R-134a, Air+Water) · 3 analysis depths · Weighted step-level scoring

| Rank | Model | Provider | Score | Water | Air | R-134a | Air+Water |
|------|-------|----------|-------|-------|-----|--------|-----------|
| 🥇 | Claude Opus 4.6 | Anthropic | **91.0%** | 97.9% | 99.5% | 75.1% | 75.9% |
| 🥈 | GPT-5.4 | OpenAI | **88.1%** | 91.5% | 97.4% | 79.2% | 70.3% |
| 🥉 | Gemini 3.1 Pro | Google | **83.9%** | 93.9% | 81.3% | 88.6% | 61.7% |
| 4 | DeepSeek-R1 | DeepSeek | **81.1%** | 89.0% | 90.4% | 63.7% | 63.1% |
| 5 | MiniMax M2.5 | MiniMax | **40.2%** | 42.9% | 63.2% | 15.0% | 11.8% |

#### Per-Cycle-Type Breakdown

| Model | RNK-I | RNK-A | RNK-RH | BRY-I | BRY-A | BRY-AV | BRY-RG | BRY-RV | VCR-A | CCGT |
|-------|-------|-------|--------|-------|-------|--------|--------|--------|-------|------|
| Opus 4.6 | 98.0% | 99.8% | 95.0% | 100% | 99.7% | 98.8% | 99.7% | 99.5% | 75.1% | 75.9% |
| GPT-5.4 | 98.0% | 96.7% | 82.3% | 100% | 100% | 95.2% | 100% | 88.7% | 79.2% | 70.3% |
| Gemini 3.1 | 100% | 99.8% | 83.9% | 97.3% | 97.0% | 63.3% | 96.7% | 37.6% | 88.6% | 61.7% |
| DeepSeek-R1 | 94.6% | 94.0% | 80.3% | 100% | 99.2% | 88.5% | 100% | 52.1% | 63.7% | 63.1% |
| MiniMax M2.5 | 73.4% | 44.6% | 34.4% | 100% | 98.2% | 30.5% | 65.0% | 2.9% | 15.0% | 11.9% |

### Cross-Tier Performance

Each tier adds complexity. Rankings stabilize from Tier 2 onward.

| Model | Tier 1 | Tier 2 | Tier 3 | T1→T3 Drop |
|-------|--------|--------|--------|------------|
| Claude Opus 4.6 | 95.6% | 92.0% | 91.0% | −4.6 pp |
| GPT-5.4 | 96.9% | 91.0% | 88.1% | −8.8 pp |
| Gemini 3.1 Pro | 97.3% | 89.5% | 83.9% | −13.4 pp |
| DeepSeek-R1 | 89.5% | 86.9% | 81.1% | −8.4 pp |
| MiniMax M2.5 | 84.5% | 73.4% | 40.2% | −44.3 pp |

## Key Findings

### Tier 1 Findings

#### 1. Supercritical is the discriminator

All models struggle above the critical point (T > 373.95°C, P > 22.064 MPa). The best score is GPT-5.4 at 86.7%. Why? LLMs memorize steam table values from textbooks (Çengel & Boles, Moran & Shapiro) but don't know the IAPWS-IF97 equations of state. Near the critical point, properties change extremely nonlinearly — linear interpolation from memorized table entries produces large errors.

Example: At 402°C and 25.3 MPa, Claude Opus interpolated from memorized values and reported h = 1887 kJ/kg. The IAPWS-IF97 equation gives h = 2585.77 kJ/kg — a 27% error. The same model with Python code execution (CoolProp) gets the exact answer.

#### 2. Reasoning mode is critical

GPT-5.4 without reasoning: 81.0%. With reasoning: 96.9%. A 16-point jump from enabling chain-of-thought. Reasoning enables cross-checking, self-correction, and more careful interpolation. All models in the leaderboard use their best available reasoning mode.

#### 3. Efficiency ≠ accuracy

Gemini scored #1 with 525 tokens/question average. Claude Opus used 12,981 tokens (25×) and scored lower. More thinking does not necessarily produce better answers for well-defined property lookups.

#### 4. No model is perfect everywhere

Each model has unique weaknesses: GPT-5.4 struggles on inverse lookups (88.3%), Opus on supercritical (48.3%), MiniMax on inverse lookups (63.3%), DeepSeek on hard problems (67.6%). The benchmark discriminates.

#### 5. Tool use changes everything

The same model that scores 48% on supercritical questions without tools scores 100% with Python code execution (CoolProp/IAPWS). The gap isn't knowledge — it's methodology. LLMs know they need equation-of-state solvers but can't run them without tool access.

### Tier 2 Findings

#### 6. Rankings reshuffle under multi-step reasoning

Gemini (#1 on Tier 1) drops to #3 on Tier 2 (−7.8 pp). Opus (#3 on Tier 1) climbs to #1 (−3.6 pp). Property lookup accuracy does not predict component analysis performance. Multi-step thermodynamic reasoning is a distinct capability.

#### 7. R-134a is the Tier 2 discriminator

Analogous to supercritical for Tier 1. All models collapse on refrigerant properties (44–58%). Even Gemini (97.4% on water) drops to 44.6% on R-134a. Training data is overwhelmingly water/steam. R-134a exposes genuine equation-of-state reasoning gaps vs. table memorization.

#### 8. Compressor is the hardest component

All models score 50–76% on compressors vs. 90–100% on turbines. The work input formula w_in = (h₂s − h₁) / η requires dividing by isentropic efficiency, not multiplying. Models frequently reverse this — a conceptual error, not a lookup failure.

| Component | Opus | GPT-5.4 | Gemini | DeepSeek | MiniMax |
|-----------|------|---------|--------|----------|---------|
| Turbine | 96.9% | 91.2% | 93.5% | 93.0% | 69.6% |
| **Compressor** | **76.3%** | **73.4%** | **58.5%** | **62.2%** | **50.7%** |
| Pump | 100% | 100% | 100% | 97.0% | 88.5% |
| Heat Exchanger | 88.7% | 84.9% | 88.5% | 89.9% | 84.1% |
| Boiler | 98.2% | 97.1% | 100% | 93.5% | 74.8% |
| Mixing Chamber | 92.0% | 98.6% | 97.8% | 95.7% | 80.6% |
| Nozzle | 94.1% | 97.9% | 91.4% | 78.5% | 68.1% |

#### 9. Deeper analysis ≠ harder (for frontier models)

Counter-intuitive: top models score higher on Depth C (full exergy analysis) than Depth A (energy balance only). Opus: 90.2% → 94.8%. GPT-5.4: 89.8% → 94.7%. The structured framework of second-law analysis (entropy generation → exergy destruction → η_II) may scaffold reasoning better than open-ended energy balance.

| Depth | Description | Opus | GPT-5.4 | Gemini | DeepSeek | MiniMax |
|-------|-------------|------|---------|--------|----------|---------|
| A | Energy balance | 90.2% | 89.8% | 87.9% | 81.3% | 71.8% |
| B | + Entropy generation | 91.5% | 89.2% | 88.8% | 87.9% | 76.0% |
| C | + Exergy analysis | 94.8% | 94.7% | 92.2% | 92.4% | 72.3% |

#### 10. Boiler Carnot factor is NOT a discriminator

Top 3 models all score 97–100% on boilers. The Carnot factor calculation (1 − T₀/T_mean) is conceptually simple and well-represented in textbooks. It does not separate frontier models.

#### 11. Token efficiency varies 23×

Gemini uses 1,310 tokens/question; Opus uses 30,371 (23× more) for only 2.5 pp higher score. GPT-5.4 finds the sweet spot: 8,986 tokens for 91.0%. Three efficiency tiers emerge: lean (Gemini), balanced (GPT-5.4), and exhaustive (Opus, DeepSeek).

#### 12. Pump is solved

All top-3 models score 100% on pump calculations. Pumps have the simplest thermodynamics (incompressible liquid, small enthalpy change) and are no longer discriminating.

#### 13. Three performance tiers emerge

- **Tier A (90%+):** Opus (92.0%), GPT-5.4 (91.0%) — reliable for engineering calculations
- **Tier B (85–90%):** Gemini (89.5%), DeepSeek (86.9%) — competitive but with blind spots
- **Tier C (<75%):** MiniMax (73.4%) — not ready for unsupervised thermo work

### Tier 3 Findings

#### 14. Four-layer difficulty hierarchy works

Ideal gas cycles (~99%) → constant cp air (~97%) → variable cp / VCR (~60–88%) → CCGT (~12–76%). Each layer adds a distinct reasoning challenge: equation-of-state lookups, temperature-dependent properties, multi-fluid coupling.

#### 15. Variable cp air is the new discriminator

BRY-AV (variable cp air Brayton) separates models that memorize constant cp formulas from those that can apply NASA polynomial thermodynamics. Gemini drops from 97.0% (BRY-A, constant cp) to 63.3% (BRY-AV) and 37.6% (BRY-RV, regenerative + variable cp). Opus maintains 98.8%/99.5%.

#### 16. CCGT is the future-proof ceiling

Combined cycle gas turbine (9 state points, dual fluids, HRSG coupling) is the hardest cycle. Best score: Opus at 75.9%. No model exceeds 76% — this problem class has headroom for years.

#### 17. R-134a IIR reference state restores fairness

Using the IIR convention (h=200, s=1.0 at 0°C sat. liquid) for R-134a aligns with textbook practice. Without it, models that memorize ASHRAE-convention values produce systematic offsets that penalize correct reasoning.

#### 18. BRY-RV is the hardest non-CCGT cycle

Regenerative Brayton with variable cp air produces the widest score spread: 2.9% (MiniMax) to 99.5% (Opus). The regenerator effectiveness calculation with temperature-dependent properties requires careful state-point tracking that most models fail.

#### 19. Cross-tier ranking stabilizes

The top-3 ranking (Opus > GPT-5.4 > Gemini) holds across Tiers 2 and 3. Tier 1 rankings are misleading — property lookup accuracy does not predict multi-step thermodynamic reasoning. Three tiers are needed for reliable model assessment.

## Dataset

### Tier 1: Property Lookups (110 questions)

```json
{
  "id": "T1-SH-001",
  "tier": 1,
  "category": "superheated_vapor",
  "difficulty": "easy",
  "question": "Determine the specific enthalpy (h), specific entropy (s), and specific volume (v) of superheated steam at 350°C and 2000 kPa.\n\nReport your answers as:\nh = ___ kJ/kg\ns = ___ kJ/(kg·K)\nv = ___ m³/kg",
  "given": {"fluid": "Water", "T_C": 350, "P_kPa": 2000},
  "expected": {
    "h_kJ_kg": {"value": 3137.7, "unit": "kJ/kg", "tolerance_pct": 2.0, "abs_tolerance": 0.5},
    "s_kJ_kgK": {"value": 6.9583, "unit": "kJ/(kg*K)", "tolerance_pct": 2.0, "abs_tolerance": 0.5},
    "v_m3_kg": {"value": 0.13857, "unit": "m³/kg", "tolerance_pct": 2.0, "abs_tolerance": 0.5}
  }
}
```

| Category | Code | Count | Difficulty |
|----------|------|-------|------------|
| Subcooled Liquid | SL | 10 | easy |
| Saturated Liquid | SF | 12 | easy-medium |
| Wet Steam | WS | 18 | medium-hard |
| Saturated Vapor | SV | 10 | easy-medium |
| Superheated Vapor | SH | 20 | easy-medium |
| Supercritical | SC | 10 | hard |
| Phase Determination | PD | 15 | easy-hard |
| Inverse Lookups | IL | 15 | medium-hard |

**Total:** 110 questions (52 easy, 30 medium, 28 hard)

### Tier 2: Component Analysis (101 questions)

Multi-step thermodynamic analysis of individual components. Each question requires computing inlet/outlet properties, energy balance, and (at higher depths) entropy generation and exergy destruction.

**Components:** Turbine (18), Heat Exchanger (19), Compressor (14), Boiler (14), Nozzle (14), Mixing Chamber (12), Pump (10)

**Analysis Depths:**
- **Depth A (36 q):** Energy balance — compute work/heat output from inlet/outlet states
- **Depth B (35 q):** + Entropy generation — add s₂ and S_gen calculations
- **Depth C (30 q):** + Exergy analysis — add exergy destruction and second-law efficiency (η_II)

**Fluids:** Water (74), Air (17), R-134a (10)

**Difficulty:** Easy (34), Medium (37), Hard (30)

### Tier 3: Cycle Analysis (82 questions)

Full thermodynamic cycle calculations — Rankine, Brayton, vapor-compression refrigeration, and combined cycle. Each question requires computing multiple state points, energy/entropy balances, and (at higher depths) exergy destruction across the entire cycle.

**Cycle Types:** RNK-I (2), RNK-A (15), RNK-RH (10), BRY-I (3), BRY-A (9), BRY-AV (6), BRY-RG (6), BRY-RV (4), VCR-A (15), CCGT (12)

- **RNK-I/A/RH:** Ideal, actual, and reheat Rankine cycles (Water)
- **BRY-I/A/AV/RG/RV:** Ideal, actual, actual with variable cp, regenerative, and regenerative with variable cp Brayton cycles (Air)
- **VCR-A:** Actual vapor-compression refrigeration (R-134a, IIR reference state)
- **CCGT:** Combined cycle gas turbine (Air + Water, 9 state points)

**Analysis Depths:**
- **Depth A (29 q):** State points + energy balance (w_net, η_th, COP)
- **Depth B (26 q):** + Entropy generation per component
- **Depth C (27 q):** + Exergy destruction and second-law efficiency (η_II)

**Fluids:** Water (27), Air (28), R-134a (15), Air+Water (12)

**Difficulty:** Easy (15), Medium (26), Hard (41)

### Ground Truth

All reference values computed with CoolProp 7.2.0. Tier 1 uses IAPWS-IF97 (water/steam). Tier 2 uses IAPWS-IF97 for water and Helmholtz EOS for air and R-134a. Tier 3 uses IAPWS-IF97 for water, Helmholtz EOS for R-134a (IIR reference state), CoolProp real-gas for constant cp air cycles, and NASA 7-coefficient polynomials for variable cp air cycles (BRY-AV, BRY-RV). CoolProp validated against NIST reference data with maximum deviation of 0.037%.

## Quick Start

### Evaluate your model

```bash
git clone https://github.com/olivenet-iot/ThermoQA
cd ThermoQA
pip install -r requirements.txt

# Tier 1: Property lookups
export OPENAI_API_KEY=xxx
python scripts/run_evaluation.py --provider openai --model gpt-5.4 --output results/

# Tier 2: Component analysis
python scripts/run_evaluation_tier2.py --provider openai --output results_tier2/

# Tier 3: Cycle analysis
python scripts/run_evaluation_tier3.py --provider openai --output results_tier3/

# Or with other providers
python scripts/run_evaluation.py --provider anthropic --output results/
python scripts/run_evaluation.py --provider google --output results/
python scripts/run_evaluation.py --provider deepseek --output results/
python scripts/run_evaluation.py --provider ollama --model your-model --output results/

# View leaderboard
python scripts/run_evaluation.py --report results/
```

### Batch evaluation (50% cheaper)

```bash
# Anthropic batch (Tier 1)
python scripts/run_batch_anthropic.py --submit
python scripts/run_batch_anthropic.py --status
python scripts/run_batch_anthropic.py --collect

# Anthropic batch (Tier 2)
python scripts/run_batch_anthropic_tier2.py --submit
python scripts/run_batch_anthropic_tier2.py --status
python scripts/run_batch_anthropic_tier2.py --collect

# OpenAI batch (Tier 1)
python scripts/run_batch_openai.py --submit
python scripts/run_batch_openai.py --status
python scripts/run_batch_openai.py --collect

# OpenAI batch (Tier 2)
python scripts/run_batch_openai_tier2.py --submit
python scripts/run_batch_openai_tier2.py --status
python scripts/run_batch_openai_tier2.py --collect

# Anthropic batch (Tier 3)
python scripts/run_batch_anthropic_tier3.py --submit
python scripts/run_batch_anthropic_tier3.py --status
python scripts/run_batch_anthropic_tier3.py --collect

# OpenAI batch (Tier 3)
python scripts/run_batch_openai_tier3.py --submit
python scripts/run_batch_openai_tier3.py --status
python scripts/run_batch_openai_tier3.py --collect
```

### LLM-based extraction (recommended)

After running evaluation, re-extract answers using Sonnet 4.6 for robust parsing of any output format:

```bash
export ANTHROPIC_API_KEY=xxx
# Tier 1
python scripts/reextract.py --provider openai --dry-run  # preview changes
python scripts/reextract.py --provider openai             # apply
python scripts/reextract.py --all                          # all providers

# Tier 2
python scripts/reextract_tier2.py --provider openai
python scripts/reextract_tier2.py --all

# Tier 3
python scripts/reextract_tier3.py --provider openai
python scripts/reextract_tier3.py --all
```

## Methodology

### Tier 1 Pipeline

```
Question (JSONL) → LLM API call → Raw response → LLM Extractor (Sonnet 4.6) → Scorer → Results
```

1. **Question delivery:** System prompt instructs the model to show reasoning and report answers in `symbol = value unit` format. Each question includes format hints.
2. **Model response:** Free-form text. Models can use any format — prose, LaTeX, tables. All reasoning modes (thinking/chain-of-thought) enabled.
3. **Extraction:** LLM-based extractor (Claude Sonnet 4.6, temperature=0) parses the final answer values from the full response including thinking text. This eliminates model-specific regex issues.
4. **Scoring:** Per-property scoring with ±2% relative tolerance OR ±0.5 absolute tolerance (whichever is more lenient). Quality (x): absolute tolerance 0.03. Phase: exact match with alias list.

### Tier 2 Pipeline

Same extraction pipeline as Tier 1, with weighted step-level scoring:

1. **Questions:** Each problem specifies a component (turbine, compressor, etc.), operating conditions, and an analysis depth (A/B/C). Multiple output properties are requested, each with a weight reflecting engineering importance.
2. **Weighted scoring:** Each step (h₁, s₁, w_out, S_gen, x_dest, η_II, ...) has an assigned weight. The question score is the weighted sum of correct steps. Final answers (work output, exergy destruction) carry higher weights (0.20–0.30) than intermediate properties (0.10–0.15).
3. **Anchor-derive pattern:** Inlet properties anchor the calculation. Subsequent steps derive from anchors via energy/entropy/exergy balances. Error in an anchor propagates downstream — this tests multi-step reasoning fidelity.
4. **Dead state:** T₀ = 25°C (298.15 K), P₀ = 0.1 MPa (101.325 kPa) for all exergy calculations.

### Tier 3 Pipeline

Same extraction and scoring pipeline as Tier 2, extended to full cycle analysis:

1. **Questions:** Each problem specifies a cycle type (Rankine, Brayton, VCR, CCGT), operating conditions (pressures, temperatures, efficiencies, mass flow), and an analysis depth (A/B/C). 20–40 output properties are requested per question, each with a weight.
2. **Multi-state scoring:** Cycles involve 4–9 state points. Each state point's properties (h, s, T, P) are scored individually, then derived quantities (w_net, η_th, COP, S_gen, x_dest) carry higher weights.
3. **Variable cp handling:** BRY-AV and BRY-RV cycles use NASA 7-coefficient polynomials for air, matching textbook variable-cp Brayton analysis. This tests whether models can go beyond constant cp = 1.005 kJ/(kg·K).
4. **CCGT coupling:** Combined cycle questions require solving gas and steam sub-cycles linked by an HRSG energy balance (m_dot_steam computed from gas-side waste heat). Errors in the gas cycle propagate to the steam cycle.

### Why LLM extraction?

Initial regex-based extraction had ~5-15% failure rate depending on model output format (LaTeX subscripts, prose answers, thinking block contamination). LLM extraction reduced this to ~0% while being model-agnostic. We test thermodynamic knowledge, not output formatting.

### Scoring

- **Property accuracy:** fraction of correctly extracted properties within tolerance
- **Question score:** (Tier 1) fraction of correct properties; (Tier 2/3) weighted sum of correct steps
- **Mean question score:** average across all questions (reported as "Score" in leaderboard)

## Supported Providers

| Provider | SDK | Model | Thinking |
|----------|-----|-------|----------|
| Anthropic | anthropic | claude-opus-4-6 | adaptive |
| OpenAI | openai | gpt-5.4 | reasoning_effort=high |
| Google | google-genai | gemini-3.1-pro-preview | thinking_level=HIGH |
| DeepSeek | openai-compatible | deepseek-reasoner | native reasoning |
| MiniMax | openai-compatible | MiniMax-M2.5 | inline thinking |
| Ollama | HTTP | any local model | varies |

## Roadmap

- [x] **Tier 1 — Property Lookups** (v0.1, 110 questions)
- [x] **Tier 2 — Component Analysis** (v0.2, 101 questions)
- [x] **Tier 3 — Cycle Analysis** (v0.3, 82 questions) ← current
- [ ] **Tier 4 — Industrial Scenarios** (20-30 questions): Under-specified, judgment-required problems
- [ ] **Multi-run consistency analysis** (3 runs, mean ± std)
- [ ] **Tool-augmented track** (CoolProp function calling)
- [ ] **EntropyHunter evaluation** (fine-tuned 8B model)

## Related Projects

- **[EntropyHunter](https://huggingface.co/olivenet/entropy-hunter-8b-gguf)** — The world's first open-source fine-tuned LLM for second-law thermodynamic exergy analysis (92.7% adjusted accuracy, Qwen3-8B)
- **ExergyLab** — 36,000+ line thermoeconomic analysis platform with 7 analysis engines

## Citation

```bibtex
@misc{duzkar2026thermoqa,
  title={ThermoQA: A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models},
  author={Düzkar, Kemal},
  year={2026},
  url={https://github.com/olivenet-iot/ThermoQA}
}
```

## Competitive Landscape

Only two dedicated thermodynamics benchmarks exist in the LLM evaluation literature:

| Benchmark | Size | Format | Coverage |
|-----------|------|--------|----------|
| UTQA (Geißler et al., 2025) | 50 | MCQ | Physical chemistry thermo |
| Loubet et al. (2025) | 22 | Calculation | Ideal gas only |
| **ThermoQA (ours)** | **293** | **Open calculation** | **Engineering thermo, real fluids, component + cycle analysis** |

ThermoQA is the first benchmark covering applied engineering thermodynamics: steam tables, real fluid properties, supercritical states, multi-step component analysis, full cycle calculations (Rankine, Brayton, VCR, combined cycle), exergy destruction, and four working fluids.

## License

Dataset: CC-BY-4.0 · Code: MIT

## Author

**Kemal Düzkar** · Chemical Engineer · Olivenet · KKTC

Built with the conviction that measuring thermodynamic AI is the first step toward improving it.
