# ThermoQA Comprehensive Analysis Report

**Generated**: 2026-03-17 10:01 UTC

**Dataset**: 293 questions across 3 tiers (110 T1 + 101 T2 + 82 T3)

**Models**: Claude Opus 4.6, GPT-5.4, Gemini 2.5 Pro, Grok 4, DeepSeek R1, MiniMax M1

**Runs**: 3 independent evaluations per model

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Per-Tier Leaderboards](#2-per-tier-leaderboards)
   - 2.1 [Tier 1: Property Lookups](#21-tier-1-property-lookups-110-questions)
   - 2.2 [Tier 2: Component Analysis](#22-tier-2-component-analysis-101-questions)
   - 2.3 [Tier 3: Cycle Analysis](#23-tier-3-cycle-analysis-82-questions)
3. [Cross-Tier Analysis](#3-cross-tier-analysis)
4. [Multi-Run Consistency](#4-multi-run-consistency-analysis)
5. [Discriminator Analysis](#5-discriminator-analysis)
6. [Error Pattern Analysis](#6-error-pattern-analysis)
7. [Token Efficiency](#7-token-efficiency)
8. [Grok 4 Analysis](#8-grok-4-analysis)
9. [Extraction Methodology](#9-extraction-methodology--reliability)
10. [Statistical Significance](#10-statistical-significance)
11. [Recommendations](#11-recommendations)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

### Overall Leaderboard

| Rank | Model           | Tier 1    | Tier 2    | Tier 3    | Composite |
| :--: | --------------- | --------: | --------: | --------: | --------: |
| 1    | Claude Opus 4.6 | 96.4±0.9% | 92.1±0.1% | 93.6±0.5% | 94.1±0.2% |
| 2    | GPT-5.4         | 97.8±0.8% | 90.8±0.5% | 89.7±0.1% | 93.1±0.2% |
| 3    | Gemini 2.5 Pro  | 97.9±0.5% | 90.8±1.2% | 87.5±1.5% | 92.5±1.0% |
| 4    | DeepSeek R1     | 90.5±0.1% | 89.2±2.5% | 81.0±2.2% | 87.4±0.5% |
| 5    | Grok 4          | 91.8±1.2% | 87.9±0.7% | 80.4±0.8% | 87.3±0.3% |
| 6    | MiniMax M1      | 85.2±0.6% | 76.2±1.1% | 52.7±1.5% | 73.0±0.6% |

### Key Findings

1. **Claude Opus 4.6** leads the benchmark with a composite score of 94.1%, demonstrating the strongest overall thermodynamic reasoning.

2. **Performance spread is 21.1%** between the top and bottom models, confirming that thermodynamic reasoning is a meaningful differentiator.

3. **MiniMax M1 degrades 38.2% from Tier 1→3**, showing the largest gap between property lookup and cycle analysis.

4. **Multi-run consistency varies 10×**: GPT-5.4 (σ=0.1%) vs DeepSeek R1 (σ=2.2%) on Tier 3.

5. **Supercritical water** is the most discriminating Tier 1 category: GPT-5.4 scores 89.5% vs MiniMax M1 at 45.0%.


---

## 2. Per-Tier Leaderboards

### 2.1 Tier 1: Property Lookups (110 questions)

#### Leaderboard

| Rank | Model           | Score     | Property Acc. |
| :--: | --------------- | --------: | ------------: |
| 1    | Gemini 2.5 Pro  | 97.9±0.5% | 96.1±1.1%     |
| 2    | GPT-5.4         | 97.8±0.8% | 97.2±0.9%     |
| 3    | Claude Opus 4.6 | 96.4±0.9% | 94.5±1.0%     |
| 4    | Grok 4          | 91.8±1.2% | 89.8±0.5%     |
| 5    | DeepSeek R1     | 90.5±0.1% | 87.5±0.2%     |
| 6    | MiniMax M1      | 85.2±0.6% | 81.6±1.7%     |

#### By Category

| Model    | Subcooled | Sat. Liq. | Wet Steam | Sat. Vap. | Superheat. | Supercrit. | Phase Det. | Inverse |
| -------- | --------: | --------: | --------: | --------: | ---------: | ---------: | ---------: | ------: |
| Gemini   | 100.0%    | 100.0%    | 100.0%    | 100.0%    | 99.4%      | 77.8%      | 100.0%     | 100.0%  |
| GPT-5.4  | 100.0%    | 100.0%    | 100.0%    | 100.0%    | 99.4%      | 89.5%      | 100.0%     | 91.7%   |
| Opus     | 100.0%    | 100.0%    | 99.4%     | 100.0%    | 98.9%      | 70.5%      | 95.5%      | 100.0%  |
| Grok 4   | 100.0%    | 100.0%    | 100.0%    | 100.0%    | 99.4%      | 52.8%      | 82.2%      | 90.0%   |
| DeepSeek | 100.0%    | 100.0%    | 94.5%     | 99.2%     | 92.2%      | 48.9%      | 88.9%      | 93.3%   |
| MiniMax  | 93.3%     | 87.5%     | 92.0%     | 95.8%     | 85.8%      | 45.0%      | 97.8%      | 75.9%   |

#### By Difficulty

| Model    | Easy   | Medium | Hard  |
| -------- | -----: | -----: | ----: |
| Gemini   | 100.0% | 99.6%  | 92.1% |
| GPT-5.4  | 100.0% | 95.7%  | 95.9% |
| Opus     | 98.7%  | 98.9%  | 89.5% |
| Grok 4   | 97.9%  | 95.0%  | 77.2% |
| DeepSeek | 98.1%  | 93.2%  | 73.6% |
| MiniMax  | 92.3%  | 85.7%  | 71.4% |

#### Supercritical Spotlight

The supercritical category (10 questions) is the single most discriminating subset in Tier 1.

| Model           | Score | σ    |
| --------------- | ----: | ---: |
| GPT-5.4         | 89.5% | 2.5% |
| Gemini 2.5 Pro  | 77.8% | 3.9% |
| Claude Opus 4.6 | 70.5% | 3.9% |
| Grok 4          | 52.8% | 6.3% |
| DeepSeek R1     | 48.9% | 1.0% |
| MiniMax M1      | 45.0% | 4.4% |

### 2.2 Tier 2: Component Analysis (101 questions)

#### Leaderboard

| Rank | Model           | Score     | Property Acc. |
| :--: | --------------- | --------: | ------------: |
| 1    | Claude Opus 4.6 | 92.1±0.1% | 91.6±0.6%     |
| 2    | GPT-5.4         | 90.8±0.5% | 90.4±0.4%     |
| 3    | Gemini 2.5 Pro  | 90.8±1.2% | 89.1±0.9%     |
| 4    | DeepSeek R1     | 89.2±2.5% | 89.9±2.0%     |
| 5    | Grok 4          | 87.9±0.7% | 87.9±0.4%     |
| 6    | MiniMax M1      | 76.2±1.1% | 79.5±0.9%     |

#### By Component

| Model    | Turbine | Compr. | Pump   | HX    | Boiler | Mixer | Nozzle |
| -------- | ------: | -----: | -----: | ----: | -----: | ----: | -----: |
| Opus     | 96.9%   | 75.4%  | 100.0% | 90.0% | 98.8%  | 91.5% | 93.4%  |
| GPT-5.4  | 90.8%   | 71.2%  | 100.0% | 84.8% | 99.1%  | 99.0% | 96.6%  |
| Gemini   | 94.4%   | 66.3%  | 100.0% | 89.1% | 98.5%  | 98.6% | 91.7%  |
| DeepSeek | 91.9%   | 67.2%  | 98.5%  | 91.3% | 97.8%  | 96.6% | 83.6%  |
| Grok 4   | 90.0%   | 64.8%  | 99.0%  | 85.5% | 93.8%  | 98.1% | 89.1%  |
| MiniMax  | 70.1%   | 55.5%  | 97.5%  | 87.6% | 71.3%  | 88.5% | 68.3%  |

#### By Fluid

| Model    | Water | Air   | R134a |
| -------- | ----: | ----: | ----: |
| Opus     | 96.8% | 94.0% | 54.0% |
| GPT-5.4  | 95.6% | 93.6% | 50.4% |
| Gemini   | 98.2% | 84.0% | 47.6% |
| DeepSeek | 92.0% | 92.4% | 63.4% |
| Grok 4   | 93.8% | 88.3% | 44.0% |
| MiniMax  | 74.5% | 96.2% | 54.2% |

#### By Depth

| Model    | Depth A | Depth B | Depth C |
| -------- | ------: | ------: | ------: |
| Opus     | 90.0%   | 90.8%   | 96.1%   |
| GPT-5.4  | 88.2%   | 90.8%   | 93.8%   |
| Gemini   | 90.1%   | 89.5%   | 93.0%   |
| DeepSeek | 86.2%   | 88.8%   | 93.4%   |
| Grok 4   | 82.2%   | 88.3%   | 94.3%   |
| MiniMax  | 71.9%   | 78.7%   | 78.3%   |

### 2.3 Tier 3: Cycle Analysis (82 questions)

#### Leaderboard

| Rank | Model           | Score     | Property Acc. |
| :--: | --------------- | --------: | ------------: |
| 1    | Claude Opus 4.6 | 93.6±0.5% | 92.8±0.6%     |
| 2    | GPT-5.4         | 89.7±0.1% | 88.7±0.5%     |
| 3    | Gemini 2.5 Pro  | 87.5±1.5% | 87.8±1.4%     |
| 4    | DeepSeek R1     | 81.0±2.2% | 84.4±2.2%     |
| 5    | Grok 4          | 80.4±0.8% | 79.5±1.0%     |
| 6    | MiniMax M1      | 52.7±1.5% | 55.1±1.5%     |

#### By Cycle Group

| Model    | RNK   | BRY   | VCR   | CCGT  |
| -------- | ----: | ----: | ----: | ----: |
| Opus     | 95.9% | 99.2% | 81.6% | 90.1% |
| GPT-5.4  | 92.1% | 97.8% | 76.6% | 82.0% |
| Gemini   | 95.2% | 84.2% | 90.9% | 74.0% |
| DeepSeek | 86.0% | 87.7% | 66.8% | 72.2% |
| Grok 4   | 90.9% | 83.2% | 73.6% | 58.6% |
| MiniMax  | 52.3% | 72.8% | 32.5% | 31.8% |

#### Detailed Cycle Subtype Breakdown (10 subtypes)

| Model    | RNK-I  | RNK-A | RNK-RH | BRY-I  | BRY-A  | BRY-RG | BRY-AV | BRY-RV | VCR-A | CCGT  |
| -------- | -----: | ----: | -----: | -----: | -----: | -----: | -----: | -----: | ----: | ----: |
| Opus     | 99.3%  | 99.8% | 89.5%  | 100.0% | 99.9%  | 99.6%  | 97.4%  | 98.9%  | 81.6% | 90.1% |
| GPT-5.4  | 90.4%  | 97.5% | 84.3%  | 99.1%  | 100.0% | 100.0% | 96.8%  | 90.3%  | 76.6% | 82.0% |
| Gemini   | 100.0% | 99.7% | 87.5%  | 96.7%  | 97.2%  | 96.7%  | 69.7%  | 48.4%  | 90.9% | 74.0% |
| DeepSeek | 95.7%  | 89.8% | 78.4%  | 98.5%  | 99.2%  | 99.5%  | 76.7%  | 52.5%  | 66.8% | 72.2% |
| Grok 4   | 90.4%  | 96.6% | 82.5%  | 97.5%  | 96.8%  | 96.7%  | 54.9%  | 63.8%  | 73.6% | 58.6% |
| MiniMax  | 61.7%  | 59.1% | 40.2%  | 100.0% | 99.1%  | 89.5%  | 27.8%  | 35.8%  | 32.5% | 31.8% |

#### By Fluid

| Model    | Water | Air   | R-134a | Air+Water |
| -------- | ----: | ----: | -----: | --------: |
| Opus     | 95.9% | 99.2% | 81.6%  | 90.1%     |
| GPT-5.4  | 92.1% | 97.8% | 76.6%  | 82.0%     |
| Gemini   | 95.2% | 84.2% | 90.9%  | 74.0%     |
| DeepSeek | 86.0% | 87.7% | 66.8%  | 72.2%     |
| Grok 4   | 90.9% | 83.2% | 73.6%  | 58.6%     |
| MiniMax  | 52.3% | 72.8% | 32.5%  | 31.8%     |

#### By Depth

| Model    | Depth A | Depth B | Depth C |
| -------- | ------: | ------: | ------: |
| Opus     | 93.5%   | 96.1%   | 91.1%   |
| GPT-5.4  | 90.8%   | 92.4%   | 86.1%   |
| Gemini   | 84.4%   | 92.2%   | 86.4%   |
| DeepSeek | 76.0%   | 86.9%   | 80.8%   |
| Grok 4   | 80.1%   | 81.9%   | 79.2%   |
| MiniMax  | 44.6%   | 64.7%   | 49.8%   |

---

## 3. Cross-Tier Analysis

### 3.1 Tier Degradation

How much does each model degrade from property lookups (T1) to full cycle analysis (T3)?

| Model           | T1 Score | T3 Score | Absolute Drop | Relative Drop |
| --------------- | -------: | -------: | ------------: | ------------: |
| MiniMax M1      | 85.2%    | 52.7%    | 32.5%         | 38.2%         |
| Grok 4          | 91.8%    | 80.4%    | 11.5%         | 12.5%         |
| Gemini 2.5 Pro  | 97.9%    | 87.5%    | 10.3%         | 10.6%         |
| DeepSeek R1     | 90.5%    | 81.0%    | 9.5%          | 10.5%         |
| GPT-5.4         | 97.8%    | 89.7%    | 8.1%          | 8.2%          |
| Claude Opus 4.6 | 96.4%    | 93.6%    | 2.8%          | 3.0%          |

### 3.2 Ranking Instability

Model rank at each tier — ranking shifts reveal where different capabilities matter.

| Model           | T1 Rank | T2 Rank | T3 Rank | Max Δ |
| --------------- | :-----: | :-----: | :-----: | :---: |
| Claude Opus 4.6 | 3       | 1       | 1       | 2     |
| Gemini 2.5 Pro  | 1       | 3       | 3       | 2     |
| Grok 4          | 4       | 5       | 5       | 1     |
| DeepSeek R1     | 5       | 4       | 4       | 1     |
| GPT-5.4         | 2       | 2       | 2       | 0     |
| MiniMax M1      | 6       | 6       | 6       | 0     |

### 3.3 Skill Decomposition

Each tier tests a different skill:
- **Tier 1** = Memorization (property lookup from training data)
- **Tier 2** = Chaining (multi-step component calculations)
- **Tier 3** = Reasoning (full cycle analysis with coupled equations)

| Model           | Memorization (T1) | Chaining (T2) | Reasoning (T3) | Best Skill   |
| --------------- | ----------------: | ------------: | -------------: | ------------ |
| Claude Opus 4.6 | 96.4%             | 92.1%         | 93.6%          | Memorization |
| GPT-5.4         | 97.8%             | 90.8%         | 89.7%          | Memorization |
| Gemini 2.5 Pro  | 97.9%             | 90.8%         | 87.5%          | Memorization |
| Grok 4          | 91.8%             | 87.9%         | 80.4%          | Memorization |
| DeepSeek R1     | 90.5%             | 89.2%         | 81.0%          | Memorization |
| MiniMax M1      | 85.2%             | 76.2%         | 52.7%          | Memorization |

---

## 4. Multi-Run Consistency Analysis

Each model was evaluated 3 times. This section analyzes score stability.

### 4.1 Run-to-Run Variability (σ)

| Model           | T1 σ | T2 σ | T3 σ | Mean σ |
| --------------- | ---: | ---: | ---: | -----: |
| Claude Opus 4.6 | 0.9% | 0.1% | 0.5% | 0.5%   |
| GPT-5.4         | 0.8% | 0.5% | 0.1% | 0.5%   |
| Grok 4          | 1.2% | 0.7% | 0.8% | 0.9%   |
| MiniMax M1      | 0.6% | 1.1% | 1.5% | 1.0%   |
| Gemini 2.5 Pro  | 0.5% | 1.2% | 1.5% | 1.1%   |
| DeepSeek R1     | 0.1% | 2.5% | 2.2% | 1.6%   |

### 4.2 Question-Level Volatility

For each (question, model) pair across 3 runs, we classify as:
- **Always Correct**: all 3 runs score ≥ 0.99
- **Always Wrong**: all 3 runs score < 0.01
- **Volatile**: mixed results across runs

#### Tier 1

| Model    | Always Correct | Always Wrong | Volatile | Volatility Rate |
| -------- | -------------: | -----------: | -------: | --------------: |
| Opus     | 99             | 0            | 11       | 10.0%           |
| Gemini   | 99             | 0            | 11       | 10.0%           |
| GPT-5.4  | 98             | 0            | 12       | 10.9%           |
| Grok 4   | 90             | 1            | 19       | 17.3%           |
| DeepSeek | 82             | 0            | 28       | 25.5%           |
| MiniMax  | 62             | 0            | 48       | 43.6%           |

#### Tier 2

| Model    | Always Correct | Always Wrong | Volatile | Volatility Rate |
| -------- | -------------: | -----------: | -------: | --------------: |
| Opus     | 66             | 1            | 34       | 33.7%           |
| GPT-5.4  | 59             | 1            | 41       | 40.6%           |
| Gemini   | 59             | 0            | 42       | 41.6%           |
| Grok 4   | 46             | 2            | 53       | 52.5%           |
| DeepSeek | 48             | 0            | 53       | 52.5%           |
| MiniMax  | 26             | 0            | 75       | 74.3%           |

#### Tier 3

| Model    | Always Correct | Always Wrong | Volatile | Volatility Rate |
| -------- | -------------: | -----------: | -------: | --------------: |
| Opus     | 37             | 0            | 45       | 54.9%           |
| GPT-5.4  | 32             | 0            | 50       | 61.0%           |
| Gemini   | 31             | 0            | 51       | 62.2%           |
| Grok 4   | 20             | 0            | 62       | 75.6%           |
| DeepSeek | 20             | 0            | 62       | 75.6%           |
| MiniMax  | 12             | 0            | 70       | 85.4%           |

### 4.3 Universally Volatile Questions

Questions that are volatile (inconsistent across runs) for 3 or more models:

#### Tier 1: 16 questions volatile for 3+ models

| Question ID | # Models Volatile | Category/Type     |
| ----------- | :---------------: | ----------------- |
| T1-SC-001   | 6                 | supercritical     |
| T1-SC-002   | 6                 | supercritical     |
| T1-SC-006   | 6                 | supercritical     |
| T1-SC-007   | 6                 | supercritical     |
| T1-SC-008   | 6                 | supercritical     |
| T1-SC-009   | 6                 | supercritical     |
| T1-SC-010   | 6                 | supercritical     |
| T1-SC-005   | 5                 | supercritical     |
| T1-SH-018   | 4                 | superheated_vapor |
| T1-SC-004   | 4                 | supercritical     |
| T1-IL-006   | 4                 | inverse_lookups   |
| T1-IL-007   | 4                 | inverse_lookups   |
| T1-SH-007   | 3                 | superheated_vapor |
| T1-SH-017   | 3                 | superheated_vapor |
| T1-SC-003   | 3                 | supercritical     |
| T1-IL-002   | 3                 | inverse_lookups   |

#### Tier 2: 55 questions volatile for 3+ models

| Question ID   | # Models Volatile | Category/Type  |
| ------------- | :---------------: | -------------- |
| T2-CMP-BR-001 | 6                 | compressor     |
| T2-CMP-BR-002 | 6                 | compressor     |
| T2-HX-AW-003  | 6                 | heat_exchanger |
| T2-HX-CW-003  | 6                 | heat_exchanger |
| T2-HX-AR-001  | 6                 | heat_exchanger |
| T2-HX-AR-002  | 6                 | heat_exchanger |
| T2-HX-BR-001  | 6                 | heat_exchanger |
| T2-HX-BR-002  | 6                 | heat_exchanger |
| T2-HX-CR-001  | 6                 | heat_exchanger |
| T2-HX-CR-002  | 6                 | heat_exchanger |
| T2-MIX-CW-001 | 6                 | mixing_chamber |
| T2-MIX-CW-003 | 6                 | mixing_chamber |
| T2-NOZ-BA-001 | 6                 | nozzle         |
| T2-NOZ-BA-002 | 6                 | nozzle         |
| T2-TRB-AW-003 | 5                 | turbine        |
| T2-TRB-AA-001 | 5                 | turbine        |
| T2-TRB-BA-001 | 5                 | turbine        |
| T2-CMP-AW-001 | 5                 | compressor     |
| T2-CMP-AW-002 | 5                 | compressor     |
| T2-CMP-CW-001 | 5                 | compressor     |

#### Tier 3: 64 questions volatile for 3+ models

| Question ID        | # Models Volatile | Category/Type |
| ------------------ | :---------------: | ------------- |
| T3-RNK-A-WA-C-003  | 6                 | RNK-A         |
| T3-RNK-RH-WA-A-002 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-A-003 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-B-001 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-B-002 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-B-003 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-C-001 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-C-002 | 6                 | RNK-RH        |
| T3-RNK-RH-WA-C-003 | 6                 | RNK-RH        |
| T3-VCR-A-RF-A-001  | 6                 | VCR-A         |
| T3-VCR-A-RF-A-003  | 6                 | VCR-A         |
| T3-VCR-A-RF-A-004  | 6                 | VCR-A         |
| T3-VCR-A-RF-A-005  | 6                 | VCR-A         |
| T3-VCR-A-RF-C-001  | 6                 | VCR-A         |
| T3-VCR-A-RF-C-002  | 6                 | VCR-A         |
| T3-VCR-A-RF-C-003  | 6                 | VCR-A         |
| T3-VCR-A-RF-C-004  | 6                 | VCR-A         |
| T3-VCR-A-RF-C-005  | 6                 | VCR-A         |
| T3-BRY-AV-AR-B-002 | 6                 | BRY-AV        |
| T3-BRY-AV-AR-C-002 | 6                 | BRY-AV        |

### 4.4 Volatility vs Difficulty

Volatile question rate by difficulty level (averaged across models):

#### Tier 1

| Difficulty | Total (q×model) | Volatile | Rate  |
| ---------- | --------------: | -------: | ----: |
| Easy       | 312             | 25       | 8.0%  |
| Medium     | 180             | 32       | 17.8% |
| Hard       | 168             | 72       | 42.9% |

#### Tier 2

| Difficulty | Total (q×model) | Volatile | Rate  |
| ---------- | --------------: | -------: | ----: |
| Easy       | 204             | 95       | 46.6% |
| Medium     | 222             | 106      | 47.7% |
| Hard       | 180             | 97       | 53.9% |

#### Tier 3

| Difficulty | Total (q×model) | Volatile | Rate  |
| ---------- | --------------: | -------: | ----: |
| Easy       | 90              | 39       | 43.3% |
| Medium     | 156             | 95       | 60.9% |
| Hard       | 246             | 206      | 83.7% |


---

## 5. Discriminator Analysis

Which question subsets best separate model capabilities?

### 5.1 Tier 1: Supercritical Region

Supercritical water properties (T > 373.95°C, P > 22.064 MPa) — requires knowledge beyond standard steam tables.

| Model           | Supercritical Score | Overall T1 Score | Gap   |
| --------------- | ------------------: | ---------------: | ----: |
| GPT-5.4         | 89.5%               | 97.8%            | 8.4%  |
| Gemini 2.5 Pro  | 77.8%               | 97.9%            | 20.1% |
| Claude Opus 4.6 | 70.5%               | 96.4%            | 25.9% |
| Grok 4          | 52.8%               | 91.8%            | 39.0% |
| DeepSeek R1     | 48.9%               | 90.5%            | 41.6% |
| MiniMax M1      | 45.0%               | 85.2%            | 40.2% |

### 5.2 Tier 2: R-134a Refrigerant

R-134a questions test whether models can handle non-water fluids.

| Model           | R-134a Score | Water Score | Gap   |
| --------------- | -----------: | ----------: | ----: |
| DeepSeek R1     | 63.4%        | 92.0%       | 28.6% |
| MiniMax M1      | 54.2%        | 74.5%       | 20.3% |
| Claude Opus 4.6 | 54.0%        | 96.8%       | 42.7% |
| GPT-5.4         | 50.4%        | 95.6%       | 45.2% |
| Gemini 2.5 Pro  | 47.6%        | 98.2%       | 50.6% |
| Grok 4          | 44.0%        | 93.8%       | 49.8% |

### 5.3 Tier 2: Compressor Component

Compressors involve isentropic efficiency with different fluid types.

| Model           | Compressor Score | Overall T2 Score | Gap   |
| --------------- | ---------------: | ---------------: | ----: |
| Claude Opus 4.6 | 75.4%            | 92.1%            | 16.6% |
| GPT-5.4         | 71.2%            | 90.8%            | 19.6% |
| DeepSeek R1     | 67.2%            | 89.2%            | 22.0% |
| Gemini 2.5 Pro  | 66.3%            | 90.8%            | 24.5% |
| Grok 4          | 64.8%            | 87.9%            | 23.1% |
| MiniMax M1      | 55.5%            | 76.2%            | 20.7% |

### 5.4 Tier 3: Hard Cycle Variants

BRY-AV (aftercooling, variable-cp), BRY-RV (regenerative, variable-cp), and CCGT (combined cycle) are the hardest T3 subtypes.

| Model           | BRY-AV | BRY-RV | CCGT  | Mean Hard |
| --------------- | -----: | -----: | ----: | --------: |
| Claude Opus 4.6 | 97.4%  | 98.9%  | 90.1% | 93.7%     |
| GPT-5.4         | 96.8%  | 90.3%  | 82.0% | 87.5%     |
| DeepSeek R1     | 76.7%  | 52.5%  | 72.2% | 69.9%     |
| Gemini 2.5 Pro  | 69.7%  | 48.4%  | 74.0% | 68.2%     |
| Grok 4          | 54.9%  | 63.8%  | 58.6% | 58.6%     |
| MiniMax M1      | 27.8%  | 35.8%  | 31.8% | 31.4%     |

### 5.5 Discriminator Progression: Cross-Model Variance by Tier

Variance of model means increases from T1→T3, confirming progressive difficulty.

| Tier   | Model Score Range | Variance | Questions |
| ------ | ----------------: | -------: | --------: |
| Tier 1 | 12.7%             | 0.002534 | 110       |
| Tier 2 | 15.9%             | 0.003461 | 101       |
| Tier 3 | 40.9%             | 0.021586 | 82        |

---

## 6. Error Pattern Analysis

### 6.1 Error Type Distribution

From `scores` array `error_type` field (per-property level, averaged across runs):

#### Tier 1

| Model    | Correct     | Out Of Tolerance | Extraction Failed | Missing    | Total Steps |
| -------- | ----------: | ---------------: | ----------------: | ---------: | ----------: |
| Opus     | 274 (94.5%) | 0 (0.0%)         | 0 (0.0%)          | 16 (5.5%)  | 290         |
| GPT-5.4  | 282 (97.2%) | 0 (0.0%)         | 0 (0.0%)          | 8 (2.8%)   | 290         |
| Gemini   | 279 (96.1%) | 0 (0.0%)         | 0 (0.0%)          | 11 (3.9%)  | 290         |
| Grok 4   | 260 (89.8%) | 0 (0.0%)         | 0 (0.0%)          | 30 (10.2%) | 290         |
| DeepSeek | 254 (87.5%) | 0 (0.0%)         | 0 (0.0%)          | 36 (12.5%) | 290         |
| MiniMax  | 237 (81.6%) | 0 (0.0%)         | 0 (0.0%)          | 53 (18.4%) | 290         |

#### Tier 2

| Model    | Correct     | Out Of Tolerance | Extraction Failed | Missing     | Total Steps |
| -------- | ----------: | ---------------: | ----------------: | ----------: | ----------: |
| Opus     | 685 (91.6%) | 0 (0.0%)         | 0 (0.0%)          | 63 (8.4%)   | 748         |
| GPT-5.4  | 676 (90.4%) | 0 (0.0%)         | 0 (0.0%)          | 72 (9.6%)   | 748         |
| Gemini   | 666 (89.1%) | 0 (0.0%)         | 0 (0.0%)          | 82 (10.9%)  | 748         |
| Grok 4   | 657 (87.9%) | 0 (0.0%)         | 0 (0.0%)          | 91 (12.1%)  | 748         |
| DeepSeek | 673 (89.9%) | 0 (0.0%)         | 0 (0.0%)          | 75 (10.1%)  | 748         |
| MiniMax  | 594 (79.5%) | 0 (0.0%)         | 0 (0.0%)          | 154 (20.5%) | 748         |

#### Tier 3

| Model    | Correct      | Out Of Tolerance | Extraction Failed | Missing     | Total Steps |
| -------- | -----------: | ---------------: | ----------------: | ----------: | ----------: |
| Opus     | 1974 (92.8%) | 0 (0.0%)         | 0 (0.0%)          | 153 (7.2%)  | 2127        |
| GPT-5.4  | 1886 (88.7%) | 0 (0.0%)         | 0 (0.0%)          | 241 (11.3%) | 2127        |
| Gemini   | 1868 (87.8%) | 0 (0.0%)         | 0 (0.0%)          | 259 (12.2%) | 2127        |
| Grok 4   | 1691 (79.5%) | 0 (0.0%)         | 0 (0.0%)          | 436 (20.5%) | 2127        |
| DeepSeek | 1794 (84.3%) | 0 (0.0%)         | 0 (0.0%)          | 333 (15.7%) | 2127        |
| MiniMax  | 1173 (55.1%) | 0 (0.0%)         | 0 (0.0%)          | 954 (44.9%) | 2127        |

### 6.2 Error Propagation (Step-Pair Correlation)

Do early-step failures cause late-step failures? Phi coefficient for adjacent step pairs:

#### Tier 2

| Step Pair           | φ Coefficient | Co-failures | Total |
| ------------------- | ------------: | ----------: | ----: |
| s_c_in → s_c_out    | 1.000         | 54          | 216   |
| h2s → h2            | 0.937         | 106         | 756   |
| h_out → q_in        | 0.929         | 21          | 252   |
| s_out → s_gen       | 0.814         | 2           | 180   |
| h2 → w_in           | 0.764         | 79          | 432   |
| h2s → V2            | 0.675         | 25          | 252   |
| V2 → h2             | 0.675         | 25          | 252   |
| h3 → T3             | 0.664         | 3           | 216   |
| T3 → s1             | 0.660         | 3           | 144   |
| X_dest_dot → eta_II | 0.553         | 40          | 180   |
| s3 → S_gen_dot      | 0.484         | 3           | 144   |
| h2 → w_out          | 0.407         | 18          | 324   |
| x_dest → eta_II     | 0.383         | 22          | 360   |
| h1 → s1             | 0.370         | 54          | 1008  |
| w_in → s2           | 0.331         | 26          | 270   |

#### Tier 3

| Step Pair                   | φ Coefficient | Co-failures | Total |
| --------------------------- | ------------: | ----------: | ----: |
| h1 → h2                     | 1.000         | 3           | 90    |
| s_gen_HPT → s_gen_reheater  | 1.000         | 3           | 108   |
| s_gen_comp → s_gen_regen    | 1.000         | 1           | 108   |
| s_gen_regen → s_gen_cc      | 1.000         | 1           | 108   |
| s_gen_gas_turb → s_gen_HRSG | 0.954         | 11          | 144   |
| h6 → h7s                    | 0.941         | 17          | 216   |
| s4 → s5                     | 0.936         | 76          | 360   |
| h5s → h5                    | 0.936         | 25          | 180   |
| h2s → h2                    | 0.933         | 131         | 1386  |
| h4 → T4                     | 0.931         | 104         | 324   |
| s2 → s3                     | 0.928         | 149         | 954   |
| h4s → h4                    | 0.923         | 140         | 756   |
| s1 → s2                     | 0.915         | 136         | 954   |
| s3 → s4                     | 0.888         | 136         | 954   |
| x_dest_hr → x_dest_total    | 0.877         | 26          | 162   |

### 6.3 Near-Miss Analysis

Steps where the model was *almost* correct (1.5% < |error| < 2.5%):

#### Tier 1

| Model    | Near-Misses (3 runs) | Total Steps | Rate |
| -------- | -------------------: | ----------: | ---: |
| MiniMax  | 65                   | 870         | 7.5% |
| GPT-5.4  | 47                   | 870         | 5.4% |
| DeepSeek | 32                   | 870         | 3.7% |
| Grok 4   | 25                   | 870         | 2.9% |
| Gemini   | 20                   | 870         | 2.3% |
| Opus     | 18                   | 870         | 2.1% |

#### Tier 2

| Model    | Near-Misses (3 runs) | Total Steps | Rate |
| -------- | -------------------: | ----------: | ---: |
| MiniMax  | 152                  | 2244        | 6.8% |
| Grok 4   | 98                   | 2244        | 4.4% |
| GPT-5.4  | 90                   | 2244        | 4.0% |
| DeepSeek | 69                   | 2244        | 3.1% |
| Gemini   | 51                   | 2244        | 2.3% |
| Opus     | 47                   | 2244        | 2.1% |

#### Tier 3

| Model    | Near-Misses (3 runs) | Total Steps | Rate |
| -------- | -------------------: | ----------: | ---: |
| GPT-5.4  | 422                  | 6381        | 6.6% |
| MiniMax  | 346                  | 6381        | 5.4% |
| Grok 4   | 340                  | 6381        | 5.3% |
| DeepSeek | 324                  | 6381        | 5.1% |
| Gemini   | 314                  | 6381        | 4.9% |
| Opus     | 150                  | 6381        | 2.4% |


---

## 7. Token Efficiency

### 7.1 Mean Output Tokens

| Model           | T1 Tokens | T2 Tokens | T3 Tokens | T3/T1 Ratio |
| --------------- | --------: | --------: | --------: | ----------: |
| Claude Opus 4.6 | 12,115    | 29,969    | 52,637    | 4.3×        |
| GPT-5.4         | 10,771    | 9,021     | 15,366    | 1.4×        |
| Gemini 2.5 Pro  | 821       | 1,315     | 2,229     | 2.7×        |
| Grok 4          | 411       | 629       | 1,011     | 2.5×        |
| DeepSeek R1     | 7,315     | 13,844    | 17,927    | 2.5×        |
| MiniMax M1      | 7,624     | 12,048    | 15,066    | 2.0×        |

### 7.2 Tokens per Percentage Point

Lower is more efficient: `mean_tokens / (score × 100)`

| Model           | T1 tok/pp | T2 tok/pp | T3 tok/pp |
| --------------- | --------: | --------: | --------: |
| Claude Opus 4.6 | 126       | 326       | 563       |
| GPT-5.4         | 110       | 99        | 171       |
| Gemini 2.5 Pro  | 8         | 14        | 25        |
| Grok 4          | 4         | 7         | 13        |
| DeepSeek R1     | 81        | 155       | 221       |
| MiniMax M1      | 90        | 158       | 286       |

### 7.3 Token-Accuracy Correlation

**Tier 1**: Pearson r = 0.067, Spearman ρ = 0.029

**Tier 2**: Pearson r = 0.118, Spearman ρ = 0.371

**Tier 3**: Pearson r = 0.292, Spearman ρ = 0.600


---

## 8. Grok 4 Analysis

Grok 4 (xAI) is the newest model in the benchmark. How does it compare?

### 8.1 Rank Position

| Tier   | Grok 4 Score | Rank | Gap to #1 | Gap to Median |
| ------ | -----------: | :--: | --------: | ------------: |
| Tier 1 | 91.8%        | #4   | 6.1%      | -2.3%         |
| Tier 2 | 87.9%        | #5   | 4.1%      | -2.1%         |
| Tier 3 | 80.4%        | #5   | 13.2%     | -3.9%         |

### 8.2 Grok 4 vs DeepSeek R1 Head-to-Head

Both are reasoning-focused models. Direct comparison:

| Dimension        | Grok 4 | DeepSeek R1 | Winner   |
| ---------------- | -----: | ----------: | -------- |
| Tier 1 Overall   | 91.8%  | 90.5%       | Grok 4   |
| Tier 2 Overall   | 87.9%  | 89.2%       | DeepSeek |
| Tier 3 Overall   | 80.4%  | 81.0%       | DeepSeek |
| T1 Supercritical | 52.8%  | 48.9%       | Grok 4   |
| T2 Compressor    | 64.8%  | 67.2%       | DeepSeek |
| T2 R-134a        | 44.0%  | 63.4%       | DeepSeek |
| T3 CCGT          | 58.6%  | 72.2%       | DeepSeek |
| T3 VCR           | 73.6%  | 66.8%       | Grok 4   |

### 8.3 Grok 4 Strengths & Weaknesses

**Weaknesses** (below median by >2pp):

- T1 supercritical: 52.8% (-17.8% vs median)
- T1 phase_determination: 82.2% (-15.6% vs median)
- T3 CCGT: 58.6% (-15.4% vs median)
- T2 boiler: 93.8% (-4.8% vs median)
- T3 BRY: 83.2% (-4.5% vs median)
- T2 heat_exchanger: 85.5% (-3.6% vs median)
- T1 inverse_lookups: 90.0% (-3.3% vs median)
- T3 VCR: 73.6% (-3.1% vs median)
- T2 nozzle: 89.1% (-2.6% vs median)
- T2 compressor: 64.8% (-2.4% vs median)


---

## 9. Extraction Methodology & Reliability

All responses were re-extracted using gpt-4.1-mini LLM extraction.

### 9.1 Extraction Failure Rates

Per-step extraction failure rate (`error_type` = 'extraction_failed' or 'missing'):

#### Tier 1

| Model    | Total Steps | Extraction Failed | Missing | Failure Rate | Non-null Pass Rate |
| -------- | ----------: | ----------------: | ------: | -----------: | -----------------: |
| Opus     | 870         | 0                 | 0       | 0.0%         | 94.5%              |
| GPT-5.4  | 870         | 0                 | 0       | 0.0%         | 97.2%              |
| Gemini   | 870         | 0                 | 0       | 0.0%         | 96.1%              |
| Grok 4   | 870         | 0                 | 0       | 0.0%         | 89.8%              |
| DeepSeek | 870         | 0                 | 0       | 0.0%         | 87.5%              |
| MiniMax  | 870         | 0                 | 0       | 0.0%         | 81.6%              |

#### Tier 2

| Model    | Total Steps | Extraction Failed | Missing | Failure Rate | Non-null Pass Rate |
| -------- | ----------: | ----------------: | ------: | -----------: | -----------------: |
| Opus     | 2244        | 0                 | 0       | 0.0%         | 91.6%              |
| GPT-5.4  | 2244        | 0                 | 0       | 0.0%         | 90.4%              |
| Gemini   | 2244        | 0                 | 0       | 0.0%         | 89.1%              |
| Grok 4   | 2244        | 0                 | 3       | 0.1%         | 88.0%              |
| DeepSeek | 2244        | 0                 | 0       | 0.0%         | 89.9%              |
| MiniMax  | 2244        | 0                 | 3       | 0.1%         | 79.6%              |

#### Tier 3

| Model    | Total Steps | Extraction Failed | Missing | Failure Rate | Non-null Pass Rate |
| -------- | ----------: | ----------------: | ------: | -----------: | -----------------: |
| Opus     | 6381        | 0                 | 0       | 0.0%         | 92.8%              |
| GPT-5.4  | 6381        | 0                 | 0       | 0.0%         | 88.7%              |
| Gemini   | 6381        | 0                 | 0       | 0.0%         | 87.8%              |
| Grok 4   | 6381        | 0                 | 52      | 0.8%         | 80.2%              |
| DeepSeek | 6381        | 0                 | 34      | 0.5%         | 84.8%              |
| MiniMax  | 6381        | 0                 | 500     | 7.8%         | 59.8%              |

### 9.2 Steps with Highest Extraction Failure

#### Tier 2

| Step       | Total | Failed | Failure Rate |
| ---------- | ----: | -----: | -----------: |
| X_dest_dot | 180   | 1      | 0.6%         |
| eta_II     | 540   | 2      | 0.4%         |
| s1         | 1152  | 3      | 0.3%         |
| h1         | 1224  | 0      | 0.0%         |
| h2s        | 1008  | 0      | 0.0%         |
| h2         | 1224  | 0      | 0.0%         |
| w_out      | 324   | 0      | 0.0%         |
| s2         | 774   | 0      | 0.0%         |
| s_gen      | 810   | 0      | 0.0%         |
| x_dest     | 360   | 0      | 0.0%         |
| w_in       | 432   | 0      | 0.0%         |
| h_h_in     | 342   | 0      | 0.0%         |
| h_h_out    | 342   | 0      | 0.0%         |
| h_c_in     | 342   | 0      | 0.0%         |
| Q_dot      | 342   | 0      | 0.0%         |

#### Tier 3

| Step              | Total | Failed | Failure Rate |
| ----------------- | ----: | -----: | -----------: |
| ef7               | 72    | 8      | 11.1%        |
| ef8               | 72    | 8      | 11.1%        |
| ef9               | 72    | 8      | 11.1%        |
| x_dest_gas_turb   | 72    | 7      | 9.7%         |
| x_dest_HRSG       | 72    | 7      | 9.7%         |
| x_dest_steam_turb | 72    | 7      | 9.7%         |
| s_gen_HRSG        | 144   | 12     | 8.3%         |
| s_gen_steam_turb  | 144   | 11     | 7.6%         |
| ef5               | 180   | 13     | 7.2%         |
| ef6               | 180   | 13     | 7.2%         |
| s_gen_gas_turb    | 144   | 10     | 6.9%         |
| eta_combined      | 216   | 12     | 5.6%         |
| s9                | 144   | 8      | 5.6%         |
| W_net_combined    | 216   | 11     | 5.1%         |
| s7                | 144   | 7      | 4.9%         |


---

## 10. Statistical Significance

### 10.1 Pairwise Welch t-test (Tier 3)

Can we distinguish model performance on Tier 3 with only 3 runs?
✓ = significant at α=0.05, ✗ = not significant.

|          | Opus         | GPT-5.4      | Gemini       | Grok 4       | DeepSeek     | MiniMax     |
| -------- | :----------: | :----------: | :----------: | :----------: | :----------: | :---------: |
| Opus     | —            | ✓ (t=12.66)  | ✓ (t=6.50)   | ✓ (t=24.59)  | ✓ (t=9.49)   | ✓ (t=45.89) |
| GPT-5.4  | ✓ (t=-12.66) | —            | ✗ (t=2.49)   | ✓ (t=20.54)  | ✓ (t=6.75)   | ✓ (t=43.86) |
| Gemini   | ✓ (t=-6.50)  | ✗ (t=-2.49)  | —            | ✓ (t=7.27)   | ✓ (t=4.18)   | ✓ (t=28.67) |
| Grok 4   | ✓ (t=-24.59) | ✓ (t=-20.54) | ✓ (t=-7.27)  | —            | ✗ (t=-0.49)  | ✓ (t=29.02) |
| DeepSeek | ✓ (t=-9.49)  | ✓ (t=-6.75)  | ✓ (t=-4.18)  | ✗ (t=0.49)   | —            | ✓ (t=18.44) |
| MiniMax  | ✓ (t=-45.89) | ✓ (t=-43.86) | ✓ (t=-28.67) | ✓ (t=-29.02) | ✓ (t=-18.44) | —           |

### 10.2 95% Confidence Intervals

#### Tier 1

| Model           | Mean  | 95% CI         | Width |
| --------------- | ----: | :------------: | ----: |
| Gemini 2.5 Pro  | 97.9% | [96.6%, 99.2%] | 2.6%  |
| GPT-5.4         | 97.8% | [95.8%, 99.8%] | 3.9%  |
| Claude Opus 4.6 | 96.4% | [94.1%, 98.7%] | 4.6%  |
| Grok 4          | 91.8% | [88.7%, 94.9%] | 6.2%  |
| DeepSeek R1     | 90.5% | [90.2%, 90.9%] | 0.7%  |
| MiniMax M1      | 85.2% | [83.6%, 86.7%] | 3.1%  |

#### Tier 2

| Model           | Mean  | 95% CI         | Width |
| --------------- | ----: | :------------: | ----: |
| Claude Opus 4.6 | 92.1% | [91.7%, 92.4%] | 0.8%  |
| GPT-5.4         | 90.8% | [89.5%, 92.1%] | 2.6%  |
| Gemini 2.5 Pro  | 90.8% | [87.7%, 93.8%] | 6.1%  |
| DeepSeek R1     | 89.2% | [83.1%, 95.4%] | 12.3% |
| Grok 4          | 87.9% | [86.2%, 89.6%] | 3.3%  |
| MiniMax M1      | 76.2% | [73.5%, 78.8%] | 5.3%  |

#### Tier 3

| Model           | Mean  | 95% CI         | Width |
| --------------- | ----: | :------------: | ----: |
| Claude Opus 4.6 | 93.6% | [92.3%, 94.8%] | 2.5%  |
| GPT-5.4         | 89.7% | [89.4%, 90.1%] | 0.7%  |
| Gemini 2.5 Pro  | 87.5% | [83.8%, 91.3%] | 7.6%  |
| DeepSeek R1     | 81.0% | [75.5%, 86.6%] | 11.1% |
| Grok 4          | 80.4% | [78.4%, 82.3%] | 3.9%  |
| MiniMax M1      | 52.7% | [49.1%, 56.3%] | 7.2%  |

### 10.3 Cross-Tier Correlations

- **T1–T2**: Pearson r = 0.881, Spearman ρ = 0.714
- **T1–T3**: Pearson r = 0.917, Spearman ρ = 0.714
- **T2–T3**: Pearson r = 0.991, Spearman ρ = 1.000


---

## 11. Recommendations

### 11.1 Per-Model Improvement Areas

#### Claude Opus 4.6

- **T1 supercritical**: 70.5% (25.9% below overall)
- **T2 compressor**: 75.4% (16.6% below overall)
- **T3 VCR**: 81.6% (12.0% below overall)

#### GPT-5.4

- **T2 compressor**: 71.2% (19.6% below overall)
- **T3 VCR**: 76.6% (13.1% below overall)
- **T1 supercritical**: 89.5% (8.4% below overall)
- **T3 CCGT**: 82.0% (7.8% below overall)
- **T1 inverse_lookups**: 91.7% (6.1% below overall)

#### Gemini 2.5 Pro

- **T2 compressor**: 66.3% (24.5% below overall)
- **T1 supercritical**: 77.8% (20.1% below overall)
- **T3 CCGT**: 74.0% (13.5% below overall)

#### Grok 4

- **T1 supercritical**: 52.8% (39.0% below overall)
- **T2 compressor**: 64.8% (23.1% below overall)
- **T3 CCGT**: 58.6% (21.7% below overall)
- **T1 phase_determination**: 82.2% (9.6% below overall)
- **T3 VCR**: 73.6% (6.8% below overall)

#### DeepSeek R1

- **T1 supercritical**: 48.9% (41.6% below overall)
- **T2 compressor**: 67.2% (22.0% below overall)
- **T3 VCR**: 66.8% (14.3% below overall)
- **T3 CCGT**: 72.2% (8.8% below overall)
- **T2 nozzle**: 83.6% (5.7% below overall)

#### MiniMax M1

- **T1 supercritical**: 45.0% (40.2% below overall)
- **T3 CCGT**: 31.8% (20.9% below overall)
- **T2 compressor**: 55.5% (20.7% below overall)
- **T3 VCR**: 32.5% (20.1% below overall)
- **T1 inverse_lookups**: 75.9% (9.3% below overall)

### 11.2 Model Selection Guide

- **Property lookups (T1)**: Gemini 2.5 Pro (97.9%)
- **Component analysis (T2)**: Claude Opus 4.6 (92.1%)
- **Cycle analysis (T3)**: Claude Opus 4.6 (93.6%)
- **Overall best**: Claude Opus 4.6 (composite 94.1%)
- **Most consistent**: GPT-5.4 (mean σ = 0.5%)

### 11.3 Benchmark Design Lessons

1. **Multi-run evaluation is essential**: Single-run results can be misleading. σ ranges from 0.1% to 2.5% across models.
2. **Tiered design reveals different skills**: T1-T3 rankings are not identical, confirming that memorization ≠ reasoning.
3. **Supercritical and R-134a are natural discriminators**: These subsets produce the widest performance spreads.
4. **Weighted scoring matters**: Using step weights (vs binary pass/fail) rewards partial understanding.
5. **LLM re-extraction reduces noise**: gpt-4.1-mini extraction normalizes format differences across model output styles.

---

## 12. Appendix

### A.1 Per-Question Score Matrix

Mean question score across 3 runs. 293 questions × 6 models.

#### Tier 1

| ID        | Opus   | GPT-5.4 | Gemini | Grok 4 | DeepSeek | MiniMax |
| --------- | -----: | ------: | -----: | -----: | -------: | ------: |
| T1-SL-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 66.7%   |
| T1-SL-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-007 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 66.7%   |
| T1-SL-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SL-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 91.7%   |
| T1-SF-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 83.3%   |
| T1-SF-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 91.7%   |
| T1-SF-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-007 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 66.7%   |
| T1-SF-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 33.3%   |
| T1-SF-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SF-011 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 83.3%   |
| T1-SF-012 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 88.9%   |
| T1-WS-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 77.8%    | 100.0%  |
| T1-WS-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 88.9%   |
| T1-WS-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-007 | 88.9%  | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-011 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-012 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-013 | 100.0% | 100.0%  | 100.0% | 100.0% | 77.8%    | 100.0%  |
| T1-WS-014 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-WS-015 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 88.9%   |
| T1-WS-016 | 100.0% | 100.0%  | 100.0% | 100.0% | 55.6%    | 33.3%   |
| T1-WS-017 | 100.0% | 100.0%  | 100.0% | 100.0% | 88.9%    | 100.0%  |
| T1-WS-018 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 55.6%   |
| T1-SV-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SV-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 91.7%   |
| T1-SV-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 91.7%    | 83.3%   |
| T1-SV-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 91.7%   |
| T1-SV-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SV-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SV-007 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 91.7%   |
| T1-SV-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SV-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SV-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 77.8%   |
| T1-SH-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 88.9%   |
| T1-SH-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 88.9%    | 77.8%   |
| T1-SH-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 66.7%   |
| T1-SH-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-007 | 100.0% | 100.0%  | 100.0% | 88.9%  | 77.8%    | 77.8%   |
| T1-SH-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 77.8%    | 66.7%   |
| T1-SH-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-011 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-012 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-013 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-014 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 83.3%   |
| T1-SH-015 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-016 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-SH-017 | 100.0% | 100.0%  | 88.9%  | 100.0% | 44.4%    | 88.9%   |
| T1-SH-018 | 77.8%  | 88.9%   | 100.0% | 100.0% | 77.8%    | 55.6%   |
| T1-SH-019 | 100.0% | 100.0%  | 100.0% | 100.0% | 77.8%    | 55.6%   |
| T1-SH-020 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 77.8%   |
| T1-SC-001 | 44.4%  | 77.8%   | 77.8%  | 55.6%  | 33.3%    | 33.3%   |
| T1-SC-002 | 66.7%  | 77.8%   | 88.9%  | 66.7%  | 44.4%    | 55.6%   |
| T1-SC-003 | 100.0% | 100.0%  | 88.9%  | 77.8%  | 100.0%   | 77.8%   |
| T1-SC-004 | 100.0% | 100.0%  | 88.9%  | 77.8%  | 77.8%    | 66.7%   |
| T1-SC-005 | 77.8%  | 100.0%  | 77.8%  | 66.7%  | 33.3%    | 33.3%   |
| T1-SC-006 | 55.6%  | 88.9%   | 50.0%  | 33.3%  | 27.8%    | 33.3%   |
| T1-SC-007 | 61.1%  | 72.2%   | 61.1%  | 27.8%  | 44.4%    | 38.9%   |
| T1-SC-008 | 50.0%  | 88.9%   | 94.4%  | 44.4%  | 38.9%    | 38.9%   |
| T1-SC-009 | 66.7%  | 94.4%   | 72.2%  | 38.9%  | 50.0%    | 33.3%   |
| T1-SC-010 | 83.3%  | 94.4%   | 77.8%  | 38.9%  | 38.9%    | 38.9%   |
| T1-PD-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-004 | 33.3%  | 100.0%  | 100.0% | 0.0%   | 66.7%    | 100.0%  |
| T1-PD-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-006 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-007 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-008 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-010 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-011 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-PD-012 | 100.0% | 100.0%  | 100.0% | 66.7%  | 33.3%    | 100.0%  |
| T1-PD-013 | 100.0% | 100.0%  | 100.0% | 33.3%  | 33.3%    | 100.0%  |
| T1-PD-014 | 100.0% | 100.0%  | 100.0% | 33.3%  | 100.0%   | 66.7%   |
| T1-PD-015 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-IL-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-IL-002 | 100.0% | 100.0%  | 100.0% | 66.7%  | 83.3%    | 33.3%   |
| T1-IL-003 | 100.0% | 100.0%  | 100.0% | 66.7%  | 100.0%   | 66.7%   |
| T1-IL-004 | 100.0% | 100.0%  | 100.0% | 66.7%  | 100.0%   | 83.3%   |
| T1-IL-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-IL-006 | 100.0% | 66.7%   | 100.0% | 83.3%  | 66.7%    | 50.0%   |
| T1-IL-007 | 100.0% | 66.7%   | 100.0% | 66.7%  | 66.7%    | 50.0%   |
| T1-IL-008 | 100.0% | 50.0%   | 100.0% | 100.0% | 100.0%   | 50.0%   |
| T1-IL-009 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-IL-010 | 100.0% | 91.7%   | 100.0% | 100.0% | 91.7%    | 100.0%  |
| T1-IL-011 | 100.0% | 100.0%  | 100.0% | 100.0% | 91.7%    | 83.3%   |
| T1-IL-012 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 77.8%   |
| T1-IL-013 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 44.4%   |
| T1-IL-014 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T1-IL-015 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |

#### Tier 2

| ID            | Opus   | GPT-5.4 | Gemini | Grok 4 | DeepSeek | MiniMax |
| ------------- | -----: | ------: | -----: | -----: | -------: | ------: |
| T2-TRB-AW-001 | 88.2%  | 100.0%  | 100.0% | 88.2%  | 82.4%    | 47.1%   |
| T2-TRB-AW-002 | 100.0% | 100.0%  | 100.0% | 88.2%  | 100.0%   | 64.7%   |
| T2-TRB-AW-003 | 88.2%  | 76.5%   | 88.2%  | 64.7%  | 100.0%   | 70.6%   |
| T2-TRB-AW-004 | 100.0% | 88.2%   | 100.0% | 88.2%  | 88.2%    | 49.0%   |
| T2-TRB-AW-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 47.1%   |
| T2-TRB-BW-001 | 100.0% | 82.6%   | 100.0% | 73.9%  | 91.3%    | 52.2%   |
| T2-TRB-BW-002 | 82.6%  | 91.3%   | 100.0% | 100.0% | 100.0%   | 73.9%   |
| T2-TRB-BW-003 | 100.0% | 82.6%   | 100.0% | 91.3%  | 65.2%    | 46.4%   |
| T2-TRB-BW-004 | 100.0% | 91.3%   | 100.0% | 100.0% | 100.0%   | 82.6%   |
| T2-TRB-CW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 95.1%    | 61.7%   |
| T2-TRB-CW-002 | 90.1%  | 100.0%  | 100.0% | 100.0% | 90.1%    | 53.1%   |
| T2-TRB-CW-003 | 100.0% | 80.2%   | 100.0% | 87.7%  | 80.2%    | 37.0%   |
| T2-TRB-AA-001 | 100.0% | 96.1%   | 88.2%  | 88.2%  | 92.2%    | 92.2%   |
| T2-TRB-AA-002 | 100.0% | 96.1%   | 88.2%  | 88.2%  | 92.2%    | 100.0%  |
| T2-TRB-BA-001 | 94.2%  | 82.6%   | 73.9%  | 82.6%  | 88.4%    | 100.0%  |
| T2-TRB-BA-002 | 100.0% | 100.0%  | 82.6%  | 82.6%  | 88.4%    | 88.4%   |
| T2-TRB-CA-001 | 100.0% | 100.0%  | 82.7%  | 95.1%  | 100.0%   | 97.5%   |
| T2-TRB-CA-002 | 100.0% | 66.7%   | 95.1%  | 100.0% | 100.0%   | 97.5%   |
| T2-CMP-AW-001 | 100.0% | 88.2%   | 82.4%  | 52.9%  | 52.9%    | 29.4%   |
| T2-CMP-AW-002 | 100.0% | 76.5%   | 88.2%  | 88.2%  | 70.6%    | 29.4%   |
| T2-CMP-BW-001 | 91.3%  | 100.0%  | 78.3%  | 100.0% | 36.2%    | 30.4%   |
| T2-CMP-BW-002 | 100.0% | 82.6%   | 100.0% | 100.0% | 73.9%    | 52.2%   |
| T2-CMP-CW-001 | 100.0% | 80.2%   | 92.6%  | 95.1%  | 71.6%    | 45.7%   |
| T2-CMP-AR-001 | 11.8%  | 0.0%    | 11.8%  | 0.0%   | 31.4%    | 31.4%   |
| T2-CMP-AR-002 | 0.0%   | 11.8%   | 11.8%  | 0.0%   | 43.1%    | 13.7%   |
| T2-CMP-BR-001 | 63.8%  | 17.4%   | 17.4%  | 17.4%  | 52.2%    | 31.9%   |
| T2-CMP-BR-002 | 26.1%  | 62.3%   | 26.1%  | 17.4%  | 47.8%    | 30.4%   |
| T2-CMP-AA-001 | 88.2%  | 100.0%  | 88.2%  | 88.2%  | 92.2%    | 100.0%  |
| T2-CMP-AA-002 | 92.2%  | 100.0%  | 88.2%  | 88.2%  | 92.2%    | 100.0%  |
| T2-CMP-BA-001 | 88.4%  | 100.0%  | 82.6%  | 82.6%  | 94.2%    | 94.2%   |
| T2-CMP-BA-002 | 94.2%  | 100.0%  | 82.6%  | 82.6%  | 82.6%    | 88.4%   |
| T2-CMP-CA-001 | 100.0% | 77.8%   | 77.8%  | 95.1%  | 100.0%   | 100.0%  |
| T2-PMP-AW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-AW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-AW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-BW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-BW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-BW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-PMP-CW-001 | 100.0% | 100.0%  | 100.0% | 95.1%  | 100.0%   | 95.1%   |
| T2-PMP-CW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 95.1%    | 90.1%   |
| T2-PMP-CW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 90.1%    | 95.1%   |
| T2-PMP-CW-004 | 100.0% | 100.0%  | 100.0% | 95.1%  | 100.0%   | 95.1%   |
| T2-HX-AW-001  | 100.0% | 90.5%   | 100.0% | 100.0% | 95.2%    | 100.0%  |
| T2-HX-AW-002  | 100.0% | 71.4%   | 100.0% | 71.4%  | 100.0%   | 90.5%   |
| T2-HX-AW-003  | 95.2%  | 85.7%   | 95.2%  | 85.7%  | 95.2%    | 95.2%   |
| T2-HX-AW-004  | 100.0% | 81.0%   | 100.0% | 90.5%  | 90.5%    | 85.7%   |
| T2-HX-AW-005  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-HX-BW-001  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-HX-BW-002  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-HX-BW-003  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-HX-BW-004  | 100.0% | 84.8%   | 100.0% | 90.9%  | 97.0%    | 97.0%   |
| T2-HX-CW-001  | 92.3%  | 94.9%   | 100.0% | 94.9%  | 100.0%   | 87.2%   |
| T2-HX-CW-002  | 100.0% | 92.3%   | 97.4%  | 94.9%  | 100.0%   | 92.3%   |
| T2-HX-CW-003  | 94.9%  | 97.4%   | 92.3%  | 92.3%  | 97.4%    | 82.1%   |
| T2-HX-CW-004  | 89.7%  | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-HX-AR-001  | 81.0%  | 66.7%   | 71.4%  | 71.4%  | 90.5%    | 66.7%   |
| T2-HX-AR-002  | 71.4%  | 66.7%   | 71.4%  | 61.9%  | 66.7%    | 66.7%   |
| T2-HX-BR-001  | 72.7%  | 72.7%   | 72.7%  | 66.7%  | 69.7%    | 81.8%   |
| T2-HX-BR-002  | 72.7%  | 60.6%   | 72.7%  | 63.6%  | 78.8%    | 75.8%   |
| T2-HX-CR-001  | 71.8%  | 74.4%   | 59.0%  | 69.2%  | 76.9%    | 69.2%   |
| T2-HX-CR-002  | 69.2%  | 71.8%   | 61.5%  | 71.8%  | 76.9%    | 74.4%   |
| T2-BLR-AW-001 | 100.0% | 100.0%  | 100.0% | 25.0%  | 100.0%   | 75.0%   |
| T2-BLR-AW-002 | 83.3%  | 91.7%   | 100.0% | 91.7%  | 75.0%    | 50.0%   |
| T2-BLR-AW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 75.0%   |
| T2-BLR-AW-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 25.0%   |
| T2-BLR-BW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 75.0%   |
| T2-BLR-BW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-BLR-BW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 85.0%   |
| T2-BLR-BW-004 | 100.0% | 95.0%   | 100.0% | 100.0% | 100.0%   | 95.0%   |
| T2-BLR-BW-005 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 50.0%   |
| T2-BLR-CW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 94.4%   |
| T2-BLR-CW-002 | 100.0% | 100.0%  | 100.0% | 95.8%  | 100.0%   | 76.4%   |
| T2-BLR-CW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 94.4%    | 70.8%   |
| T2-BLR-CW-004 | 100.0% | 100.0%  | 94.4%  | 100.0% | 100.0%   | 61.1%   |
| T2-BLR-CW-005 | 100.0% | 100.0%  | 84.7%  | 100.0% | 100.0%   | 65.3%   |
| T2-MIX-AW-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 66.7%   |
| T2-MIX-AW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-MIX-AW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-MIX-AW-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-MIX-BW-001 | 21.1%  | 100.0%  | 100.0% | 94.7%  | 100.0%   | 100.0%  |
| T2-MIX-BW-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 98.2%   |
| T2-MIX-BW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-MIX-BW-004 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T2-MIX-CW-001 | 94.2%  | 91.3%   | 97.1%  | 91.3%  | 91.3%    | 63.8%   |
| T2-MIX-CW-002 | 100.0% | 100.0%  | 100.0% | 97.1%  | 94.2%    | 79.7%   |
| T2-MIX-CW-003 | 91.3%  | 97.1%   | 85.5%  | 94.2%  | 73.9%    | 68.1%   |
| T2-MIX-CW-004 | 91.3%  | 100.0%  | 100.0% | 100.0% | 100.0%   | 85.5%   |
| T2-NOZ-AW-001 | 69.2%  | 100.0%  | 100.0% | 89.7%  | 56.4%    | 43.6%   |
| T2-NOZ-AW-002 | 100.0% | 100.0%  | 100.0% | 79.5%  | 71.8%    | 48.7%   |
| T2-NOZ-AW-003 | 100.0% | 89.7%   | 100.0% | 100.0% | 56.4%    | 30.8%   |
| T2-NOZ-BW-001 | 100.0% | 100.0%  | 100.0% | 86.0%  | 70.2%    | 52.6%   |
| T2-NOZ-BW-002 | 100.0% | 100.0%  | 93.0%  | 100.0% | 100.0%   | 35.1%   |
| T2-NOZ-BW-003 | 100.0% | 100.0%  | 100.0% | 100.0% | 93.0%    | 52.6%   |
| T2-NOZ-CW-001 | 100.0% | 91.3%   | 97.1%  | 73.9%  | 79.7%    | 59.4%   |
| T2-NOZ-CW-002 | 97.1%  | 100.0%  | 97.1%  | 91.3%  | 94.2%    | 55.1%   |
| T2-NOZ-AA-001 | 84.6%  | 100.0%  | 84.6%  | 84.6%  | 84.6%    | 100.0%  |
| T2-NOZ-AA-002 | 84.6%  | 100.0%  | 84.6%  | 84.6%  | 84.6%    | 94.9%   |
| T2-NOZ-BA-001 | 93.0%  | 78.9%   | 71.9%  | 78.9%  | 86.0%    | 93.0%   |
| T2-NOZ-BA-002 | 78.9%  | 93.0%   | 78.9%  | 78.9%  | 93.0%    | 93.0%   |
| T2-NOZ-CA-001 | 100.0% | 100.0%  | 79.7%  | 100.0% | 100.0%   | 100.0%  |
| T2-NOZ-CA-002 | 100.0% | 100.0%  | 97.1%  | 100.0% | 100.0%   | 97.1%   |

#### Tier 3

| ID                 | Opus   | GPT-5.4 | Gemini | Grok 4 | DeepSeek | MiniMax |
| ------------------ | -----: | ------: | -----: | -----: | -------: | ------: |
| T3-RNK-I-WA-A-001  | 100.0% | 82.1%   | 100.0% | 82.1%  | 100.0%   | 42.9%   |
| T3-RNK-I-WA-C-001  | 98.6%  | 98.6%   | 100.0% | 98.6%  | 91.4%    | 80.6%   |
| T3-RNK-A-WA-A-001  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 40.0%   |
| T3-RNK-A-WA-A-002  | 100.0% | 100.0%  | 100.0% | 100.0% | 91.1%    | 77.8%   |
| T3-RNK-A-WA-A-003  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 64.4%   |
| T3-RNK-A-WA-A-004  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 38.9%   |
| T3-RNK-A-WA-A-005  | 100.0% | 100.0%  | 100.0% | 100.0% | 63.3%    | 44.4%   |
| T3-RNK-A-WA-B-001  | 100.0% | 100.0%  | 100.0% | 70.4%  | 80.2%    | 63.0%   |
| T3-RNK-A-WA-B-002  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 59.9%   |
| T3-RNK-A-WA-B-003  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 85.8%   |
| T3-RNK-A-WA-B-004  | 100.0% | 93.8%   | 100.0% | 100.0% | 92.0%    | 52.5%   |
| T3-RNK-A-WA-B-005  | 100.0% | 100.0%  | 100.0% | 100.0% | 78.4%    | 75.3%   |
| T3-RNK-A-WA-C-001  | 100.0% | 97.3%   | 100.0% | 97.3%  | 75.3%    | 43.1%   |
| T3-RNK-A-WA-C-002  | 100.0% | 98.0%   | 100.0% | 93.7%  | 98.0%    | 93.7%   |
| T3-RNK-A-WA-C-003  | 96.5%  | 95.3%   | 95.3%  | 97.3%  | 94.5%    | 49.0%   |
| T3-RNK-A-WA-C-004  | 100.0% | 80.4%   | 100.0% | 93.7%  | 96.1%    | 39.2%   |
| T3-RNK-A-WA-C-005  | 100.0% | 97.6%   | 100.0% | 96.1%  | 77.6%    | 58.8%   |
| T3-RNK-RH-WA-A-001 | 100.0% | 78.4%   | 94.1%  | 100.0% | 53.9%    | 20.6%   |
| T3-RNK-RH-WA-A-002 | 73.5%  | 90.2%   | 84.3%  | 41.2%  | 52.9%    | 19.6%   |
| T3-RNK-RH-WA-A-003 | 79.4%  | 84.3%   | 92.2%  | 94.1%  | 94.1%    | 43.1%   |
| T3-RNK-RH-WA-A-004 | 93.1%  | 81.4%   | 97.1%  | 91.2%  | 100.0%   | 29.4%   |
| T3-RNK-RH-WA-B-001 | 77.3%  | 85.9%   | 87.4%  | 49.0%  | 77.3%    | 65.2%   |
| T3-RNK-RH-WA-B-002 | 96.0%  | 83.8%   | 98.5%  | 91.9%  | 88.9%    | 78.3%   |
| T3-RNK-RH-WA-B-003 | 98.0%  | 82.8%   | 93.4%  | 91.4%  | 90.4%    | 49.5%   |
| T3-RNK-RH-WA-C-001 | 96.6%  | 81.9%   | 65.1%  | 89.4%  | 71.7%    | 31.8%   |
| T3-RNK-RH-WA-C-002 | 97.8%  | 80.4%   | 78.2%  | 89.7%  | 90.0%    | 32.4%   |
| T3-RNK-RH-WA-C-003 | 82.9%  | 93.8%   | 84.4%  | 86.9%  | 65.1%    | 31.8%   |
| T3-BRY-I-AR-A-001  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-I-AR-B-001  | 100.0% | 100.0%  | 91.8%  | 92.5%  | 97.3%    | 100.0%  |
| T3-BRY-I-AR-C-001  | 100.0% | 97.3%   | 98.2%  | 100.0% | 98.2%    | 100.0%  |
| T3-BRY-A-AR-A-001  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-A-AR-A-002  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-A-AR-A-003  | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-A-AR-B-001  | 100.0% | 100.0%  | 92.6%  | 92.6%  | 97.5%    | 97.5%   |
| T3-BRY-A-AR-B-002  | 100.0% | 100.0%  | 92.6%  | 92.6%  | 100.0%   | 100.0%  |
| T3-BRY-A-AR-B-003  | 100.0% | 100.0%  | 92.6%  | 92.6%  | 95.1%    | 100.0%  |
| T3-BRY-A-AR-C-001  | 100.0% | 100.0%  | 98.4%  | 96.9%  | 100.0%   | 96.9%   |
| T3-BRY-A-AR-C-002  | 99.2%  | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-A-AR-C-003  | 100.0% | 100.0%  | 98.4%  | 96.9%  | 100.0%   | 97.6%   |
| T3-BRY-RG-AR-A-001 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-RG-AR-A-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 100.0%  |
| T3-BRY-RG-AR-B-001 | 100.0% | 100.0%  | 90.2%  | 90.2%  | 96.7%    | 100.0%  |
| T3-BRY-RG-AR-B-002 | 100.0% | 100.0%  | 90.2%  | 90.2%  | 100.0%   | 96.7%   |
| T3-BRY-RG-AR-C-001 | 97.6%  | 100.0%  | 100.0% | 100.0% | 100.0%   | 69.0%   |
| T3-BRY-RG-AR-C-002 | 100.0% | 100.0%  | 100.0% | 100.0% | 100.0%   | 71.0%   |
| T3-VCR-A-RF-A-001  | 68.7%  | 75.8%   | 86.9%  | 70.7%  | 43.4%    | 25.3%   |
| T3-VCR-A-RF-A-002  | 91.9%  | 73.7%   | 100.0% | 78.8%  | 54.5%    | 5.1%    |
| T3-VCR-A-RF-A-003  | 80.8%  | 77.8%   | 91.9%  | 67.7%  | 61.6%    | 19.2%   |
| T3-VCR-A-RF-A-004  | 80.8%  | 72.7%   | 78.8%  | 68.7%  | 67.7%    | 14.1%   |
| T3-VCR-A-RF-A-005  | 70.7%  | 70.7%   | 75.8%  | 70.7%  | 59.6%    | 11.1%   |
| T3-VCR-A-RF-B-001  | 90.6%  | 87.1%   | 100.0% | 92.4%  | 84.2%    | 53.8%   |
| T3-VCR-A-RF-B-002  | 95.3%  | 100.0%  | 100.0% | 81.3%  | 83.0%    | 50.3%   |
| T3-VCR-A-RF-B-003  | 80.7%  | 77.2%   | 100.0% | 87.7%  | 81.3%    | 39.2%   |
| T3-VCR-A-RF-B-004  | 95.3%  | 93.6%   | 100.0% | 90.1%  | 81.3%    | 52.0%   |
| T3-VCR-A-RF-B-005  | 95.3%  | 81.3%   | 100.0% | 70.8%  | 66.1%    | 56.7%   |
| T3-VCR-A-RF-C-001  | 63.4%  | 68.5%   | 85.7%  | 73.1%  | 67.7%    | 32.6%   |
| T3-VCR-A-RF-C-002  | 83.9%  | 67.0%   | 88.5%  | 63.1%  | 63.8%    | 35.1%   |
| T3-VCR-A-RF-C-003  | 77.1%  | 63.1%   | 86.4%  | 55.9%  | 58.1%    | 37.3%   |
| T3-VCR-A-RF-C-004  | 69.9%  | 68.1%   | 78.5%  | 76.3%  | 60.2%    | 21.9%   |
| T3-VCR-A-RF-C-005  | 79.2%  | 73.1%   | 91.4%  | 56.3%  | 68.8%    | 34.4%   |
| T3-BRY-AV-AR-A-001 | 100.0% | 100.0%  | 89.6%  | 61.5%  | 76.0%    | 4.2%    |
| T3-BRY-AV-AR-A-002 | 89.6%  | 100.0%  | 36.5%  | 34.4%  | 42.7%    | 21.9%   |
| T3-BRY-AV-AR-B-001 | 97.6%  | 100.0%  | 63.7%  | 48.8%  | 81.5%    | 40.5%   |
| T3-BRY-AV-AR-B-002 | 98.2%  | 92.9%   | 88.1%  | 62.5%  | 87.5%    | 48.8%   |
| T3-BRY-AV-AR-C-001 | 100.0% | 93.9%   | 80.1%  | 48.3%  | 93.5%    | 24.1%   |
| T3-BRY-AV-AR-C-002 | 99.2%  | 93.9%   | 60.5%  | 73.9%  | 78.9%    | 27.6%   |
| T3-BRY-RV-AR-A-001 | 100.0% | 100.0%  | 26.5%  | 90.2%  | 25.5%    | 35.3%   |
| T3-BRY-RV-AR-A-002 | 100.0% | 100.0%  | 24.5%  | 26.5%  | 52.9%    | 10.8%   |
| T3-BRY-RV-AR-B-001 | 98.4%  | 93.7%   | 68.3%  | 67.7%  | 78.8%    | 61.4%   |
| T3-BRY-RV-AR-C-001 | 97.0%  | 67.7%   | 74.3%  | 71.0%  | 52.8%    | 35.6%   |
| T3-CCGT-MX-A-001   | 96.9%  | 82.2%   | 69.8%  | 62.8%  | 54.3%    | 25.6%   |
| T3-CCGT-MX-A-002   | 100.0% | 98.4%   | 75.2%  | 51.9%  | 76.0%    | 34.9%   |
| T3-CCGT-MX-A-003   | 91.5%  | 76.7%   | 51.2%  | 62.0%  | 46.5%    | 33.3%   |
| T3-CCGT-MX-A-004   | 96.1%  | 87.6%   | 73.6%  | 68.2%  | 86.8%    | 31.0%   |
| T3-CCGT-MX-B-001   | 94.8%  | 85.3%   | 84.5%  | 64.7%  | 84.5%    | 42.5%   |
| T3-CCGT-MX-B-002   | 94.8%  | 81.7%   | 86.1%  | 71.0%  | 79.4%    | 43.3%   |
| T3-CCGT-MX-B-003   | 92.1%  | 79.8%   | 82.1%  | 70.2%  | 71.4%    | 50.4%   |
| T3-CCGT-MX-B-004   | 94.0%  | 84.1%   | 96.4%  | 68.3%  | 87.7%    | 19.0%   |
| T3-CCGT-MX-C-001   | 66.9%  | 77.9%   | 74.5%  | 40.6%  | 60.2%    | 16.7%   |
| T3-CCGT-MX-C-002   | 88.0%  | 77.3%   | 67.7%  | 58.1%  | 62.2%    | 29.7%   |
| T3-CCGT-MX-C-003   | 87.5%  | 76.8%   | 55.7%  | 33.6%  | 80.5%    | 15.6%   |
| T3-CCGT-MX-C-004   | 78.9%  | 75.5%   | 71.4%  | 52.1%  | 77.1%    | 39.3%   |

### A.2 Full Aggregate Data

#### Tier 1 Aggregates

**Claude Opus 4.6**: overall = 96.4±0.9%, property_acc = 94.5±1.0%

**GPT-5.4**: overall = 97.8±0.8%, property_acc = 97.2±0.9%

**Gemini 2.5 Pro**: overall = 97.9±0.5%, property_acc = 96.1±1.1%

**Grok 4**: overall = 91.8±1.2%, property_acc = 89.8±0.5%

**DeepSeek R1**: overall = 90.5±0.1%, property_acc = 87.5±0.2%

**MiniMax M1**: overall = 85.2±0.6%, property_acc = 81.6±1.7%

#### Tier 2 Aggregates

**Claude Opus 4.6**: overall = 92.1±0.1%, property_acc = 91.6±0.6%

**GPT-5.4**: overall = 90.8±0.5%, property_acc = 90.4±0.4%

**Gemini 2.5 Pro**: overall = 90.8±1.2%, property_acc = 89.1±0.9%

**Grok 4**: overall = 87.9±0.7%, property_acc = 87.9±0.4%

**DeepSeek R1**: overall = 89.2±2.5%, property_acc = 89.9±2.0%

**MiniMax M1**: overall = 76.2±1.1%, property_acc = 79.5±0.9%

#### Tier 3 Aggregates

**Claude Opus 4.6**: overall = 93.6±0.5%, property_acc = 92.8±0.6%

**GPT-5.4**: overall = 89.7±0.1%, property_acc = 88.7±0.5%

**Gemini 2.5 Pro**: overall = 87.5±1.5%, property_acc = 87.8±1.4%

**Grok 4**: overall = 80.4±0.8%, property_acc = 79.5±1.0%

**DeepSeek R1**: overall = 81.0±2.2%, property_acc = 84.4±2.2%

**MiniMax M1**: overall = 52.7±1.5%, property_acc = 55.1±1.5%

### A.3 Methodology Notes

- **Ground truth**: All reference values computed via CoolProp (v7.2.0)
- **Scoring**: ±2% relative tolerance OR ±0.5 absolute (whichever is more lenient)
- **Phase/exact match**: Exact string comparison for phase identification
- **Multi-run**: 3 independent runs per model, temperature=1.0 for reasoning models
- **Extraction**: Two-pass LLM extraction using gpt-4.1-mini with take-max strategy
- **Composite score**: Question-count-weighted: (110×T1 + 101×T2 + 82×T3) / 293
- **Confidence intervals**: Student's t at 95% with df=2 (n=3 runs)
- **Report generated**: 2026-03-17 10:01 UTC
