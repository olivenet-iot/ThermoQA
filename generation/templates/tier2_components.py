"""
Tier 2 component analysis question templates for ThermoQA.

Each template defines a component × depth × fluid combination with
parameter ranges, step definitions with weights, and multiple question phrasings.
"""

from dataclasses import dataclass, field


@dataclass
class ComponentTemplate:
    template_id: str          # e.g., "TRB-AW", "CMP-CR"
    component: str            # turbine, compressor, pump, ...
    depth: str                # A, B, C
    fluid: str                # Water, R134a, Air
    id_prefix: str            # TRB, CMP, PMP, HX, BLR, MIX, NOZ
    param_ranges: dict        # {param: (min, max)}
    question_templates: list[str]
    steps: list[dict]         # [{id, formula, unit, weight}, ...]
    difficulty: str
    notes: str = ""


# ── Helper: build step lists by depth ──────────────────────

def _steps_a(component_steps_a):
    return list(component_steps_a)

def _steps_b(component_steps_a, component_steps_b):
    return list(component_steps_a) + list(component_steps_b)

def _steps_c(component_steps_a, component_steps_b, component_steps_c):
    return list(component_steps_a) + list(component_steps_b) + list(component_steps_c)


# ── Common step definitions per component ──────────────────

# Turbine steps
_TRB_A = [
    {"id": "h1", "formula": "CoolProp(T1, P1)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "s1", "formula": "CoolProp(T1, P1)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "h2s", "formula": "CoolProp(s=s1, P=P2)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "h2", "formula": "h1 - eta_s*(h1-h2s)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "w_out", "formula": "h1 - h2", "unit": "kJ/kg", "weight": 0.30},
]
_TRB_B = [
    {"id": "s2", "formula": "CoolProp(h=h2, P=P2)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "s_gen", "formula": "s2 - s1", "unit": "kJ/(kg*K)", "weight": 0.20},
]
_TRB_C = [
    {"id": "x_dest", "formula": "T0_K * s_gen", "unit": "kJ/kg", "weight": 0.10},
    {"id": "eta_II", "formula": "w_out / (w_out + x_dest)", "unit": "-", "weight": 0.10},
]

# Compressor steps
_CMP_A = [
    {"id": "h1", "formula": "CoolProp(T1, P1)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "s1", "formula": "CoolProp(T1, P1)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "h2s", "formula": "CoolProp(s=s1, P=P2)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "h2", "formula": "h1 + (h2s-h1)/eta_s", "unit": "kJ/kg", "weight": 0.15},
    {"id": "w_in", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 0.30},
]
_CMP_B = [
    {"id": "s2", "formula": "CoolProp(h=h2, P=P2)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "s_gen", "formula": "s2 - s1", "unit": "kJ/(kg*K)", "weight": 0.20},
]
_CMP_C = [
    {"id": "x_dest", "formula": "T0_K * s_gen", "unit": "kJ/kg", "weight": 0.10},
    {"id": "eta_II", "formula": "1 - x_dest / w_in", "unit": "-", "weight": 0.10},
]

# Pump steps (same structure as compressor)
_PMP_A = list(_CMP_A)  # same step IDs
_PMP_B = list(_CMP_B)
_PMP_C = list(_CMP_C)

# Heat exchanger steps
_HX_A = [
    {"id": "h_h_in", "formula": "CoolProp(T_h_in, P_h)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "h_h_out", "formula": "CoolProp(T_h_out, P_h)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "h_c_in", "formula": "CoolProp(T_c_in, P_c)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "Q_dot", "formula": "m_h * (h_h_in - h_h_out)", "unit": "kW", "weight": 0.20},
    {"id": "h_c_out", "formula": "h_c_in + Q_dot/m_c", "unit": "kJ/kg", "weight": 0.10},
    {"id": "T_c_out", "formula": "CoolProp(h=h_c_out, P_c)", "unit": "C", "weight": 0.10},
]
_HX_B = [
    {"id": "s_h_in", "formula": "CoolProp(T_h_in, P_h)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "s_h_out", "formula": "CoolProp(T_h_out, P_h)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "s_c_in", "formula": "CoolProp(T_c_in, P_c)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "s_c_out", "formula": "CoolProp(h=h_c_out, P_c)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "S_gen_dot", "formula": "m_h*(s_h_out-s_h_in) + m_c*(s_c_out-s_c_in)", "unit": "kW/K", "weight": 0.20},
]
_HX_C = [
    {"id": "X_dest_dot", "formula": "T0_K * S_gen_dot", "unit": "kW", "weight": 0.10},
    {"id": "eta_II", "formula": "m_c*(psi_c_out-psi_c_in) / (m_h*(psi_h_in-psi_h_out))", "unit": "-", "weight": 0.10},
]

# Boiler steps
_BLR_A = [
    {"id": "h_in", "formula": "CoolProp(T_in, P)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "h_out", "formula": "CoolProp(T_out, P)", "unit": "kJ/kg", "weight": 0.15},
    {"id": "q_in", "formula": "h_out - h_in", "unit": "kJ/kg", "weight": 0.30},
]
_BLR_B = [
    {"id": "s_in", "formula": "CoolProp(T_in, P)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "s_out", "formula": "CoolProp(T_out, P)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "s_gen", "formula": "(s_out - s_in) - q_in/T_source", "unit": "kJ/(kg*K)", "weight": 0.20},
]
_BLR_C = [
    {"id": "x_dest", "formula": "T0_K * s_gen", "unit": "kJ/kg", "weight": 0.10},
    {"id": "eta_II", "formula": "(psi_out - psi_in) / (q_in * (1 - T0_K/T_source))", "unit": "-", "weight": 0.10},
]

# Mixer steps
_MIX_A = [
    {"id": "h1", "formula": "CoolProp(T1, P)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "h2", "formula": "CoolProp(T2, P)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "m3", "formula": "m1 + m2", "unit": "kg/s", "weight": 0.05},
    {"id": "h3", "formula": "(m1*h1 + m2*h2) / m3", "unit": "kJ/kg", "weight": 0.20},
    {"id": "T3", "formula": "CoolProp(h=h3, P)", "unit": "C", "weight": 0.15},
]
_MIX_B = [
    {"id": "s1", "formula": "CoolProp(T1, P)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "s2", "formula": "CoolProp(T2, P)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "s3", "formula": "CoolProp(h=h3, P)", "unit": "kJ/(kg*K)", "weight": 0.05},
    {"id": "S_gen_dot", "formula": "m3*s3 - m1*s1 - m2*s2", "unit": "kW/K", "weight": 0.20},
]
_MIX_C = [
    {"id": "X_dest_dot", "formula": "T0_K * S_gen_dot", "unit": "kW", "weight": 0.10},
    {"id": "eta_II", "formula": "m3*psi3 / (m1*psi1 + m2*psi2)", "unit": "-", "weight": 0.10},
]

# Nozzle steps
_NOZ_A = [
    {"id": "h1", "formula": "CoolProp(T1, P1)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "s1", "formula": "CoolProp(T1, P1)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "h2s", "formula": "CoolProp(s=s1, P=P2)", "unit": "kJ/kg", "weight": 0.10},
    {"id": "V2", "formula": "sqrt(V1^2 + 2*eta*(h1-h2s)*1000)", "unit": "m/s", "weight": 0.20},
    {"id": "h2", "formula": "h1 - (V2^2-V1^2)/(2*1000)", "unit": "kJ/kg", "weight": 0.15},
]
_NOZ_B = [
    {"id": "s2", "formula": "CoolProp(h=h2, P=P2)", "unit": "kJ/(kg*K)", "weight": 0.10},
    {"id": "s_gen", "formula": "s2 - s1", "unit": "kJ/(kg*K)", "weight": 0.20},
]
_NOZ_C = [
    {"id": "x_dest", "formula": "T0_K * s_gen", "unit": "kJ/kg", "weight": 0.10},
    {"id": "eta_II", "formula": "KE_gain / exergy_decrease", "unit": "-", "weight": 0.10},
]


# ══════════════════════════════════════════════════════════
# TEMPLATES — Component × Depth × Fluid
# ══════════════════════════════════════════════════════════

# ── TURBINE ───────────────────────────────────────────────

TRB_AW = ComponentTemplate(
    template_id="TRB-AW",
    component="turbine", depth="A", fluid="Water", id_prefix="TRB",
    param_ranges={"T1_C": (300, 600), "P1_MPa": (1.0, 15.0),
                  "P2_MPa": (0.01, 1.0), "eta_s": (0.70, 0.95)},
    question_templates=[
        "Steam enters an adiabatic turbine at {T1_C}°C and {P1_MPa} MPa and exits at {P2_MPa} MPa. The isentropic efficiency of the turbine is {eta_s_pct}%. Determine the actual work output per unit mass.",
        "An adiabatic steam turbine operates with inlet conditions of {T1_C}°C and {P1_MPa} MPa. The exhaust pressure is {P2_MPa} MPa and the isentropic efficiency is {eta_s_pct}%. Calculate the work output per unit mass.",
    ],
    steps=_steps_a(_TRB_A),
    difficulty="easy",
)

TRB_BW = ComponentTemplate(
    template_id="TRB-BW",
    component="turbine", depth="B", fluid="Water", id_prefix="TRB",
    param_ranges={"T1_C": (300, 600), "P1_MPa": (1.0, 15.0),
                  "P2_MPa": (0.01, 1.0), "eta_s": (0.70, 0.95)},
    question_templates=[
        "Steam enters an adiabatic turbine at {T1_C}°C and {P1_MPa} MPa and exits at {P2_MPa} MPa. The isentropic efficiency is {eta_s_pct}%. Determine the work output and the entropy generation per unit mass.",
        "An adiabatic turbine receives steam at {T1_C}°C and {P1_MPa} MPa. It expands to {P2_MPa} MPa with an isentropic efficiency of {eta_s_pct}%. Find the work output per unit mass and the entropy generated.",
    ],
    steps=_steps_b(_TRB_A, _TRB_B),
    difficulty="medium",
)

TRB_CW = ComponentTemplate(
    template_id="TRB-CW",
    component="turbine", depth="C", fluid="Water", id_prefix="TRB",
    param_ranges={"T1_C": (300, 600), "P1_MPa": (1.0, 15.0),
                  "P2_MPa": (0.01, 1.0), "eta_s": (0.70, 0.95)},
    question_templates=[
        "Steam enters an adiabatic turbine at {T1_C}°C and {P1_MPa} MPa and exits at {P2_MPa} MPa. The isentropic efficiency is {eta_s_pct}%. The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the work output, entropy generation, exergy destruction, and second-law efficiency.",
        "An adiabatic steam turbine operates between {P1_MPa} MPa / {T1_C}°C and {P2_MPa} MPa with η_s = {eta_s_pct}%. Using T₀ = 25°C and P₀ = 0.1 MPa as the dead state, calculate the work output, entropy generation, exergy destruction, and exergetic efficiency per unit mass.",
    ],
    steps=_steps_c(_TRB_A, _TRB_B, _TRB_C),
    difficulty="hard",
)

TRB_AA = ComponentTemplate(
    template_id="TRB-AA",
    component="turbine", depth="A", fluid="Air", id_prefix="TRB",
    param_ranges={"T1_C": (800, 1500), "P1_MPa": (0.5, 2.0),
                  "P2_MPa": (0.1, 0.5), "eta_s": (0.80, 0.92)},
    question_templates=[
        "Air enters an adiabatic gas turbine at {T1_C} K and {P1_MPa} MPa and exits at {P2_MPa} MPa. The isentropic efficiency is {eta_s_pct}%. Assume air is an ideal gas with c_p = 1.005 kJ/(kg·K) and k = 1.4. Calculate the work output per unit mass.",
        "An adiabatic turbine receives air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4) at {T1_C} K and {P1_MPa} MPa. It expands to {P2_MPa} MPa with η_s = {eta_s_pct}%. Find the work output per unit mass.",
    ],
    steps=_steps_a(_TRB_A),
    difficulty="easy",
    notes="T1 in Kelvin for Air templates",
)

TRB_BA = ComponentTemplate(
    template_id="TRB-BA",
    component="turbine", depth="B", fluid="Air", id_prefix="TRB",
    param_ranges={"T1_C": (800, 1500), "P1_MPa": (0.5, 2.0),
                  "P2_MPa": (0.1, 0.5), "eta_s": (0.80, 0.92)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4) enters an adiabatic turbine at {T1_C} K and {P1_MPa} MPa and exits at {P2_MPa} MPa with η_s = {eta_s_pct}%. Determine the work output and entropy generation per unit mass.",
    ],
    steps=_steps_b(_TRB_A, _TRB_B),
    difficulty="medium",
    notes="T1 in Kelvin for Air templates",
)

TRB_CA = ComponentTemplate(
    template_id="TRB-CA",
    component="turbine", depth="C", fluid="Air", id_prefix="TRB",
    param_ranges={"T1_C": (800, 1500), "P1_MPa": (0.5, 2.0),
                  "P2_MPa": (0.1, 0.5), "eta_s": (0.80, 0.92)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)) enters an adiabatic turbine at {T1_C} K and {P1_MPa} MPa and exits at {P2_MPa} MPa with η_s = {eta_s_pct}%. The dead state is T₀ = 25°C (298.15 K), P₀ = 0.1 MPa. Calculate the work output, entropy generation, exergy destruction, and second-law efficiency per unit mass.",
    ],
    steps=_steps_c(_TRB_A, _TRB_B, _TRB_C),
    difficulty="hard",
    notes="T1 in Kelvin for Air templates",
)

# ── COMPRESSOR ────────────────────────────────────────────

CMP_AW = ComponentTemplate(
    template_id="CMP-AW",
    component="compressor", depth="A", fluid="Water", id_prefix="CMP",
    param_ranges={"T1_C": (100, 300), "P1_MPa": (0.01, 0.5),
                  "P2_MPa": (0.5, 5.0), "eta_s": (0.75, 0.90)},
    question_templates=[
        "Steam enters an adiabatic compressor at {T1_C}°C and {P1_MPa} MPa and is compressed to {P2_MPa} MPa. The isentropic efficiency is {eta_s_pct}%. Determine the work input per unit mass.",
        "An adiabatic compressor receives steam at {T1_C}°C and {P1_MPa} MPa and compresses it to {P2_MPa} MPa with η_s = {eta_s_pct}%. Calculate the specific work input.",
    ],
    steps=_steps_a(_CMP_A),
    difficulty="easy",
)

CMP_BW = ComponentTemplate(
    template_id="CMP-BW",
    component="compressor", depth="B", fluid="Water", id_prefix="CMP",
    param_ranges={"T1_C": (100, 300), "P1_MPa": (0.01, 0.5),
                  "P2_MPa": (0.5, 5.0), "eta_s": (0.75, 0.90)},
    question_templates=[
        "Steam at {T1_C}°C and {P1_MPa} MPa is compressed adiabatically to {P2_MPa} MPa with an isentropic efficiency of {eta_s_pct}%. Find the work input and entropy generation per unit mass.",
    ],
    steps=_steps_b(_CMP_A, _CMP_B),
    difficulty="medium",
)

CMP_CW = ComponentTemplate(
    template_id="CMP-CW",
    component="compressor", depth="C", fluid="Water", id_prefix="CMP",
    param_ranges={"T1_C": (100, 300), "P1_MPa": (0.01, 0.5),
                  "P2_MPa": (0.5, 5.0), "eta_s": (0.75, 0.90)},
    question_templates=[
        "Steam at {T1_C}°C and {P1_MPa} MPa enters an adiabatic compressor and exits at {P2_MPa} MPa. The isentropic efficiency is {eta_s_pct}%. The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the work input, entropy generation, exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_CMP_A, _CMP_B, _CMP_C),
    difficulty="hard",
)

CMP_AR = ComponentTemplate(
    template_id="CMP-AR",
    component="compressor", depth="A", fluid="R134a", id_prefix="CMP",
    param_ranges={"T1_C": (-10, 30), "P1_MPa": (0.1, 0.5),
                  "P2_MPa": (0.8, 2.0), "eta_s": (0.75, 0.88)},
    question_templates=[
        "R-134a enters an adiabatic compressor as superheated vapor at {T1_C}°C and {P1_MPa} MPa and is compressed to {P2_MPa} MPa with an isentropic efficiency of {eta_s_pct}%. Calculate the work input per unit mass.",
    ],
    steps=_steps_a(_CMP_A),
    difficulty="easy",
)

CMP_BR = ComponentTemplate(
    template_id="CMP-BR",
    component="compressor", depth="B", fluid="R134a", id_prefix="CMP",
    param_ranges={"T1_C": (-10, 30), "P1_MPa": (0.1, 0.5),
                  "P2_MPa": (0.8, 2.0), "eta_s": (0.75, 0.88)},
    question_templates=[
        "R-134a at {T1_C}°C and {P1_MPa} MPa is compressed adiabatically to {P2_MPa} MPa (η_s = {eta_s_pct}%). Determine the work input and entropy generation per unit mass.",
    ],
    steps=_steps_b(_CMP_A, _CMP_B),
    difficulty="medium",
)

CMP_AA = ComponentTemplate(
    template_id="CMP-AA",
    component="compressor", depth="A", fluid="Air", id_prefix="CMP",
    param_ranges={"T1_C": (280, 350), "P1_MPa": (0.1, 0.2),
                  "P2_MPa": (0.5, 2.0), "eta_s": (0.78, 0.90)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4) at {T1_C} K and {P1_MPa} MPa enters an adiabatic compressor and is compressed to {P2_MPa} MPa with η_s = {eta_s_pct}%. Calculate the work input per unit mass.",
    ],
    steps=_steps_a(_CMP_A),
    difficulty="easy",
    notes="T1 in Kelvin for Air templates",
)

CMP_BA = ComponentTemplate(
    template_id="CMP-BA",
    component="compressor", depth="B", fluid="Air", id_prefix="CMP",
    param_ranges={"T1_C": (280, 350), "P1_MPa": (0.1, 0.2),
                  "P2_MPa": (0.5, 2.0), "eta_s": (0.78, 0.90)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)) at {T1_C} K and {P1_MPa} MPa is compressed adiabatically to {P2_MPa} MPa (η_s = {eta_s_pct}%). Calculate the work input and entropy generation per unit mass.",
    ],
    steps=_steps_b(_CMP_A, _CMP_B),
    difficulty="medium",
    notes="T1 in Kelvin for Air templates",
)

