# ThermoQA — Project Handoff Document
## A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models
### Initiated 6 March 2026

---

## One-Line Summary
ThermoQA is a comprehensive benchmark to evaluate LLM performance on engineering thermodynamics — from steam table lookups to multi-step exergy analysis and full cycle calculations. **No such benchmark exists today.** The field is wide open.

---

## Who Is This For
This document is a **continuation prompt** for Claude. It contains all context needed to begin development of ThermoQA without re-explaining decisions already made.

**Owner:** Kemal Düzkar, chemical engineer / founder of Olivenet Ltd (KKTC). Built EntropyHunter v0.4 (92.7% adjusted accuracy, fine-tuned Qwen3-8B for exergy analysis, published on HuggingFace). Background: thermodynamics, heat transfer, IoT, MES (Accenture/Novartis/Takeda). Not a programmer — an engineer who measures physical reality. Thesis: magnetic nanoparticles/hyperthermia. First IoT project: heat exchanger efficiency via Arduino.

**Previous project:** EntropyHunter — the world's first open-source fine-tuned model for second-law thermodynamic (exergy) analysis. Search past chats for full history: v0.1 through v0.4, taxonomy design, data generation, training, benchmarking, HuggingFace release.

**Relationship to EntropyHunter:** ThermoQA is the natural evolution. EntropyHunter is a model — ThermoQA is the standard by which all models (including EntropyHunter) will be measured. The benchmark infrastructure, scoring methodology, and domain expertise from EntropyHunter directly inform ThermoQA's design.

---

## Motivation & Vision

### Why ThermoQA?
Kemal's core identity is "entropy hunter" — finding thermodynamic inefficiencies via exergy analysis. After building the model (EntropyHunter), the next step is building the measuring stick. ThermoQA serves multiple strategic purposes:

1. **Community standard** — Every new LLM (Qwen3.5, Llama 4, GPT-5) gets evaluated. Kemal's name appears in every comparison. "We evaluated on ThermoQA (Düzkar, 2026)..."
2. **EntropyHunter credibility** — "EntropyHunter scored 92.7% on ThermoQA" is infinitely more meaningful than "92.7% on our internal benchmark"
3. **Academic publication** — arxiv paper: "ThermoQA: A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models"
4. **Olivenet positioning** — Establishes Olivenet as the authority at the intersection of thermodynamics and AI
5. **Personal fulfillment** — Kemal wants the "pioneer" feeling again, the deep technical work, the community contribution. Not just building products — creating standards.

### Kemal's Personal Perspective
> "Bir şeyler yapmak istiyorum ama emin de değilim. EntropyHunter iyi oldu bunun gibi bir şeyler yapasım var sanki teknik derinliği olacak. İlk etapta kullanılmasa bile community için faydalı olabilecek. Entropy exergy termodinamik bu konularda öncü bir fine tuning ve dataset olabilecek şidim."

The desire is for work with **technical depth**, **community value**, and **pioneering nature** — regardless of immediate commercial application. ThermoQA satisfies all three.

---

## Competitive Landscape — Research Results (6 March 2026)

### CRITICAL FINDING: The field is nearly empty.

Only **two dedicated thermodynamics benchmarks** exist in the entire LLM evaluation literature. Combined, they contain **72 problems**. Both focus on idealized physical-chemistry-style questions — neither touches engineering thermodynamics.

### Existing Dedicated Thermodynamics Benchmarks

**1. UTQA (Undergraduate Thermodynamics Question Answering)**
- Authors: Geißler et al., University of Würzburg
- Published: August 2025, arXiv: 2508.21452
- HuggingFace: `herteltm/UTQA`
- Size: **50 single-choice questions**
- Coverage: Ideal-gas processes, entropy concepts, reversibility, PV diagram interpretation
- Best result: GPT-o3 at **82%** (below their 95% competence threshold)
- Key finding: Models struggle with irreversible processes and visual thermodynamic features
- Quote: "existing science benchmarks devote surprisingly little attention to thermodynamic reasoning"
- **Limitations: MCQ format (eliminates process), no engineering applications, no calculations, no property lookups**

**2. Loubet et al.'s Thermodynamic Problem Benchmark**
- Authors: Loubet et al., RPTU Kaiserslautern-Landau
- Published: January 2025, arXiv: 2502.05195
- Size: **22 calculation problems** (13 "simple" + 9 "advanced")
- Coverage: Ideal gas state changes, open/closed systems, coupled systems
- Format: Open numerical solutions, graded by human experts
- Key findings:
  - High inconsistency: std dev ≈ 30-50% of mean score across repeated runs
  - All models incorrectly assumed reversibility when not stated
  - Problems/solutions publicly available on GitLab
