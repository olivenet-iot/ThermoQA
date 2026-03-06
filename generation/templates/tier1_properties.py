"""
Tier 1 property lookup question templates for ThermoQA.

Each template defines a category of questions with parameter ranges,
target properties, physics constraints, and multiple question phrasings.
"""

from dataclasses import dataclass, field


@dataclass
class PropertyTemplate:
    template_id: str
    category: str               # phase name from taxonomy
    subcategory: str            # specific variant within category
    given_params: list          # e.g., ["T_C", "P_kPa"]
    target_properties: list     # e.g., ["h_kJ_kg", "s_kJ_kgK"]
    param_ranges: dict          # e.g., {"T_C": (120, 600), "P_kPa": (100, 15000)}
    question_templates: list    # list of format strings with {placeholders}
    constraints: list           # e.g., ["T_C > T_sat(P_kPa) + 10"]
    difficulty: str = "medium"
    notes: str = ""


# === SUBCOOLED LIQUID (SL) — 10 questions, 3 templates ===

SL_MULTI = PropertyTemplate(
    template_id="SL-MULTI-001",
    category="subcooled_liquid",
    subcategory="multi_property",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"],
    param_ranges={"T_C": (20, 300), "P_kPa": (500, 15000)},
    question_templates=[
        "Determine the specific enthalpy (h), specific entropy (s), and specific volume (v) of compressed liquid water at {T_C}\u00b0C and {P_kPa} kPa.",
        "Water exists as a compressed liquid at {T_C}\u00b0C and {P_kPa} kPa. Calculate h, s, and v.",
        "Find the specific enthalpy, entropy, and specific volume of subcooled water at a temperature of {T_C}\u00b0C and pressure of {P_kPa} kPa.",
    ],
    constraints=["T_C < T_sat(P_kPa) - 5"],
    difficulty="easy",
)