CMP_CA = ComponentTemplate(
    template_id="CMP-CA",
    component="compressor", depth="C", fluid="Air", id_prefix="CMP",
    param_ranges={"T1_C": (280, 350), "P1_MPa": (0.1, 0.2),
                  "P2_MPa": (0.5, 2.0), "eta_s": (0.78, 0.90)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)) at {T1_C} K and {P1_MPa} MPa enters an adiabatic compressor and exits at {P2_MPa} MPa with η_s = {eta_s_pct}%. Using T₀ = 298.15 K and P₀ = 0.1 MPa, determine the work input, entropy generation, exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_CMP_A, _CMP_B, _CMP_C),
    difficulty="hard",
    notes="T1 in Kelvin for Air templates",
)

# ── PUMP ──────────────────────────────────────────────────

PMP_AW = ComponentTemplate(
    template_id="PMP-AW",
    component="pump", depth="A", fluid="Water", id_prefix="PMP",
    param_ranges={"T1_C": (20, 80), "P1_MPa": (0.005, 0.1),
                  "P2_MPa": (1.0, 15.0), "eta_s": (0.70, 0.90)},
    question_templates=[
        "Liquid water at {T1_C}°C and {P1_MPa} MPa is pumped to {P2_MPa} MPa by an adiabatic pump with an isentropic efficiency of {eta_s_pct}%. Determine the work input per unit mass.",
        "An adiabatic pump increases the pressure of water from {P1_MPa} MPa to {P2_MPa} MPa. The inlet temperature is {T1_C}°C and the isentropic efficiency is {eta_s_pct}%. Calculate the specific work input.",
    ],
    steps=_steps_a(_PMP_A),
    difficulty="easy",
)