- **Limitations: Only 22 problems, ideal gas only, no steam/real fluids, no cycles, no exergy**

### Physics/Science Benchmarks with Minor Thermo Coverage

| Benchmark | Total | Est. Thermo | Format | Engineering? |
|-----------|-------|-------------|--------|-------------|
| SciBench (ICML 2024) | 789 | ~84 | Open-ended | No — physical chemistry |
| UGPhysics (Feb 2025) | 5,520 | ~1,500 | Mixed | No |
| PhysReason (ACL 2025) | 1,200 | ~150-200 | Open-ended | No |
| PHYBench (Apr 2025) | 500 | ~50-80 | Symbolic | No |
| OlympiadBench | 8,952 | ~300-400 | Open-ended | No |
| JEEBench | 515 | ~15-25 | Mixed | Partial |
| ABench-Physics (Jul 2025) | varies | minor | Dynamic | No |
| PHYSICS Dataset (Yale, 2025) | 16,568 | ~3,000 | Mixed | No |

**Pattern:** Thermodynamics appears as **15-20% of physics benchmarks** with no engineering depth.

### Engineering Benchmarks (Emerging, Thermo-Light)

- **EngTrace** (Nov 2025, arXiv: 2511.01650): Symbolic templates, 9 engineering domains. Chemical Engineering branch includes energy balances, Rackett equation. DeepSeek-R1 scored 78.33% on ChemE thermo. **Template-based dynamic generation prevents data contamination — relevant design pattern for ThermoQA.**
- **EngiBench** (Sep 2025): 1,717 hierarchical engineering problems. Chemical & Biological is one of three subfields.
- **CeProBench** (Mar 2025): Chemical process development tasks — closer to process simulation.
- **FE Exam studies**: GPT-4 scored 76% on FE Mechanical (includes thermo), 70.9% on FE Civil. Useful baselines but proprietary content.

### Documented LLM Failure Patterns in Thermodynamics

1. **Multi-step calculation failure** — Engineering equations paper (Jan 2026): LLMs "excel at symbolic tasks — semantic understanding, domain knowledge retrieval, equation formulation — rather than iterative arithmetic." Recommends hybrid architectures.
2. **Inconsistency** — Loubet: std dev 30-50% of mean score. ABench: 22.5% average performance drop when numerical values change.
3. **Reversibility assumption** — Both UTQA and Loubet independently found LLMs default to reversible processes when problem is ambiguous. Dangerous in engineering contexts.
4. **Bloom's Taxonomy decline** — Shahid & Walmsley (MDPI, Feb 2026): ChatGPT ~88% on thermo recall, but **~41% on creative/evaluative tasks**. Knowledge ≠ reasoning.

### Five Critical Gaps (ThermoQA's Territory)

| Gap | What's Missing | Why It Matters |
|-----|---------------|----------------|
| 1. Applied engineering thermo | Rankine, Brayton, VCR, CHP, reheat, regen — zero coverage | Core of professional practice |
| 2. Property lookups | Steam tables, refrigerant tables, CoolProp integration — never tested | Foundation of every calculation |
| 3. Second-law / exergy analysis | Exergy destruction, exergetic efficiency, entropy generation — blank slate | EntropyHunter's domain, most analytically demanding |
| 4. Thermoeconomics | SPECO, exergoeconomic, pinch analysis — zero results | Essential for industrial optimization |
| 5. Industrial scenarios | Under-specified, realistic, judgment-required — completely absent | Where LLMs fail most (88% → 41% recall→eval) |

---

## Architecture & Design Decisions

### Three-Tier Difficulty System

**Tier 1 — Property & Fundamentals (100-120 questions)**
- Single-step, exact-answer problems
- Steam table lookups, phase determination, basic energy/entropy calculation
- Scoring: ±2% tolerance against CoolProp reference values
- Example: "What is the specific enthalpy of superheated steam at 10 bar, 250°C?"
- Purpose: Tests thermodynamic "vocabulary" — does the model know basic properties?

