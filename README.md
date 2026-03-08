# ThermoQA — A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models

ThermoQA evaluates how well large language models can solve 
engineering thermodynamics problems — from steam table property 
lookups to multi-step exergy analysis. Ground truth is computed 
with CoolProp (IAPWS-IF97), the international standard for 
water and steam properties.

## Leaderboard — Tier 1: Property Lookups (v0.1)

110 questions · Water/steam only · CoolProp 7.2.0 ground truth (IAPWS-IF97) · ±2% tolerance

| Rank | Model | Provider | Score | Easy | Medium | Hard |
|------|-------|----------|-------|------|--------|------|
| 🥇 | Gemini 3.1 Pro | Google | **97.3%** | 100% | 98.9% | 87.5% |
| 🥈 | GPT-5.4 | OpenAI | **96.9%** | 100% | 93.9% | 94.4% |
| 🥉 | Claude Opus 4.6 | Anthropic | **95.6%** | 88.5% | 94.4% | 75.0% |
| 4 | DeepSeek-R1 | DeepSeek | **89.5%** | 97.4% | 96.1% | 67.6% |
| 5 | MiniMax M2.5 | MiniMax | **84.5%** | 90.1% | 78.9% | 70.8% |

### Per-Category Breakdown

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

## Key Findings

### 1. Supercritical is the discriminator

All models struggle above the critical point (T > 373.95°C, P > 22.064 MPa). The best score is GPT-5.4 at 86.7%. Why? LLMs memorize steam table values from textbooks (Çengel & Boles, Moran & Shapiro) but don't know the IAPWS-IF97 equations of state. Near the critical point, properties change extremely nonlinearly — linear interpolation from memorized table entries produces large errors.

Example: At 402°C and 25.3 MPa, Claude Opus interpolated from memorized values and reported h = 1887 kJ/kg. The IAPWS-IF97 equation gives h = 2585.77 kJ/kg — a 27% error. The same model with Python code execution (CoolProp) gets the exact answer.

### 2. Reasoning mode is critical

GPT-5.4 without reasoning: 81.0%. With reasoning: 96.9%. A 16-point jump from enabling chain-of-thought. Reasoning enables cross-checking, self-correction, and more careful interpolation. All models in the leaderboard use their best available reasoning mode.

### 3. Efficiency ≠ accuracy

Gemini scored #1 with 525 tokens/question average. Claude Opus used 12,981 tokens (25×) and scored lower. More thinking does not necessarily produce better answers for well-defined property lookups.

### 4. No model is perfect everywhere

Each model has unique weaknesses: GPT-5.4 struggles on inverse lookups (88.3%), Opus on supercritical (48.3%), MiniMax on inverse lookups (63.3%), DeepSeek on hard problems (67.6%). The benchmark discriminates.

### 5. Tool use changes everything

The same model that scores 48% on supercritical questions without tools scores 100% with Python code execution (CoolProp/IAPWS). The gap isn't knowledge — it's methodology. LLMs know they need equation-of-state solvers but can't run them without tool access.

## Dataset

### Question Format

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

### Distribution

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

### Ground Truth

All reference values computed with CoolProp 7.2.0 using the IAPWS-IF97 equation of state — the international standard for water and steam properties. CoolProp validated against NIST reference data with maximum deviation of 0.037%.

## Quick Start

### Evaluate your model

```bash
git clone https://github.com/olivenet-iot/ThermoQA
cd ThermoQA
pip install -r requirements.txt

# Run evaluation (choose your provider)
export OPENAI_API_KEY=xxx
python scripts/run_evaluation.py --provider openai --model gpt-5.4 --output results/

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
# Anthropic batch
python scripts/run_batch_anthropic.py --submit
python scripts/run_batch_anthropic.py --status
python scripts/run_batch_anthropic.py --collect

# OpenAI batch
python scripts/run_batch_openai.py --submit
python scripts/run_batch_openai.py --status
python scripts/run_batch_openai.py --collect
```

### LLM-based extraction (recommended)

After running evaluation, re-extract answers using Sonnet 4.6 for robust parsing of any output format:

```bash
export ANTHROPIC_API_KEY=xxx
python scripts/reextract.py --provider openai --dry-run  # preview changes
python scripts/reextract.py --provider openai             # apply
python scripts/reextract.py --all                          # all providers
```

## Methodology

### Evaluation Pipeline

```
Question (JSONL) → LLM API call → Raw response → LLM Extractor (Sonnet 4.6) → Scorer → Results
```

1. **Question delivery:** System prompt instructs the model to show reasoning and report answers in `symbol = value unit` format. Each question includes format hints.
2. **Model response:** Free-form text. Models can use any format — prose, LaTeX, tables. All reasoning modes (thinking/chain-of-thought) enabled.
3. **Extraction:** LLM-based extractor (Claude Sonnet 4.6, temperature=0) parses the final answer values from the full response including thinking text. This eliminates model-specific regex issues.
4. **Scoring:** Per-property scoring with ±2% relative tolerance OR ±0.5 absolute tolerance (whichever is more lenient). Quality (x): absolute tolerance 0.03. Phase: exact match with alias list.

### Why LLM extraction?

Initial regex-based extraction had ~5-15% failure rate depending on model output format (LaTeX subscripts, prose answers, thinking block contamination). LLM extraction reduced this to ~0% while being model-agnostic. We test thermodynamic knowledge, not output formatting.

### Scoring

- **Property accuracy:** fraction of correctly extracted properties within tolerance
- **Question score:** fraction of correct properties per question
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

- [x] **Tier 1 — Property Lookups** (v0.1, 110 questions) ← current
- [ ] **Tier 2 — Component Analysis** (80-100 questions): Single equipment, exergy destruction, entropy generation, second-law efficiency
- [ ] **Tier 3 — Cycle Analysis** (60-80 questions): Rankine, Brayton, VCR, cogeneration — full cycle calculations
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
| **ThermoQA (ours)** | **110+** | **Open calculation** | **Engineering thermo, real fluids** |

ThermoQA is the first benchmark covering applied engineering thermodynamics: steam tables, real fluid properties, supercritical states, and (upcoming) component/cycle analysis.

## License

Dataset: CC-BY-4.0 · Code: MIT

## Author

**Kemal Düzkar** · Chemical Engineer · Olivenet · KKTC

Built with the conviction that measuring thermodynamic AI is the first step toward improving it.