PMP_BW = ComponentTemplate(
    template_id="PMP-BW",
    component="pump", depth="B", fluid="Water", id_prefix="PMP",
    param_ranges={"T1_C": (20, 80), "P1_MPa": (0.005, 0.1),
                  "P2_MPa": (1.0, 15.0), "eta_s": (0.70, 0.90)},
    question_templates=[
        "Water at {T1_C}°C and {P1_MPa} MPa is pumped adiabatically to {P2_MPa} MPa with η_s = {eta_s_pct}%. Find the work input and entropy generation per unit mass.",
    ],
    steps=_steps_b(_PMP_A, _PMP_B),
    difficulty="medium",
)

PMP_CW = ComponentTemplate(
    template_id="PMP-CW",
    component="pump", depth="C", fluid="Water", id_prefix="PMP",
    param_ranges={"T1_C": (20, 80), "P1_MPa": (0.005, 0.1),
                  "P2_MPa": (1.0, 15.0), "eta_s": (0.70, 0.90)},
    question_templates=[
        "An adiabatic pump pressurizes water from {T1_C}°C and {P1_MPa} MPa to {P2_MPa} MPa with η_s = {eta_s_pct}%. The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the work input, entropy generation, exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_PMP_A, _PMP_B, _PMP_C),
    difficulty="hard",
)

# ── HEAT EXCHANGER ────────────────────────────────────────

HX_AW = ComponentTemplate(
    template_id="HX-AW",
    component="heat_exchanger", depth="A", fluid="Water", id_prefix="HX",
    param_ranges={"T_h_in": (60, 95), "T_h_out": (30, 70),
                  "T_c_in": (15, 40), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 5.0), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "In a counter-flow heat exchanger, hot water enters at {T_h_in}°C and {P_h_MPa} MPa with a mass flow rate of {m_h} kg/s, and exits at {T_h_out}°C. Cold water enters at {T_c_in}°C and {P_c_MPa} MPa with a mass flow rate of {m_c} kg/s. Both streams remain liquid. Determine the heat transfer rate and the cold stream exit temperature.",
        "Hot water ({m_h} kg/s) enters a heat exchanger at {T_h_in}°C / {P_h_MPa} MPa and exits at {T_h_out}°C. Cold water ({m_c} kg/s) enters at {T_c_in}°C / {P_c_MPa} MPa. Calculate Q̇ and T_c_out.",
    ],
    steps=_steps_a(_HX_A),
    difficulty="easy",
)