**Tier 2 — Component Analysis (80-100 questions)**
- Single equipment, multi-step (3-6 calculation steps)
- Boiler, turbine, compressor, heat exchanger, pump, valve, mixer
- Exergy destruction, entropy generation, second-law efficiency
- Each intermediate value scored separately
- Example: "Adiabatic turbine: 6 MPa/400°C inlet, 50 kPa outlet, η_s = 85%. Calculate outlet enthalpy, entropy generation, and exergy destruction. T₀ = 25°C."
- Purpose: Tests multi-step thermodynamic reasoning — EntropyHunter territory

**Tier 3 — System & Cycle Analysis (60-80 questions)**
- Full cycles and multi-equipment systems
- Rankine (simple, reheat, regenerative), Brayton, vapor-compression refrigeration, cogeneration
- 8-15 calculation steps, 6+ state points, multiple component balances
- Example: "Reheat Rankine: 12 MPa boiler, 2 MPa reheat, 10 kPa condenser, η_t = 87%, η_p = 82%, 100 MW net. Calculate all state points, cycle efficiency, exergy efficiency, and exergy destruction per component."
- Purpose: Tests sustained engineering reasoning across complex systems

**Bonus Tier — Applied/Industrial (20-30 questions)**
- Real-world scenarios with engineering judgment
- Under-specified inputs, measurement uncertainty, design trade-offs
- More subjective scoring but highly discriminating
- Example: "Flue gas 220°C, ambient 15°C, natural gas 500 Nm³/h — should we add an economizer?"
- Purpose: Tests the recall→evaluation gap (88% → 41% per Shahid & Walmsley)

### Scoring Architecture

Based on EntropyHunter's proven scaffold-based scoring, extended:

1. **Numerical accuracy** — Each intermediate and final value vs CoolProp/reference. ±2% (Tier 1-2), ±5% (Tier 3). Binary pass/fail per value.

2. **Step accuracy** — Inspired by PhysReason's PSAS framework. Each solution step scored independently:
   - Correct formula + correct number = full marks
   - Correct formula + wrong number = partial (arithmetic error)
   - Wrong formula + lucky number = zero (memorization, not reasoning)

3. **Consistency score** — Per Loubet et al.'s finding. Each problem run 3× (temperature 0.7). Report both mean accuracy and standard deviation. A model scoring 80% ± 5% is more trustworthy than 85% ± 25%.

4. **Unit consistency** — EntropyHunter's known weakness. Separate check: t/h vs kg/s, kJ vs J, bar vs kPa. Flagged independently.

5. **Reversibility awareness** — Special check inspired by UTQA/Loubet finding. Problems with ambiguous reversibility are flagged. Model should ask/state assumption, not silently assume reversible.

### Format Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Format | **Open calculation, not MCQ** | MCQ allows elimination; UTQA's MCQ showed models passing without reasoning. Loubet's open format is more discriminating. |
| Language | **English** | Tokenizer efficiency, global community reach. Same decision as EntropyHunter. |
| Primary fluid | **Water/steam (80%+)** | Most reference data, most engineering applications, CoolProp well-validated. Expand to R-134a, R-410A, air later. |
| Ground truth | **CoolProp + cross-reference** | Python/CoolProp computes every reference value. Cross-check against Çengel/Boles tables for wet steam and supercritical edge cases. |
| Anti-contamination | **Parametric templates** | Inspired by EngTrace/ABench. Each problem has a template; parameters randomized per run. Prevents memorization. ABench showed 22.5% performance drop on value-altered variants. |
| Scoring extraction | **Scaffold-based** | EntropyHunter's v0.4 lesson: structured output enables reliable extraction. Define expected scaffold per tier. |

### Ground Truth Generation Strategy

**Key insight from EntropyHunter:** Opus is an excellent teacher but makes arithmetic errors. ThermoQA's ground truth must come from **computation, not LLM generation**.

Pipeline:
```
1. Template defines problem structure and parameter ranges
2. param_sampler.py generates physically valid parameters
3. ground_truth.py computes ALL values via CoolProp (Python, no LLM)
4. solution_generator.py (Opus teacher) writes natural language solution steps
5. CoolProp values cross-check Opus solution → reject mismatches
```

This inverts EntropyHunter's approach: there, Opus generated everything and quality.py validated. Here, **CoolProp generates the truth** and Opus just narrates it. Eliminates the "Opus self-corrects" problem entirely.

---

## Project Structure