SL_U_RHO = PropertyTemplate(
    template_id="SL-URHO-001",
    category="subcooled_liquid",
    subcategory="u_and_rho",
    given_params=["T_C", "P_kPa"],
    target_properties=["u_kJ_kg", "rho_kg_m3"],
    param_ranges={"T_C": (20, 300), "P_kPa": (500, 15000)},
    question_templates=[
        "What are the specific internal energy (u) and density (\u03c1) of liquid water at {T_C}\u00b0C and {P_kPa} kPa?",
        "Calculate the internal energy and density of compressed liquid water at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=["T_C < T_sat(P_kPa) - 5"],
    difficulty="easy",
)

SL_SINGLE = PropertyTemplate(
    template_id="SL-SING-001",
    category="subcooled_liquid",
    subcategory="single_property",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg"],
    param_ranges={"T_C": (20, 300), "P_kPa": (500, 15000)},
    question_templates=[
        "What is the specific enthalpy of liquid water at {T_C}\u00b0C and {P_kPa} kPa?",
        "Determine the enthalpy of compressed water at a temperature of {T_C}\u00b0C and a pressure of {P_kPa} kPa.",
    ],
    constraints=["T_C < T_sat(P_kPa) - 5"],
    difficulty="easy",
)


# === SATURATED LIQUID (SF) — 12 questions, 4 templates ===

SF_P_ALL = PropertyTemplate(
    template_id="SF-PALL-001",
    category="saturated_liquid",
    subcategory="given_P_all_props",
    given_params=["P_kPa"],
    target_properties=["T_sat_C", "h_f_kJ_kg", "s_f_kJ_kgK", "v_f_m3_kg"],
    param_ranges={"P_kPa": (100, 10000)},
    question_templates=[
        "At a pressure of {P_kPa} kPa, determine the saturation temperature and the specific enthalpy, entropy, and specific volume of saturated liquid water.",
        "Find T_sat, h_f, s_f, and v_f for saturated water at {P_kPa} kPa.",
        "Water is at saturation as a liquid at {P_kPa} kPa. What are the saturation temperature, specific enthalpy, specific entropy, and specific volume?",
    ],
    constraints=[],
    difficulty="easy",
)

SF_T_ALL = PropertyTemplate(
    template_id="SF-TALL-001",
    category="saturated_liquid",
    subcategory="given_T_all_props",
    given_params=["T_C"],
    target_properties=["P_sat_kPa", "h_f_kJ_kg", "s_f_kJ_kgK", "v_f_m3_kg"],
    param_ranges={"T_C": (100, 311)},
    question_templates=[
        "At a saturation temperature of {T_C}\u00b0C, find the saturation pressure and the properties h_f, s_f, and v_f of saturated liquid water.",
        "Determine P_sat, h_f, s_f, and v_f for saturated water at {T_C}\u00b0C.",
    ],
    constraints=[],
    difficulty="easy",
)

SF_P_SINGLE = PropertyTemplate(
    template_id="SF-PSNG-001",
    category="saturated_liquid",
    subcategory="given_P_single",
    given_params=["P_kPa"],
    target_properties=["h_f_kJ_kg"],
    param_ranges={"P_kPa": (100, 10000)},
    question_templates=[
        "What is the specific enthalpy of saturated liquid water at {P_kPa} kPa?",
        "Determine h_f for water at a saturation pressure of {P_kPa} kPa.",
    ],
    constraints=[],
    difficulty="easy",
)

SF_T_SINGLE = PropertyTemplate(
    template_id="SF-TSNG-001",
    category="saturated_liquid",
    subcategory="given_T_single",
    given_params=["T_C"],
    target_properties=["P_sat_kPa", "h_f_kJ_kg"],
    param_ranges={"T_C": (100, 311)},
    question_templates=[
        "What is the saturation pressure and specific enthalpy of saturated liquid water at {T_C}\u00b0C?",
        "For saturated liquid water at {T_C}\u00b0C, determine P_sat and h_f.",
    ],
    constraints=[],
    difficulty="medium",
)


# === WET STEAM (WS) — 18 questions, 5 templates ===

WS_PX = PropertyTemplate(
    template_id="WS-PX-001",
    category="wet_steam",
    subcategory="given_P_x",
    given_params=["P_kPa", "x"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"],
    param_ranges={"P_kPa": (100, 8000), "x": (0.1, 0.95)},
    question_templates=[
        "A wet steam mixture at {P_kPa} kPa has a quality of {x}. Calculate the specific enthalpy, entropy, and specific volume.",
        "Determine h, s, and v for steam at {P_kPa} kPa with a quality (dryness fraction) of {x}.",
        "Steam at {P_kPa} kPa exists as a two-phase mixture with quality x = {x}. Find its specific enthalpy, specific entropy, and specific volume.",
    ],
    constraints=["0.1 <= x <= 0.95"],
    difficulty="medium",
)

WS_TX = PropertyTemplate(
    template_id="WS-TX-001",
    category="wet_steam",
    subcategory="given_T_x",
    given_params=["T_C", "x"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg", "P_sat_kPa"],
    param_ranges={"T_C": (100, 295), "x": (0.1, 0.95)},
    question_templates=[
        "Wet steam at {T_C}\u00b0C has a quality of {x}. Determine the saturation pressure, specific enthalpy, entropy, and specific volume.",
        "A two-phase water mixture exists at {T_C}\u00b0C with quality x = {x}. Find P_sat, h, s, and v.",
    ],
    constraints=["0.1 <= x <= 0.95"],
    difficulty="medium",
)

WS_PH_INV = PropertyTemplate(
    template_id="WS-PH-001",
    category="wet_steam",
    subcategory="inverse_P_h",
    given_params=["P_kPa", "h_kJ_kg"],
    target_properties=["x", "T_sat_C", "s_kJ_kgK"],
    param_ranges={"P_kPa": (100, 8000), "h_kJ_kg": (500, 2700)},
    question_templates=[
        "Steam at {P_kPa} kPa has a specific enthalpy of {h_kJ_kg:.1f} kJ/kg. Determine the quality, saturation temperature, and specific entropy.",
        "At a pressure of {P_kPa} kPa, steam has h = {h_kJ_kg:.1f} kJ/kg. Find the quality (x), T_sat, and s.",
    ],
    constraints=["h_f < h_kJ_kg < h_g"],
    difficulty="hard",
)

WS_PS_INV = PropertyTemplate(
    template_id="WS-PS-001",
    category="wet_steam",
    subcategory="inverse_P_s",
    given_params=["P_kPa", "s_kJ_kgK"],
    target_properties=["x", "T_sat_C", "h_kJ_kg"],
    param_ranges={"P_kPa": (100, 8000), "s_kJ_kgK": (1.5, 7.0)},
    question_templates=[
        "Steam at {P_kPa} kPa has a specific entropy of {s_kJ_kgK:.4f} kJ/(kg\u00b7K). Find the quality, saturation temperature, and specific enthalpy.",
        "At {P_kPa} kPa, steam has s = {s_kJ_kgK:.4f} kJ/(kg\u00b7K). Determine x, T_sat, and h.",
    ],
    constraints=["s_f < s_kJ_kgK < s_g"],
    difficulty="hard",
)

WS_SINGLE = PropertyTemplate(
    template_id="WS-SING-001",
    category="wet_steam",
    subcategory="single_property",
    given_params=["P_kPa", "x"],
    target_properties=["h_kJ_kg"],
    param_ranges={"P_kPa": (100, 8000), "x": (0.1, 0.95)},
    question_templates=[
        "What is the specific enthalpy of a steam-water mixture at {P_kPa} kPa with quality {x}?",
        "Calculate the enthalpy of wet steam at {P_kPa} kPa and quality x = {x}.",
    ],
    constraints=["0.1 <= x <= 0.95"],
    difficulty="medium",
)


# === SATURATED VAPOR (SV) — 10 questions, 3 templates ===

SV_P_ALL = PropertyTemplate(
    template_id="SV-PALL-001",
    category="saturated_vapor",
    subcategory="given_P_all_props",
    given_params=["P_kPa"],
    target_properties=["T_sat_C", "h_g_kJ_kg", "s_g_kJ_kgK", "v_g_m3_kg"],
    param_ranges={"P_kPa": (100, 10000)},
    question_templates=[
        "At {P_kPa} kPa, determine the saturation temperature and the specific enthalpy, entropy, and specific volume of saturated steam.",
        "Find T_sat, h_g, s_g, and v_g for saturated vapor (steam) at {P_kPa} kPa.",
        "Saturated steam exists at a pressure of {P_kPa} kPa. What are T_sat, h_g, s_g, and v_g?",
    ],
    constraints=[],
    difficulty="easy",
)

SV_T_ALL = PropertyTemplate(
    template_id="SV-TALL-001",
    category="saturated_vapor",
    subcategory="given_T_all_props",
    given_params=["T_C"],
    target_properties=["P_sat_kPa", "h_g_kJ_kg", "s_g_kJ_kgK", "v_g_m3_kg"],
    param_ranges={"T_C": (100, 311)},
    question_templates=[
        "At a saturation temperature of {T_C}\u00b0C, find P_sat and the properties h_g, s_g, and v_g of saturated steam.",
        "Determine the saturation pressure and saturated vapor properties (h_g, s_g, v_g) of steam at {T_C}\u00b0C.",
    ],
    constraints=[],
    difficulty="easy",
)

SV_SINGLE = PropertyTemplate(
    template_id="SV-SING-001",
    category="saturated_vapor",
    subcategory="single_property",
    given_params=["P_kPa"],
    target_properties=["h_g_kJ_kg"],
    param_ranges={"P_kPa": (100, 10000)},
    question_templates=[
        "What is the specific enthalpy of saturated steam at {P_kPa} kPa?",
        "Determine h_g for saturated water vapor at a pressure of {P_kPa} kPa.",
    ],
    constraints=[],
    difficulty="easy",
)


# === SUPERHEATED VAPOR (SH) — 20 questions, 4 templates ===

SH_MULTI = PropertyTemplate(
    template_id="SH-MULTI-001",
    category="superheated_vapor",
    subcategory="multi_property",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"],
    param_ranges={"T_C": (120, 600), "P_kPa": (100, 15000)},
    question_templates=[
        "Determine the specific enthalpy (h), specific entropy (s), and specific volume (v) of superheated steam at {T_C}\u00b0C and {P_kPa} kPa.",
        "Steam at {T_C}\u00b0C and {P_kPa} kPa is superheated. Calculate h, s, and v.",
        "Find the specific enthalpy, entropy, and specific volume of steam at a temperature of {T_C}\u00b0C and pressure of {P_kPa} kPa.",
        "Superheated steam enters a system at {P_kPa} kPa and {T_C}\u00b0C. What are its thermodynamic properties (h, s, v)?",
    ],
    constraints=["T_C > T_sat(P_kPa) + 10", "P_kPa < P_crit"],
    difficulty="easy",
)

SH_H_ONLY = PropertyTemplate(
    template_id="SH-HONLY-001",
    category="superheated_vapor",
    subcategory="h_only",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg"],
    param_ranges={"T_C": (120, 600), "P_kPa": (100, 15000)},
    question_templates=[
        "What is the specific enthalpy of steam at {T_C}\u00b0C and {P_kPa} kPa?",
        "Calculate the enthalpy of superheated water vapor at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=["T_C > T_sat(P_kPa) + 10", "P_kPa < P_crit"],
    difficulty="easy",
)

SH_SV = PropertyTemplate(
    template_id="SH-SV-001",
    category="superheated_vapor",
    subcategory="s_and_v",
    given_params=["T_C", "P_kPa"],
    target_properties=["s_kJ_kgK", "v_m3_kg"],
    param_ranges={"T_C": (120, 600), "P_kPa": (100, 15000)},
    question_templates=[
        "Determine the specific entropy and specific volume of steam at {T_C}\u00b0C and {P_kPa} kPa.",
        "For superheated steam at {P_kPa} kPa and {T_C}\u00b0C, calculate s and v.",
    ],
    constraints=["T_C > T_sat(P_kPa) + 10", "P_kPa < P_crit"],
    difficulty="easy",
)

SH_U_RHO_V = PropertyTemplate(
    template_id="SH-URV-001",
    category="superheated_vapor",
    subcategory="u_rho_v",
    given_params=["T_C", "P_kPa"],
    target_properties=["u_kJ_kg", "rho_kg_m3", "v_m3_kg"],
    param_ranges={"T_C": (120, 600), "P_kPa": (100, 15000)},
    question_templates=[
        "What are the specific internal energy (u), density (\u03c1), and specific volume (v) of steam at {T_C}\u00b0C and {P_kPa} kPa?",
        "Calculate u, \u03c1, and v for superheated steam at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=["T_C > T_sat(P_kPa) + 10", "P_kPa < P_crit"],
    difficulty="medium",
)


# === SUPERCRITICAL (SC) — 10 questions, 2 templates ===

SC_HSV = PropertyTemplate(
    template_id="SC-HSV-001",
    category="supercritical",
    subcategory="h_s_v",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"],
    param_ranges={"T_C": (375, 600), "P_kPa": (22500, 35000)},
    question_templates=[
        "Determine h, s, and v for water at {T_C}\u00b0C and {P_kPa} kPa. Note: this state is above the critical point.",
        "Water exists at {T_C}\u00b0C and {P_kPa} kPa. Calculate the specific enthalpy, entropy, and specific volume.",
        "Find the thermodynamic properties (h, s, v) of water at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=["T_C > 373.946", "P_kPa > 22064"],
    difficulty="hard",
)

SC_ALL = PropertyTemplate(
    template_id="SC-ALL-001",
    category="supercritical",
    subcategory="all_props_phase",
    given_params=["T_C", "P_kPa"],
    target_properties=["h_kJ_kg", "s_kJ_kgK", "v_m3_kg", "u_kJ_kg", "rho_kg_m3", "phase_name"],
    param_ranges={"T_C": (375, 600), "P_kPa": (22500, 35000)},
    question_templates=[
        "Water is at {T_C}\u00b0C and {P_kPa} kPa. Determine all thermodynamic properties (h, s, v, u, \u03c1) and identify the phase.",
        "At {T_C}\u00b0C and {P_kPa} kPa, find h, s, v, u, density, and the phase of water.",
    ],
    constraints=["T_C > 373.946", "P_kPa > 22064"],
    difficulty="hard",
)


# === PHASE DETERMINATION (PD) — 15 questions, 3 templates ===

PD_OBVIOUS = PropertyTemplate(
    template_id="PD-OBV-001",
    category="phase_determination",
    subcategory="obvious",
    given_params=["T_C", "P_kPa"],
    target_properties=["phase_name"],
    param_ranges={"T_C": (20, 600), "P_kPa": (50, 15000)},
    question_templates=[
        "Determine the phase of water at {T_C}\u00b0C and {P_kPa} kPa.",
        "What phase is water in at a temperature of {T_C}\u00b0C and a pressure of {P_kPa} kPa?",
        "Water exists at {T_C}\u00b0C and {P_kPa} kPa. Identify its phase.",
    ],
    constraints=[],
    difficulty="easy",
    notes="Clearly subcooled or clearly superheated cases.",
)

PD_NEAR_BOUNDARY = PropertyTemplate(
    template_id="PD-NEAR-001",
    category="phase_determination",
    subcategory="near_boundary",
    given_params=["T_C", "P_kPa"],
    target_properties=["phase_name"],
    param_ranges={"T_C": (100, 370), "P_kPa": (100, 20000)},
    question_templates=[
        "Water is at {T_C}\u00b0C and {P_kPa} kPa. What is its thermodynamic phase?",
        "Identify the phase of water at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=[],
    difficulty="medium",
    notes="Temperature within 2-5C of T_sat. Tests precise knowledge of saturation curve.",
)

PD_TRICKY = PropertyTemplate(
    template_id="PD-TRICK-001",
    category="phase_determination",
    subcategory="tricky",
    given_params=["T_C", "P_kPa"],
    target_properties=["phase_name"],
    param_ranges={"T_C": (250, 600), "P_kPa": (10000, 35000)},
    question_templates=[
        "At {T_C}\u00b0C and {P_kPa} kPa, what phase is water in?",
        "Determine the thermodynamic phase of water at {T_C}\u00b0C and {P_kPa} kPa.",
    ],
    constraints=[],
    difficulty="hard",
    notes="Supercritical, near-critical, or high-pressure subcooled cases.",
)


# === INVERSE LOOKUPS (IL) — 15 questions, 5 templates ===

IL_PH_T = PropertyTemplate(
    template_id="IL-PHT-001",
    category="inverse_lookups",
    subcategory="P_h_to_T",
    given_params=["P_kPa", "h_kJ_kg"],
    target_properties=["T_C", "phase_name"],
    param_ranges={"P_kPa": (100, 15000), "h_kJ_kg": (100, 3600)},
    question_templates=[
        "Steam at {P_kPa} kPa has a specific enthalpy of {h_kJ_kg:.1f} kJ/kg. What is its temperature and phase?",
        "At a pressure of {P_kPa} kPa, water has h = {h_kJ_kg:.1f} kJ/kg. Determine the temperature and identify the phase.",
    ],
    constraints=[],
    difficulty="medium",
)

IL_PS_T = PropertyTemplate(
    template_id="IL-PST-001",
    category="inverse_lookups",
    subcategory="P_s_to_T",
    given_params=["P_kPa", "s_kJ_kgK"],
    target_properties=["T_C", "phase_name"],
    param_ranges={"P_kPa": (100, 15000), "s_kJ_kgK": (0.5, 8.0)},
    question_templates=[
        "Water at {P_kPa} kPa has a specific entropy of {s_kJ_kgK:.4f} kJ/(kg\u00b7K). Find its temperature and phase.",
        "At {P_kPa} kPa, steam has s = {s_kJ_kgK:.4f} kJ/(kg\u00b7K). What are the temperature and phase?",
    ],
    constraints=[],
    difficulty="medium",
)

IL_PH_SV = PropertyTemplate(
    template_id="IL-PHSV-001",
    category="inverse_lookups",
    subcategory="P_h_to_s_v",
    given_params=["P_kPa", "h_kJ_kg"],
    target_properties=["s_kJ_kgK", "v_m3_kg", "T_C", "phase_name"],
    param_ranges={"P_kPa": (200, 12000), "h_kJ_kg": (200, 3500)},
    question_templates=[
        "Water at {P_kPa} kPa has a specific enthalpy of {h_kJ_kg:.1f} kJ/kg. Determine s, v, the temperature, and the phase.",
        "At {P_kPa} kPa, water has h = {h_kJ_kg:.1f} kJ/kg. Find the specific entropy, specific volume, temperature, and phase.",
    ],
    constraints=[],
    difficulty="hard",
)

IL_HS_TP = PropertyTemplate(
    template_id="IL-HSTP-001",
    category="inverse_lookups",
    subcategory="h_s_to_T_P",
    given_params=["h_kJ_kg", "s_kJ_kgK"],
    target_properties=["T_C", "P_kPa", "phase_name"],
    param_ranges={"h_kJ_kg": (100, 3600), "s_kJ_kgK": (0.5, 8.0)},
    question_templates=[
        "Water has a specific enthalpy of {h_kJ_kg:.1f} kJ/kg and specific entropy of {s_kJ_kgK:.4f} kJ/(kg\u00b7K). Determine the temperature, pressure, and phase.",
        "Given h = {h_kJ_kg:.1f} kJ/kg and s = {s_kJ_kgK:.4f} kJ/(kg\u00b7K), find T, P, and the phase of water.",
    ],
    constraints=[],
    difficulty="hard",
)

IL_PH_X = PropertyTemplate(
    template_id="IL-PHX-001",
    category="inverse_lookups",
    subcategory="P_h_to_x",
    given_params=["P_kPa", "h_kJ_kg"],
    target_properties=["x", "T_sat_C"],
    param_ranges={"P_kPa": (100, 8000), "h_kJ_kg": (500, 2700)},
    question_templates=[
        "A steam-water mixture at {P_kPa} kPa has a specific enthalpy of {h_kJ_kg:.1f} kJ/kg. What is the quality and saturation temperature?",
        "At {P_kPa} kPa, wet steam has h = {h_kJ_kg:.1f} kJ/kg. Determine the quality (x) and T_sat.",
    ],
    constraints=["h_f < h_kJ_kg < h_g"],
    difficulty="hard",
)


# === MASTER TEMPLATE LIST ===

TIER1_TEMPLATES = [
    # Subcooled liquid (10 questions across 3 templates)
    SL_MULTI, SL_U_RHO, SL_SINGLE,
    # Saturated liquid (12 questions across 4 templates)
    SF_P_ALL, SF_T_ALL, SF_P_SINGLE, SF_T_SINGLE,
    # Wet steam (18 questions across 4 templates)
    WS_PX, WS_TX, WS_PH_INV, WS_PS_INV,
    # Saturated vapor (10 questions across 3 templates)
    SV_P_ALL, SV_T_ALL, SV_SINGLE,
    # Superheated vapor (20 questions across 4 templates)
    SH_MULTI, SH_H_ONLY, SH_SV, SH_U_RHO_V,
    # Supercritical (10 questions across 2 templates)
    SC_HSV, SC_ALL,
    # Phase determination (15 questions across 3 templates)
    PD_OBVIOUS, PD_NEAR_BOUNDARY, PD_TRICKY,
    # Inverse lookups (15 questions across 5 templates)
    IL_PH_T, IL_PS_T, IL_PH_SV, IL_HS_TP, IL_PH_X,
]

# Question count allocation per template
# Maps template_id -> number of questions to generate
TEMPLATE_COUNTS = {
    # Subcooled: 10 total
    "SL-MULTI-001": 4,
    "SL-URHO-001": 3,
    "SL-SING-001": 3,
    # Saturated liquid: 12 total
    "SF-PALL-001": 4,
    "SF-TALL-001": 3,
    "SF-PSNG-001": 3,
    "SF-TSNG-001": 2,
    # Wet steam: 18 total
    "WS-PX-001": 8,
    "WS-TX-001": 3,
    "WS-PH-001": 4,
    "WS-PS-001": 3,
    # Saturated vapor: 10 total
    "SV-PALL-001": 4,
    "SV-TALL-001": 3,
    "SV-SING-001": 3,
    # Superheated: 20 total
    "SH-MULTI-001": 8,
    "SH-HONLY-001": 4,
    "SH-SV-001": 4,
    "SH-URV-001": 4,
    # Supercritical: 10 total
    "SC-HSV-001": 5,
    "SC-ALL-001": 5,
    # Phase determination: 15 total
    "PD-OBV-001": 6,
    "PD-NEAR-001": 5,
    "PD-TRICK-001": 4,
    # Inverse lookups: 15 total
    "IL-PHT-001": 4,
    "IL-PST-001": 4,
    "IL-PHSV-001": 3,
    "IL-HSTP-001": 2,
    "IL-PHX-001": 2,
}


def get_templates_by_category(category: str) -> list:
    """Return all templates matching the given category name."""
    return [t for t in TIER1_TEMPLATES if t.category == category]


def get_template_by_id(template_id: str) -> PropertyTemplate | None:
    """Return the template with the given ID, or None."""
    for t in TIER1_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None