HX_BW = ComponentTemplate(
    template_id="HX-BW",
    component="heat_exchanger", depth="B", fluid="Water", id_prefix="HX",
    param_ranges={"T_h_in": (60, 95), "T_h_out": (30, 70),
                  "T_c_in": (15, 40), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 5.0), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "In a counter-flow heat exchanger, hot water enters at {T_h_in}°C and {P_h_MPa} MPa ({m_h} kg/s) and exits at {T_h_out}°C. Cold water enters at {T_c_in}°C and {P_c_MPa} MPa ({m_c} kg/s). Both streams remain liquid. Determine the heat transfer rate, cold outlet temperature, and the total entropy generation rate.",
    ],
    steps=_steps_b(_HX_A, _HX_B),
    difficulty="medium",
)

HX_CW = ComponentTemplate(
    template_id="HX-CW",
    component="heat_exchanger", depth="C", fluid="Water", id_prefix="HX",
    param_ranges={"T_h_in": (60, 95), "T_h_out": (30, 70),
                  "T_c_in": (15, 40), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 5.0), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "In a counter-flow heat exchanger, hot water enters at {T_h_in}°C / {P_h_MPa} MPa ({m_h} kg/s) and exits at {T_h_out}°C. Cold water enters at {T_c_in}°C / {P_c_MPa} MPa ({m_c} kg/s). Both streams remain liquid. The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the heat transfer rate, cold outlet temperature, entropy generation rate, exergy destruction rate, and second-law efficiency.",
    ],
    steps=_steps_c(_HX_A, _HX_B, _HX_C),
    difficulty="hard",
)

