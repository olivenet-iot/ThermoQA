# ThermoQA — A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models

ThermoQA evaluates how well large language models can solve
engineering thermodynamics problems — from steam table property
lookups to multi-step component analysis with exergy destruction.
**293 questions** across three tiers, all grounded in CoolProp 7.2.0
(IAPWS-IF97 + Helmholtz EOS). No other benchmark covers applied
engineering thermodynamics at this depth.

## Leaderboard (v0.4)

All scores are 3-run means. σ = standard deviation across runs.

### Tier 1: Property Lookups

110 questions · Water/steam only · CoolProp 7.2.0 ground truth (IAPWS-IF97) · ±2% tolerance

| Rank | Model | Provider | Score | σ | Easy | Medium | Hard |
|------|-------|----------|-------|---|------|--------|------|
| 🥇 | Gemini 3.1 Pro | Google | **97.9%** | ±0.5% | 100% | 99.6% | 92.1% |
| 🥈 | GPT-5.4 | OpenAI | **97.8%** | ±0.8% | 100% | 95.7% | 95.9% |
| 🥉 | Claude Opus 4.6 | Anthropic | **96.4%** | ±0.9% | 98.7% | 98.9% | 89.5% |
| 4 | Grok 4 | xAI | **91.8%** | ±1.2% | 97.9% | 95.0% | 77.2% |
| 5 | DeepSeek-R1 | DeepSeek | **90.5%** | ±0.2% | 98.1% | 93.2% | 73.6% |
| 6 | MiniMax M2.5 | MiniMax | **85.2%** | ±0.6% | 92.3% | 85.7% | 71.4% |

#### Per-Category Breakdown

| Category | Questions | Gemini | GPT-5.4 | Opus 4.6 | Grok 4 | DeepSeek | MiniMax |
|----------|-----------|--------|---------|----------|--------|----------|---------|
| Subcooled Liquid | 10 | 100% | 100% | 100% | 100% | 100% | 93.3% |
| Saturated Liquid | 12 | 100% | 100% | 100% | 100% | 100% | 87.5% |
| Wet Steam | 18 | 100% | 100% | 99.4% | 100% | 94.5% | 92.0% |
| Saturated Vapor | 10 | 100% | 100% | 100% | 100% | 99.2% | 95.8% |
| Superheated Vapor | 20 | 99.4% | 99.4% | 98.9% | 99.4% | 92.2% | 85.8% |
| **Supercritical** | **10** | **77.8%** | **89.5%** | **70.5%** | **52.8%** | **48.9%** | **45.0%** |
| Phase Determination | 15 | 100% | 100% | 95.5% | 82.2% | 88.9% | 97.8% |
| Inverse Lookups | 15 | 100% | 91.7% | 100% | 90.0% | 93.3% | 75.9% |

### Tier 2: Component Analysis

101 questions · 7 components · 3 fluids (Water, Air, R-134a) · 3 analysis depths · Weighted step-level scoring

| Rank | Model | Provider | Score | σ | Water | Air | R-134a |
|------|-------|----------|-------|---|-------|-----|--------|
| 🥇 | Claude Opus 4.6 | Anthropic | **92.1%** | ±0.2% | 96.8% | 94.0% | 54.1% |
| 🥈 | GPT-5.4 | OpenAI | **90.8%** | ±0.5% | 95.6% | 93.6% | 50.4% |
| 🥉 | Gemini 3.1 Pro | Google | **90.8%** | ±1.2% | 98.2% | 84.0% | 47.6% |
| 4 | DeepSeek-R1 | DeepSeek | **89.2%** | ±2.5% | 92.0% | 92.4% | 63.4% |
| 5 | Grok 4 | xAI | **87.9%** | ±0.7% | 93.8% | 88.3% | 44.0% |
| 6 | MiniMax M2.5 | MiniMax | **76.2%** | ±1.1% | 74.5% | 96.3% | 54.2% |

### Tier 3: Cycle Analysis

82 questions · 10 cycle types · 4 fluids (Water, Air, R-134a, Air+Water) · 3 analysis depths · Weighted step-level scoring