```
thermoqa/
├── README.md
├── THERMOQA_HANDOFF.md              # This document
├── .gitignore
│
├── taxonomy/
│   ├── properties.yaml              # Fluids, phases, property types
│   ├── equipment.yaml               # Adapted from EntropyHunter
│   ├── cycles.yaml                  # Rankine, Brayton, VCR, combinations
│   ├── difficulty.yaml              # Tier definitions, step counts
│   └── industrial_scenarios.yaml    # Tier 4 scenario templates
│
├── generation/
│   ├── ground_truth.py              # CoolProp reference solutions
│   ├── templates/                   # Parametric question templates per tier
│   │   ├── tier1_properties/
│   │   ├── tier2_components/
│   │   ├── tier3_cycles/
│   │   └── tier4_industrial/
│   ├── param_sampler.py             # Physics-valid parameter generation
│   ├── solution_generator.py        # Opus teacher (narrative solutions)
│   └── cross_validator.py           # Opus vs CoolProp agreement check
│
├── evaluation/
│   ├── scorer.py                    # Numerical + step + consistency + unit scoring
│   ├── runner.py                    # Ollama / API model execution
│   ├── extractor.py                 # Scaffold-based answer extraction
│   └── report.py                    # Results tables, category breakdown, leaderboard
│
├── data/
│   ├── tier1_properties/            # JSON: question, parameters, reference values
│   ├── tier2_components/
│   ├── tier3_cycles/
│   └── tier4_industrial/
│
├── results/                         # Model-specific benchmark results
│
└── paper/                           # arxiv paper drafts
    └── thermoqa_paper.md
```

---

## Roadmap

### Phase 1 — Tier 1: Property Lookups (2-3 weeks)
- Define property taxonomy: fluids (water/steam initially), phases (subcooled, saturated, superheated, supercritical, wet), properties (h, s, v, u, x, T_sat, P_sat)
- Write parametric templates for 100-120 property lookup questions
- Implement ground_truth.py with CoolProp
- Implement basic scorer.py (±2% numerical matching)
- Implement runner.py (Ollama + API support)
- Run first evaluation: GPT-4, Claude, Qwen3-8B, Llama, Gemini, EntropyHunter
- **Publish on HuggingFace: `olivenet/thermoqa-v0.1`**
- **First community post: "I tested 6 LLMs on basic steam table lookups"**