HX_AR = ComponentTemplate(
    template_id="HX-AR",
    component="heat_exchanger", depth="A", fluid="R134a", id_prefix="HX",
    param_ranges={"T_h_in": (60, 90), "T_h_out": (30, 60),
                  "T_c_in": (5, 25), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 1.5), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "In a heat exchanger, hot water enters at {T_h_in}°C / {P_h_MPa} MPa ({m_h} kg/s) and exits at {T_h_out}°C. Liquid R-134a enters the cold side at {T_c_in}°C / {P_c_MPa} MPa ({m_c} kg/s). Both streams remain liquid. Determine the heat transfer rate and the R-134a exit temperature.",
    ],
    steps=_steps_a(_HX_A),
    difficulty="medium",
    notes="Hot: Water, Cold: R134a (liquid)",
)

HX_BR = ComponentTemplate(
    template_id="HX-BR",
    component="heat_exchanger", depth="B", fluid="R134a", id_prefix="HX",
    param_ranges={"T_h_in": (60, 90), "T_h_out": (30, 60),
                  "T_c_in": (5, 25), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 1.5), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "Hot water at {T_h_in}°C / {P_h_MPa} MPa ({m_h} kg/s) heats liquid R-134a entering at {T_c_in}°C / {P_c_MPa} MPa ({m_c} kg/s). The hot water exits at {T_h_out}°C. Both streams remain liquid. Find the heat transfer rate, R-134a exit temperature, and entropy generation rate.",
    ],
    steps=_steps_b(_HX_A, _HX_B),
    difficulty="medium",
    notes="Hot: Water, Cold: R134a (liquid)",
)