| Rank | Model | Provider | Score | σ | Water | Air | R-134a | Air+Water |
|------|-------|----------|-------|---|-------|-----|--------|-----------|
| 🥇 | Claude Opus 4.6 | Anthropic | **93.6%** | ±0.5% | 95.9% | 99.2% | 81.6% | 90.1% |
| 🥈 | GPT-5.4 | OpenAI | **89.7%** | ±0.1% | 92.1% | 97.8% | 76.6% | 82.0% |
| 🥉 | Gemini 3.1 Pro | Google | **87.5%** | ±1.5% | 95.2% | 84.2% | 90.9% | 74.0% |
| 4 | DeepSeek-R1 | DeepSeek | **81.0%** | ±2.2% | 86.0% | 87.7% | 66.8% | 72.2% |
| 5 | Grok 4 | xAI | **80.4%** | ±0.8% | 90.9% | 83.2% | 73.6% | 58.6% |
| 6 | MiniMax M2.5 | MiniMax | **52.7%** | ±1.5% | 52.3% | 72.8% | 32.5% | 31.8% |

#### Per-Cycle-Type Breakdown

| Model | RNK-I | RNK-A | RNK-RH | BRY-I | BRY-A | BRY-AV | BRY-RG | BRY-RV | VCR-A | CCGT |
|-------|-------|-------|--------|-------|-------|--------|--------|--------|-------|------|
| Opus 4.6 | 99.3% | 99.8% | 89.5% | 100% | 99.9% | 97.4% | 99.6% | 98.9% | 81.6% | 90.1% |
| GPT-5.4 | 90.4% | 97.5% | 84.3% | 99.1% | 100% | 96.8% | 100% | 90.3% | 76.6% | 82.0% |
| Gemini 3.1 | 100% | 99.7% | 87.5% | 96.7% | 97.2% | 69.7% | 96.7% | 48.4% | 90.9% | 74.0% |
| Grok 4 | 90.4% | 96.6% | 82.5% | 97.5% | 96.8% | 54.9% | 96.7% | 63.8% | 73.6% | 58.6% |
| DeepSeek-R1 | 95.7% | 89.8% | 78.4% | 98.5% | 99.2% | 76.7% | 99.5% | 52.5% | 66.8% | 72.2% |
| MiniMax M2.5 | 61.7% | 59.1% | 40.2% | 100% | 99.1% | 27.8% | 89.5% | 35.8% | 32.5% | 31.8% |

### Cross-Tier Performance

Each tier adds complexity. Rankings stabilize from Tier 2 onward. Composite score: weighted by question count (110×T1 + 101×T2 + 82×T3) / 293.

| Model | Tier 1 | Tier 2 | Tier 3 | T1→T3 Drop | Composite |
|-------|--------|--------|--------|------------|-----------|
| Claude Opus 4.6 | 96.4% | 92.1% | 93.6% | −2.8 pp | **94.1%** |
| GPT-5.4 | 97.8% | 90.8% | 89.7% | −8.1 pp | **93.1%** |
| Gemini 3.1 Pro | 97.9% | 90.8% | 87.5% | −10.4 pp | **92.5%** |
| DeepSeek-R1 | 90.5% | 89.2% | 81.0% | −9.5 pp | **87.4%** |
| Grok 4 | 91.8% | 87.9% | 80.4% | −11.4 pp | **87.3%** |
| MiniMax M2.5 | 85.2% | 76.2% | 52.7% | −32.5 pp | **73.0%** |

## Key Findings

### Tier 1 Findings

#### 1. Supercritical is the discriminator

All models struggle above the critical point (T > 373.95°C, P > 22.064 MPa). The best 3-run mean is GPT-5.4 at 89.5%. Why? LLMs memorize steam table values from textbooks (Çengel & Boles, Moran & Shapiro) but don't know the IAPWS-IF97 equations of state. Near the critical point, properties change extremely nonlinearly — linear interpolation from memorized table entries produces large errors.

Example: At 402°C and 25.3 MPa, Claude Opus interpolated from memorized values and reported h = 1887 kJ/kg. The IAPWS-IF97 equation gives h = 2585.77 kJ/kg — a 27% error. The same model with Python code execution (CoolProp) gets the exact answer.

#### 2. Reasoning mode is critical

GPT-5.4 without reasoning: 81.0%. With reasoning: 97.8%. A 17-point jump from enabling chain-of-thought. Reasoning enables cross-checking, self-correction, and more careful interpolation. All models in the leaderboard use their best available reasoning mode.

#### 3. Efficiency ≠ accuracy

Gemini scored #1 with 525 tokens/question average. Claude Opus used 12,981 tokens (25×) and scored lower. More thinking does not necessarily produce better answers for well-defined property lookups.

#### 4. No model is perfect everywhere