### Phase 2 — Tier 2: Component Analysis (3-4 weeks)
- Extend taxonomy with equipment types (from EntropyHunter's 7 types, 48 subtypes)
- Write templates for 80-100 component problems (exergy destruction, entropy gen, second law)
- Implement step-level scoring
- Implement consistency scoring (3 runs per problem)
- Extend extractor.py for multi-step scaffold parsing
- Run full Tier 1+2 evaluation
- **Update HuggingFace dataset**

### Phase 3 — Tier 3: Cycle Analysis (4-6 weeks)
- Cycle taxonomy: Rankine variants, Brayton variants, VCR, cogeneration
- Template design for 60-80 cycle problems (6+ state points each)
- Ground truth: full cycle CoolProp scripts
- This is the hardest part — each cycle problem generates 40+ intermediate values
- Run full Tier 1+2+3 evaluation
- **Major community post with leaderboard**

### Phase 4 — Publication (2-3 weeks)
- Tier 4 industrial scenarios (20-30, more subjective)
- Final leaderboard across all tiers
- Write arxiv paper: "ThermoQA: A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models"
- **Full HuggingFace release: `olivenet/thermoqa`**
- Community engagement: r/LocalLLaMA, r/ChemicalEngineering, HuggingFace, LinkedIn

### Total estimated timeline: 3-4 months (part-time)

---

## Lessons from EntropyHunter to Apply

| EntropyHunter Lesson | ThermoQA Application |
|---------------------|---------------------|
| JSON blocks as reasoning scaffold | Define expected output scaffolds per tier |
| 10 tests misleading, 40 tests real | ThermoQA must be large enough (300+) to be statistically significant |
| Temperature 0.7 optimal for calculations | Use same; include consistency measurement |
| Opus self-corrects → grab LAST values | Avoid by using CoolProp as ground truth, not LLM |
| num_ctx truncation mimics poor quality | Ensure problems fit context window; measure truncation |
| Balance-line is gold (self-verified) | Design scaffold so models self-verify (energy balance check) |
| Unit conversion is persistent weakness | Include as separate scoring dimension |
| 8B models can't learn JSON from SFT | Scoring must handle varied output formats |
| Benchmark-first development | Build evaluation infrastructure before any training |

---

## Relationship to Broader Olivenet Strategy

ThermoQA exists within a larger vision:

**EntropyHunter** — The model (fine-tuned Qwen3-8B for exergy analysis)
**ThermoQA** — The benchmark (measuring stick for all models)
**ExergyLab** — The calculation engine (36K lines, 7 analysis engines)
**CoolProp Agent** — The property oracle (tool-use for accurate steam properties)
**Debimetre Project** — The measurement hardware (MSP430FR6047, clamp-on flow)
**Energy Audit Pipeline** — The commercial product (sensors → analysis → AI report)

ThermoQA strengthens every other piece:
- Validates EntropyHunter improvements objectively
- Establishes Olivenet's authority in the field
- Creates community engagement that feeds back to all projects
- Provides arxiv publication for academic credibility
- Generates HuggingFace visibility for the Olivenet brand

---

## Technical Notes

### CoolProp Usage
```python
from CoolProp.CoolProp import PropsSI

# Superheated steam: T and P known
h = PropsSI('H', 'T', 273.15+200, 'P', 10e5, 'Water')  # J/kg
s = PropsSI('S', 'T', 273.15+200, 'P', 10e5, 'Water')  # J/(kg·K)

# Saturated: quality and P known
h_sat_vapor = PropsSI('H', 'P', 10e5, 'Q', 1, 'Water')
T_sat = PropsSI('T', 'P', 10e5, 'Q', 0, 'Water')        # K

# Watch out: CoolProp returns SI (J, K, Pa). Convert to kJ, °C, kPa/bar for engineering use.
```

### Dead State Reference
```python
DEAD_STATE = {
    "T0_K": 298.15,    # 25°C
    "T0_C": 25.0,
    "P0_Pa": 101325,   # 1 atm
    "P0_kPa": 101.325,
    "h0": PropsSI('H', 'T', 298.15, 'P', 101325, 'Water'),  # ~104.9 kJ/kg
    "s0": PropsSI('S', 'T', 298.15, 'P', 101325, 'Water'),  # ~0.367 kJ/(kg·K)
}
```

### Exergy of a Stream
```python
def specific_exergy(h, s, h0, s0, T0=298.15):
    """Specific flow exergy in kJ/kg"""
    return (h - h0) - T0 * (s - s0)  # Ensure consistent units (kJ)
```

---

## Key References

### Directly Relevant
- UTQA: arXiv:2508.21452, HuggingFace: `herteltm/UTQA`
- Loubet et al.: arXiv:2502.05195 (GitLab has problems/solutions)
- EngTrace: arXiv:2511.01650 (template-based dynamic generation pattern)
- ABench-Physics: arXiv:2507.04766 (22.5% drop on value alteration)
- Shahid & Walmsley: MDPI Information (Feb 2026) — Bloom's taxonomy in ChemE

### Background Physics Benchmarks
- SciBench: arXiv:2307.10635 (ICML 2024)
- UGPhysics: arXiv:2502.00334
- PhysReason: arXiv:2502.12054 (PSAS step-level scoring)
- PHYBench: arXiv:2504.16074 (Expression Edit Distance metric)

### Engineering Benchmarks
- EngiBench: arXiv:2509.17677
- CeProBench: arXiv:2603.01654
- Engineering equations: arXiv:2601.01774 (hybrid LLM+solver recommendation)

### EntropyHunter (Predecessor)
- Model: `olivenet/entropy-hunter-8b-gguf` on HuggingFace
- Dataset preview: `olivenet/entropy-hunter-dataset-preview`
- Full handoff: ENTROPY_HUNTER_HANDOFF.md (separate document)

---

## Open Questions for First Session

1. **Tier 1 taxonomy scope** — Start with water/steam only, or include ideal gas from day 1?
2. **Template format** — YAML? JSON? Python dataclasses? Need to decide on the template structure before writing 100+ templates.
3. **Scoring tolerance** — ±2% for Tier 1 reasonable? Should it be absolute (±5 kJ/kg) or relative?
4. **HuggingFace dataset format** — Follow UTQA's MCQ format for comparability, or use our own open-calculation format?
5. **Evaluation script** — Ship as Python package? Or just scripts in repo?
6. **EntropyHunter integration** — Include EntropyHunter as one of the evaluated models from v0.1? (Yes — shows continuity and gives immediate benchmark result.)