HX_CR = ComponentTemplate(
    template_id="HX-CR",
    component="heat_exchanger", depth="C", fluid="R134a", id_prefix="HX",
    param_ranges={"T_h_in": (60, 90), "T_h_out": (30, 60),
                  "T_c_in": (5, 25), "P_h_MPa": (0.5, 5.0),
                  "P_c_MPa": (0.5, 1.5), "m_h": (0.5, 10.0), "m_c": (0.5, 10.0)},
    question_templates=[
        "Hot water at {T_h_in}°C / {P_h_MPa} MPa ({m_h} kg/s) heats liquid R-134a at {T_c_in}°C / {P_c_MPa} MPa ({m_c} kg/s) in a heat exchanger. The hot water exits at {T_h_out}°C. Both streams remain liquid. T₀ = 25°C, P₀ = 0.1 MPa. Determine Q̇, T_c_out, Ṡ_gen, Ẋ_dest, and η_II.",
    ],
    steps=_steps_c(_HX_A, _HX_B, _HX_C),
    difficulty="hard",
    notes="Hot: Water, Cold: R134a (liquid)",
)

# ── BOILER ────────────────────────────────────────────────

BLR_AW = ComponentTemplate(
    template_id="BLR-AW",
    component="boiler", depth="A", fluid="Water", id_prefix="BLR",
    param_ranges={"T_in_C": (30, 80), "P_MPa": (1.0, 15.0),
                  "T_out_C": (300, 600), "T_source_K": (800, 2000)},
    question_templates=[
        "Water enters a boiler as compressed liquid at {T_in_C}°C and {P_MPa} MPa. It exits as superheated steam at {T_out_C}°C (constant pressure). Determine the heat input per unit mass.",
        "A steam boiler operates at {P_MPa} MPa. Water enters at {T_in_C}°C and exits at {T_out_C}°C. Calculate the heat addition per unit mass.",
    ],
    steps=_steps_a(_BLR_A),
    difficulty="easy",
)

BLR_BW = ComponentTemplate(
    template_id="BLR-BW",
    component="boiler", depth="B", fluid="Water", id_prefix="BLR",
    param_ranges={"T_in_C": (30, 80), "P_MPa": (1.0, 15.0),
                  "T_out_C": (300, 600), "T_source_K": (800, 2000)},
    question_templates=[
        "Water enters a boiler at {T_in_C}°C and {P_MPa} MPa and exits as superheated steam at {T_out_C}°C. The heat is supplied by combustion gases at an average temperature of {T_source_K} K. Determine the heat input and entropy generation per unit mass.",
        "A boiler at {P_MPa} MPa receives water at {T_in_C}°C and produces steam at {T_out_C}°C. The heat source temperature is {T_source_K} K. Find q_in and s_gen per unit mass.",
    ],
    steps=_steps_b(_BLR_A, _BLR_B),
    difficulty="medium",
)

BLR_CW = ComponentTemplate(
    template_id="BLR-CW",
    component="boiler", depth="C", fluid="Water", id_prefix="BLR",
    param_ranges={"T_in_C": (30, 80), "P_MPa": (1.0, 15.0),
                  "T_out_C": (300, 600), "T_source_K": (800, 2000)},
    question_templates=[
        "Water enters a boiler as compressed liquid at {T_in_C}°C and {P_MPa} MPa. It exits as superheated steam at {T_out_C}°C (constant pressure). The heat is supplied by combustion gases at an average temperature of {T_source_K} K. The dead state is T₀ = 25°C (298.15 K), P₀ = 0.1 MPa. Determine the heat input, entropy generation, exergy destruction, and second-law efficiency per unit mass.",
    ],
    steps=_steps_c(_BLR_A, _BLR_B, _BLR_C),
    difficulty="hard",
)

# ── MIXING CHAMBER ────────────────────────────────────────

MIX_AW = ComponentTemplate(
    template_id="MIX-AW",
    component="mixing_chamber", depth="A", fluid="Water", id_prefix="MIX",
    param_ranges={"T1_C": (100, 300), "T2_C": (20, 80),
                  "P_MPa": (0.1, 2.0), "m1": (1.0, 10.0), "m2": (1.0, 10.0)},
    question_templates=[
        "In a mixing chamber, stream 1 (water at {T1_C}°C, {P_MPa} MPa, {m1} kg/s) mixes with stream 2 (water at {T2_C}°C, {P_MPa} MPa, {m2} kg/s). The mixing is adiabatic at constant pressure. Determine the exit temperature and mass flow rate.",
        "Two water streams mix adiabatically at {P_MPa} MPa. Stream 1: {T1_C}°C, {m1} kg/s. Stream 2: {T2_C}°C, {m2} kg/s. Find the exit temperature.",
    ],
    steps=_steps_a(_MIX_A),
    difficulty="easy",
)