Each model has unique weaknesses: GPT-5.4 struggles on inverse lookups (91.7%), Opus on supercritical (70.5%), MiniMax on inverse lookups (75.9%), DeepSeek on hard problems (73.6%), Grok 4 on phase determination (82.2%). The benchmark discriminates.

#### 5. Tool use changes everything

The same model that scores 70% on supercritical questions without tools scores 100% with Python code execution (CoolProp/IAPWS). The gap isn't knowledge — it's methodology. LLMs know they need equation-of-state solvers but can't run them without tool access.

#### 6. Multi-run consistency varies widely

Standard deviation across 3 runs reveals determinism differences. Tier 1: DeepSeek is most consistent (σ = ±0.2%), xAI most variable (σ = ±1.2%). Tier 3: OpenAI is most deterministic (σ = ±0.1%), DeepSeek most volatile (σ = ±2.2%). Models with native reasoning tokens (DeepSeek, OpenAI) tend toward higher variance on complex problems despite low variance on simpler ones.

### Tier 2 Findings

#### 7. Rankings reshuffle under multi-step reasoning

Gemini (#1 on Tier 1) drops to #3 on Tier 2 (−7.1 pp). Opus (#3 on Tier 1) climbs to #1 (−4.3 pp). Property lookup accuracy does not predict component analysis performance. Multi-step thermodynamic reasoning is a distinct capability.

#### 8. R-134a is the Tier 2 discriminator

Analogous to supercritical for Tier 1. All models collapse on refrigerant properties (44–63%). Even Gemini (98.2% on water) drops to 47.6% on R-134a. Training data is overwhelmingly water/steam. R-134a exposes genuine equation-of-state reasoning gaps vs. table memorization.

#### 9. Compressor is the hardest component

All models score 55–75% on compressors vs. 70–97% on turbines. The work input formula w_in = (h₂s − h₁) / η requires dividing by isentropic efficiency, not multiplying. Models frequently reverse this — a conceptual error, not a lookup failure.

| Component | Opus | GPT-5.4 | Gemini | Grok 4 | DeepSeek | MiniMax |
|-----------|------|---------|--------|--------|----------|---------|
| Turbine | 96.9% | 90.8% | 94.4% | 90.0% | 91.9% | 70.1% |
| **Compressor** | **75.4%** | **71.2%** | **66.3%** | **64.8%** | **67.2%** | **55.5%** |
| Pump | 100% | 100% | 100% | 99.0% | 98.5% | 97.5% |
| Heat Exchanger | 90.1% | 84.8% | 89.2% | 85.5% | 91.3% | 87.6% |
| Boiler | 98.8% | 99.1% | 98.5% | 93.8% | 97.8% | 71.3% |
| Mixing Chamber | 91.5% | 99.0% | 98.6% | 98.1% | 96.6% | 88.5% |
| Nozzle | 93.4% | 96.6% | 91.7% | 89.1% | 83.6% | 68.3% |

#### 10. Deeper analysis ≠ harder (for frontier models)

Counter-intuitive: top models score higher on Depth C (full exergy analysis) than Depth A (energy balance only). Opus: 90.0% → 96.1%. GPT-5.4: 88.2% → 93.9%. The structured framework of second-law analysis (entropy generation → exergy destruction → η_II) may scaffold reasoning better than open-ended energy balance.

| Depth | Description | Opus | GPT-5.4 | Gemini | Grok 4 | DeepSeek | MiniMax |
|-------|-------------|------|---------|--------|--------|----------|---------|
| A | Energy balance | 90.0% | 88.2% | 90.1% | 82.2% | 86.2% | 71.9% |
| B | + Entropy generation | 90.8% | 90.8% | 89.5% | 88.3% | 88.8% | 78.7% |
| C | + Exergy analysis | 96.1% | 93.9% | 93.0% | 94.3% | 93.4% | 78.3% |

#### 11. Boiler Carnot factor is NOT a discriminator

Top 4 models all score 94–99% on boilers. The Carnot factor calculation (1 − T₀/T_mean) is conceptually simple and well-represented in textbooks. It does not separate frontier models.

#### 12. Token efficiency varies 23×

Gemini uses 1,310 tokens/question; Opus uses 30,371 (23× more) for only 1.3 pp higher score. GPT-5.4 finds the sweet spot: 8,986 tokens for 90.8%. Three efficiency tiers emerge: lean (Gemini), balanced (GPT-5.4, Grok 4), and exhaustive (Opus, DeepSeek).

#### 13. Pump is solved

All top-4 models score 99–100% on pump calculations. Pumps have the simplest thermodynamics (incompressible liquid, small enthalpy change) and are no longer discriminating.

#### 14. Three performance tiers emerge

- **Tier A (90%+):** Opus (92.1%), GPT-5.4 (90.8%), Gemini (90.8%) — reliable for engineering calculations
- **Tier B (85–90%):** DeepSeek (89.2%), Grok 4 (87.9%) — competitive but with blind spots
- **Tier C (<80%):** MiniMax (76.2%) — not ready for unsupervised thermo work

#### 15. Grok 4 enters mid-tier

Grok 4 debuts at #4 on Tier 1 (91.8%) but drops to #5 on Tier 2 (87.9%) and Tier 3 (80.4%). Strong on property lookups (100% on saturated states, 99.4% on superheated vapor) but weaker on multi-step analysis — especially variable cp air (BRY-AV: 54.9%) and combined cycle (CCGT: 58.6%). Paired with DeepSeek-R1 in the mid-tier, with nearly identical composite scores (87.3% vs. 87.4%).

### Tier 3 Findings

#### 16. Four-layer difficulty hierarchy works

Ideal gas cycles (~98–100%) → constant cp air (~97–100%) → variable cp / VCR (~28–97%) → CCGT (~32–90%). Each layer adds a distinct reasoning challenge: equation-of-state lookups, temperature-dependent properties, multi-fluid coupling.

#### 17. Variable cp air is the new discriminator

BRY-AV (variable cp air Brayton) separates models that memorize constant cp formulas from those that can apply NASA polynomial thermodynamics. Gemini drops from 97.2% (BRY-A, constant cp) to 69.7% (BRY-AV) and 48.4% (BRY-RV, regenerative + variable cp). Opus maintains 99.9%/98.9%.

#### 18. CCGT remains the hardest cycle

Combined cycle gas turbine (9 state points, dual fluids, HRSG coupling) is the hardest cycle. Best 3-run mean: Opus at 90.1%. Only two models exceed 80% (Opus, GPT-5.4). This problem class still has headroom for improvement — five of six models score below 75%.

#### 19. R-134a IIR reference state restores fairness

Using the IIR convention (h=200, s=1.0 at 0°C sat. liquid) for R-134a aligns with textbook practice. Without it, models that memorize ASHRAE-convention values produce systematic offsets that penalize correct reasoning.

#### 20. BRY-RV is the hardest non-CCGT cycle

Regenerative Brayton with variable cp air produces the widest score spread: 35.8% (MiniMax) to 98.9% (Opus). The regenerator effectiveness calculation with temperature-dependent properties requires careful state-point tracking that most models fail.

#### 21. Cross-tier ranking stabilizes

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
python scripts/run_evaluation.py --provider xai --output results/
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

After running evaluation, re-extract answers using gpt-4.1-mini for robust parsing of any output format:

```bash
export OPENAI_API_KEY=xxx
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
Question (JSONL) → LLM API call → Raw response → LLM Extractor (gpt-4.1-mini) → Scorer → Results
```

1. **Question delivery:** System prompt instructs the model to show reasoning and report answers in `symbol = value unit` format. Each question includes format hints.
2. **Model response:** Free-form text. Models can use any format — prose, LaTeX, tables. All reasoning modes (thinking/chain-of-thought) enabled.
3. **Extraction:** LLM-based extractor (gpt-4.1-mini, temperature=0) parses the final answer values from the full response including thinking text. This eliminates model-specific regex issues.
4. **Scoring:** Per-property scoring with ±2% relative tolerance OR ±0.5 absolute tolerance (whichever is more lenient). Quality (x): absolute tolerance 0.03. Phase: exact match with alias list.
5. **Consistency:** 3 independent runs per model per tier. Scores reported as mean ± standard deviation.

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
| xAI | openai-compatible | grok-4.20-beta-0309-reasoning | native reasoning |
| Ollama | HTTP | any local model | varies |

## Roadmap

- [x] **Tier 1 — Property Lookups** (v0.1, 110 questions)
- [x] **Tier 2 — Component Analysis** (v0.2, 101 questions)
- [x] **Tier 3 — Cycle Analysis** (v0.3, 82 questions)
- [x] **Multi-run consistency analysis** (v0.4, 3 runs × 6 models, mean ± std)
- [ ] **Tool-augmented track** (CoolProp function calling)
- [ ] **EntropyHunter evaluation** (fine-tuned 8B model)

## Future Work

Future extensions may include open-ended industrial design problems requiring engineering judgment, where single correct answers don't exist.

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