MIX_BW = ComponentTemplate(
    template_id="MIX-BW",
    component="mixing_chamber", depth="B", fluid="Water", id_prefix="MIX",
    param_ranges={"T1_C": (100, 300), "T2_C": (20, 80),
                  "P_MPa": (0.1, 2.0), "m1": (1.0, 10.0), "m2": (1.0, 10.0)},
    question_templates=[
        "Water at {T1_C}°C ({m1} kg/s) mixes adiabatically with water at {T2_C}°C ({m2} kg/s) at a constant pressure of {P_MPa} MPa. Find the exit temperature and entropy generation rate.",
    ],
    steps=_steps_b(_MIX_A, _MIX_B),
    difficulty="medium",
)

MIX_CW = ComponentTemplate(
    template_id="MIX-CW",
    component="mixing_chamber", depth="C", fluid="Water", id_prefix="MIX",
    param_ranges={"T1_C": (100, 300), "T2_C": (20, 80),
                  "P_MPa": (0.1, 2.0), "m1": (1.0, 10.0), "m2": (1.0, 10.0)},
    question_templates=[
        "Two water streams mix adiabatically at {P_MPa} MPa in a mixing chamber. Stream 1: {T1_C}°C, {m1} kg/s. Stream 2: {T2_C}°C, {m2} kg/s. The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the exit temperature, entropy generation rate, exergy destruction rate, and second-law efficiency.",
    ],
    steps=_steps_c(_MIX_A, _MIX_B, _MIX_C),
    difficulty="hard",
)

# ── NOZZLE ────────────────────────────────────────────────

NOZ_AW = ComponentTemplate(
    template_id="NOZ-AW",
    component="nozzle", depth="A", fluid="Water", id_prefix="NOZ",
    param_ranges={"T1_C": (200, 500), "P1_MPa": (0.5, 5.0),
                  "P2_MPa": (0.1, 1.0), "V1": (10, 80), "eta_nozzle": (0.90, 0.98)},
    question_templates=[
        "Steam enters an adiabatic nozzle at {T1_C}°C, {P1_MPa} MPa with a velocity of {V1} m/s and exits at {P2_MPa} MPa. The nozzle isentropic efficiency is {eta_nozzle_pct}%. Determine the exit velocity.",
        "An adiabatic nozzle receives steam at {T1_C}°C / {P1_MPa} MPa with V₁ = {V1} m/s. The exit pressure is {P2_MPa} MPa and η_nozzle = {eta_nozzle_pct}%. Calculate the exit velocity.",
    ],
    steps=_steps_a(_NOZ_A),
    difficulty="easy",
)

NOZ_BW = ComponentTemplate(
    template_id="NOZ-BW",
    component="nozzle", depth="B", fluid="Water", id_prefix="NOZ",
    param_ranges={"T1_C": (200, 500), "P1_MPa": (0.5, 5.0),
                  "P2_MPa": (0.1, 1.0), "V1": (10, 80), "eta_nozzle": (0.90, 0.98)},
    question_templates=[
        "Steam enters an adiabatic nozzle at {T1_C}°C, {P1_MPa} MPa with V₁ = {V1} m/s and exits at {P2_MPa} MPa. The nozzle efficiency is {eta_nozzle_pct}%. Find the exit velocity and entropy generation per unit mass.",
    ],
    steps=_steps_b(_NOZ_A, _NOZ_B),
    difficulty="medium",
)

NOZ_CW = ComponentTemplate(
    template_id="NOZ-CW",
    component="nozzle", depth="C", fluid="Water", id_prefix="NOZ",
    param_ranges={"T1_C": (200, 500), "P1_MPa": (0.5, 5.0),
                  "P2_MPa": (0.1, 1.0), "V1": (10, 80), "eta_nozzle": (0.90, 0.98)},
    question_templates=[
        "Steam at {T1_C}°C / {P1_MPa} MPa enters an adiabatic nozzle at {V1} m/s and exits at {P2_MPa} MPa (η_nozzle = {eta_nozzle_pct}%). The dead state is T₀ = 25°C, P₀ = 0.1 MPa. Determine the exit velocity, entropy generation, exergy destruction, and second-law efficiency per unit mass.",
    ],
    steps=_steps_c(_NOZ_A, _NOZ_B, _NOZ_C),
    difficulty="hard",
)

NOZ_AA = ComponentTemplate(
    template_id="NOZ-AA",
    component="nozzle", depth="A", fluid="Air", id_prefix="NOZ",
    param_ranges={"T1_C": (400, 900), "P1_MPa": (0.3, 1.0),
                  "P2_MPa": (0.1, 0.3), "V1": (30, 100), "eta_nozzle": (0.92, 0.98)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4) enters an adiabatic nozzle at {T1_C} K and {P1_MPa} MPa with a velocity of {V1} m/s. The exit pressure is {P2_MPa} MPa and η_nozzle = {eta_nozzle_pct}%. Determine the exit velocity.",
    ],
    steps=_steps_a(_NOZ_A),
    difficulty="easy",
    notes="T1 in Kelvin for Air templates",
)

NOZ_BA = ComponentTemplate(
    template_id="NOZ-BA",
    component="nozzle", depth="B", fluid="Air", id_prefix="NOZ",
    param_ranges={"T1_C": (400, 900), "P1_MPa": (0.3, 1.0),
                  "P2_MPa": (0.1, 0.3), "V1": (30, 100), "eta_nozzle": (0.92, 0.98)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)) enters an adiabatic nozzle at {T1_C} K / {P1_MPa} MPa with V₁ = {V1} m/s. It exits at {P2_MPa} MPa with η_nozzle = {eta_nozzle_pct}%. Find the exit velocity and entropy generation.",
    ],
    steps=_steps_b(_NOZ_A, _NOZ_B),
    difficulty="medium",
    notes="T1 in Kelvin for Air templates",
)

NOZ_CA = ComponentTemplate(
    template_id="NOZ-CA",
    component="nozzle", depth="C", fluid="Air", id_prefix="NOZ",
    param_ranges={"T1_C": (400, 900), "P1_MPa": (0.3, 1.0),
                  "P2_MPa": (0.1, 0.3), "V1": (30, 100), "eta_nozzle": (0.92, 0.98)},
    question_templates=[
        "Air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)) at {T1_C} K / {P1_MPa} MPa enters an adiabatic nozzle at {V1} m/s and exits at {P2_MPa} MPa (η_nozzle = {eta_nozzle_pct}%). T₀ = 298.15 K, P₀ = 0.1 MPa. Calculate the exit velocity, entropy generation, exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_NOZ_A, _NOZ_B, _NOZ_C),
    difficulty="hard",
    notes="T1 in Kelvin for Air templates",
)

# ══════════════════════════════════════════════════════════
# MASTER TEMPLATE LIST & COUNTS
# ══════════════════════════════════════════════════════════

TIER2_TEMPLATES: list[ComponentTemplate] = [
    # Turbine: 18 questions (12 Water, 6 Air)
    TRB_AW, TRB_BW, TRB_CW,
    TRB_AA, TRB_BA, TRB_CA,
    # Compressor: 14 questions (5 Water, 4 R134a, 5 Air)
    CMP_AW, CMP_BW, CMP_CW,
    CMP_AR, CMP_BR,
    CMP_AA, CMP_BA, CMP_CA,
    # Pump: 10 questions (Water only)
    PMP_AW, PMP_BW, PMP_CW,
    # Heat exchanger: 18 questions (12 Water, 6 R134a)
    HX_AW, HX_BW, HX_CW,
    HX_AR, HX_BR, HX_CR,
    # Boiler: 14 questions (Water only)
    BLR_AW, BLR_BW, BLR_CW,
    # Mixing chamber: 12 questions (Water only)
    MIX_AW, MIX_BW, MIX_CW,
    # Nozzle: 14 questions (8 Water, 6 Air)
    NOZ_AW, NOZ_BW, NOZ_CW,
    NOZ_AA, NOZ_BA, NOZ_CA,
]

# Questions per template — total 100
TIER2_TEMPLATE_COUNTS: dict[str, int] = {
    # Turbine: 18 total (12W + 6A)
    "TRB-AW": 5, "TRB-BW": 4, "TRB-CW": 3,
    "TRB-AA": 2, "TRB-BA": 2, "TRB-CA": 2,
    # Compressor: 14 total (5W + 4R + 5A)
    "CMP-AW": 2, "CMP-BW": 2, "CMP-CW": 1,
    "CMP-AR": 2, "CMP-BR": 2,
    "CMP-AA": 2, "CMP-BA": 2, "CMP-CA": 1,
    # Pump: 10 total
    "PMP-AW": 3, "PMP-BW": 3, "PMP-CW": 4,
    # Heat exchanger: 18 total (12W + 6R)
    "HX-AW": 5, "HX-BW": 4, "HX-CW": 4,
    "HX-AR": 2, "HX-BR": 2, "HX-CR": 2,
    # Boiler: 14 total
    "BLR-AW": 4, "BLR-BW": 5, "BLR-CW": 5,
    # Mixing chamber: 12 total
    "MIX-AW": 4, "MIX-BW": 4, "MIX-CW": 4,
    # Nozzle: 14 total (8W + 6A)
    "NOZ-AW": 3, "NOZ-BW": 3, "NOZ-CW": 2,
    "NOZ-AA": 2, "NOZ-BA": 2, "NOZ-CA": 2,
}


def get_templates_by_component(component: str) -> list[ComponentTemplate]:
    return [t for t in TIER2_TEMPLATES if t.component == component]


def get_template_by_id(template_id: str) -> ComponentTemplate | None:
    for t in TIER2_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None


# Fluid code mapping for question IDs
FLUID_CODES = {"Water": "W", "R134a": "R", "Air": "A"}
