"""
Tier 3 cycle analysis question templates for ThermoQA.

Each template defines a cycle_type × depth combination with
parameter ranges, step definitions with weights, and multiple question phrasings.
7 cycles × 3 depths = 21 templates, ~95 questions total.
"""

from dataclasses import dataclass, field


@dataclass
class CycleTemplate:
    template_id: str       # "RNK-I-A", "VCR-A-C"
    cycle_type: str        # "RNK-I", "RNK-A", "RNK-RH", "BRY-I", "BRY-A", "BRY-RG", "VCR-A"
    depth: str             # "A", "B", "C"
    fluid: str             # "Water", "Air", "R-134a"
    id_prefix: str         # "RNK-I", "VCR-A" etc.
    fluid_code: str        # "WA", "AR", "RF"
    param_ranges: dict
    question_templates: list[str]
    steps: list[dict]      # [{id, formula, unit, weight}, ...]
    difficulty: str
    notes: str = ""


# ── Fluid codes ──────────────────────────────────────────
TIER3_FLUID_CODES = {"Water": "WA", "Air": "AR", "R-134a": "RF"}


# ── Helper: build step lists by depth ──────────────────────
def _steps_a(a):
    return list(a)

def _steps_b(a, b):
    return list(a) + list(b)

def _steps_c(a, b, c):
    return list(a) + list(b) + list(c)


# ══════════════════════════════════════════════════════════
# STEP DEFINITIONS PER CYCLE
# Weight 1: state properties
# Weight 2: component quantities
# Weight 3: cycle results
# Weight 4: critical discriminator (x4 in VCR)
# ══════════════════════════════════════════════════════════

# ── RNK-I (Ideal Rankine, 4 states) ──────────────────────

_RNKI_A = [
    {"id": "h1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "CoolProp(s=s1, P=P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "CoolProp(s=s3, P=P_cond)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_pump", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "h3 - h2", "unit": "kJ/kg", "weight": 2},
    {"id": "w_turb", "formula": "h3 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_turb - w_pump", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "w_net / q_in", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_RNKI_B = [
    {"id": "s1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s2", "formula": "s1 (isentropic pump)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s4", "formula": "s3 (isentropic turbine)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s_gen_pump", "formula": "0 (ideal)", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_boiler", "formula": "(s3-s2) - q_in/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_turb", "formula": "0 (ideal)", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cond", "formula": "(s1-s4) + q_out/T_sink", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_RNKI_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_boiler", "formula": "T0 * s_gen_boiler", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cond", "formula": "T0 * s_gen_cond", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── RNK-A (Actual Rankine, 4+2s states) ─────────────────

_RNKA_A = [
    {"id": "h1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2s", "formula": "CoolProp(s=s1, P=P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "h1 + (h2s-h1)/eta_pump", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4s", "formula": "CoolProp(s=s3, P=P_cond)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "h3 - eta_turb*(h3-h4s)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_pump", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "h3 - h2", "unit": "kJ/kg", "weight": 2},
    {"id": "w_turb", "formula": "h3 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_turb - w_pump", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "w_net / q_in", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_RNKA_B = [
    {"id": "s1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s2", "formula": "CoolProp(h=h2, P=P_boiler)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s4", "formula": "CoolProp(h=h4, P=P_cond)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s_gen_pump", "formula": "s2 - s1", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_boiler", "formula": "(s3-s2) - q_in/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_turb", "formula": "s4 - s3", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cond", "formula": "(s1-s4) + q_out/T_sink", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_RNKA_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_pump", "formula": "T0 * s_gen_pump", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_boiler", "formula": "T0 * s_gen_boiler", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_turb", "formula": "T0 * s_gen_turb", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cond", "formula": "T0 * s_gen_cond", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── RNK-RH (Reheat Rankine, 6+3s states) ────────────────

_RNKRH_A = [
    {"id": "h1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2s", "formula": "CoolProp(s=s1, P=P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "h1 + (h2s-h1)/eta_pump", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "h3 - eta_HPT*(h3-h4s)", "unit": "kJ/kg", "weight": 1},
    {"id": "h5", "formula": "CoolProp(T5, P_reheat)", "unit": "kJ/kg", "weight": 1},
    {"id": "h6", "formula": "h5 - eta_LPT*(h5-h6s)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_pump", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "(h3-h2) + (h5-h4)", "unit": "kJ/kg", "weight": 2},
    {"id": "w_HPT", "formula": "h3 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "w_LPT", "formula": "h5 - h6", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_HPT + w_LPT - w_pump", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "w_net / q_in", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_RNKRH_B = [
    {"id": "s1", "formula": "CoolProp(Q=0, P=P_cond)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s2", "formula": "CoolProp(h=h2, P=P_boiler)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s3", "formula": "CoolProp(T3, P_boiler)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s4", "formula": "CoolProp(h=h4, P_reheat)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s5", "formula": "CoolProp(T5, P_reheat)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s6", "formula": "CoolProp(h=h6, P=P_cond)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s_gen_pump", "formula": "s2 - s1", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_boiler", "formula": "(s3-s2) - q_boiler/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_HPT", "formula": "s4 - s3", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_reheater", "formula": "(s5-s4) - q_reheat/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_LPT", "formula": "s6 - s5", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cond", "formula": "(s1-s6) + q_out/T_sink", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_RNKRH_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef5", "formula": "(h5-h0) - T0*(s5-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef6", "formula": "(h6-h0) - T0*(s6-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_pump", "formula": "T0 * s_gen_pump", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_boiler", "formula": "T0 * s_gen_boiler", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_HPT", "formula": "T0 * s_gen_HPT", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_reheater", "formula": "T0 * s_gen_reheater", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_LPT", "formula": "T0 * s_gen_LPT", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cond", "formula": "T0 * s_gen_cond", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── BRY-I (Ideal Brayton, 4 states) ─────────────────────

_BRYI_A = [
    {"id": "h1", "formula": "cp * T1", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "cp * T2 (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "cp * T3", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "cp * T4 (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_comp", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "h3 - h2", "unit": "kJ/kg", "weight": 2},
    {"id": "w_turb", "formula": "h3 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_turb - w_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "1 - 1/r_p^((k-1)/k)", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_BRYI_B = [
    {"id": "s1", "formula": "cp*ln(T1/T0) - R*ln(P1/P0)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s2", "formula": "s1 (isentropic)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s3", "formula": "cp*ln(T3/T0) - R*ln(P2/P0)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s4", "formula": "s3 (isentropic)", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s_gen_comp", "formula": "0 (ideal)", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cc", "formula": "(s3-s2) - q_in/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_turb", "formula": "0 (ideal)", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_hr", "formula": "(s1-s4) + q_out/T_sink", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_BRYI_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_cc", "formula": "T0 * s_gen_cc", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_hr", "formula": "T0 * s_gen_hr", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── BRY-A (Actual Brayton, 4+2s states) ─────────────────

_BRYA_A = [
    {"id": "h1", "formula": "cp * T1", "unit": "kJ/kg", "weight": 1},
    {"id": "h2s", "formula": "cp * T2s (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "h1 + (h2s-h1)/eta_comp", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "cp * T3", "unit": "kJ/kg", "weight": 1},
    {"id": "h4s", "formula": "cp * T4s (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "h3 - eta_turb*(h3-h4s)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_comp", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "h3 - h2", "unit": "kJ/kg", "weight": 2},
    {"id": "w_turb", "formula": "h3 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_turb - w_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "w_net / q_in", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_BRYA_B = list(_BRYI_B)  # same structure; s_gen_comp/turb nonzero for actual
_BRYA_B[4] = {"id": "s_gen_comp", "formula": "s2 - s1 (>0)", "unit": "kJ/(kg·K)", "weight": 2}
_BRYA_B[6] = {"id": "s_gen_turb", "formula": "s4 - s3 (>0)", "unit": "kJ/(kg·K)", "weight": 2}

_BRYA_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_comp", "formula": "T0 * s_gen_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cc", "formula": "T0 * s_gen_cc", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_turb", "formula": "T0 * s_gen_turb", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_hr", "formula": "T0 * s_gen_hr", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── BRY-RG (Regenerative Brayton, 6+2s states) ──────────
# States: 1-comp inlet, 2-comp exit, 3-regen cold exit, 4-turb inlet, 5-turb exit, 6-regen hot exit

_BRYRG_A = [
    {"id": "h1", "formula": "cp * T1", "unit": "kJ/kg", "weight": 1},
    {"id": "h2s", "formula": "cp * T2s (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "h2", "formula": "h1 + (h2s-h1)/eta_comp", "unit": "kJ/kg", "weight": 1},
    {"id": "h3", "formula": "cp * T3 (regen cold exit)", "unit": "kJ/kg", "weight": 1},
    {"id": "h4", "formula": "cp * T4 (turb inlet)", "unit": "kJ/kg", "weight": 1},
    {"id": "h5s", "formula": "cp * T5s (isentropic)", "unit": "kJ/kg", "weight": 1},
    {"id": "h5", "formula": "h4 - eta_turb*(h4-h5s)", "unit": "kJ/kg", "weight": 1},
    {"id": "h6", "formula": "cp * T6 (regen hot exit)", "unit": "kJ/kg", "weight": 1},
    {"id": "w_comp", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_in", "formula": "h4 - h3", "unit": "kJ/kg", "weight": 2},
    {"id": "w_turb", "formula": "h4 - h5", "unit": "kJ/kg", "weight": 2},
    {"id": "w_net", "formula": "w_turb - w_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "eta_th", "formula": "w_net / q_in", "unit": "-", "weight": 3},
    {"id": "W_dot_net", "formula": "m_dot * w_net", "unit": "kW", "weight": 3},
]
_BRYRG_B = [
    {"id": "s1", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s2", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s3", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s4", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s5", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s6", "formula": "air_state", "unit": "kJ/(kg·K)", "weight": 1},
    {"id": "s_gen_comp", "formula": "s2 - s1", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_regen", "formula": "(s3-s2) + (s6-s5)", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cc", "formula": "(s4-s3) - q_in/T_source", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_turb", "formula": "s5 - s4", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_hr", "formula": "(s1-s6) + q_out/T_sink", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_BRYRG_C = [
    {"id": "ef1", "formula": "(h1-h0) - T0*(s1-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef2", "formula": "(h2-h0) - T0*(s2-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef3", "formula": "(h3-h0) - T0*(s3-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef4", "formula": "(h4-h0) - T0*(s4-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef5", "formula": "(h5-h0) - T0*(s5-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "ef6", "formula": "(h6-h0) - T0*(s6-s0)", "unit": "kJ/kg", "weight": 1},
    {"id": "x_dest_comp", "formula": "T0 * s_gen_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_regen", "formula": "T0 * s_gen_regen", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cc", "formula": "T0 * s_gen_cc", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_turb", "formula": "T0 * s_gen_turb", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_hr", "formula": "T0 * s_gen_hr", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "eta_II", "formula": "W_dot_net / X_dot_in", "unit": "-", "weight": 3},
]

# ── VCR-A (Actual VCR, R-134a, 4+1s states) ─────────────

# NOTE: R-134a absolute h/s/ef values are NOT scored because they depend on
# the reference state (IIR vs ASHRAE). Only difference-based quantities
# (work, heat, COP, entropy generation, exergy destruction) are scored.
# The question text still asks for state properties — we just don't grade them.
_VCRA_A = [
    {"id": "w_comp", "formula": "h2 - h1", "unit": "kJ/kg", "weight": 2},
    {"id": "q_L", "formula": "h1 - h4", "unit": "kJ/kg", "weight": 2},
    {"id": "q_H", "formula": "h2 - h3", "unit": "kJ/kg", "weight": 2},
    {"id": "x4", "formula": "(h4-hf)/(hg-hf)", "unit": "-", "weight": 4},
    {"id": "COP_R", "formula": "q_L / w_comp", "unit": "-", "weight": 3},
    {"id": "W_dot_comp", "formula": "m_dot * w_comp", "unit": "kW", "weight": 3},
    {"id": "Q_dot_L", "formula": "m_dot * q_L", "unit": "kW", "weight": 3},
]
_VCRA_B = [
    {"id": "s_gen_comp", "formula": "s2 - s1", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_cond", "formula": "(s3-s2) + q_H/T_H", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_throttle", "formula": "s4 - s3", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_evap", "formula": "(s1-s4) - q_L/T_L", "unit": "kJ/(kg·K)", "weight": 2},
    {"id": "s_gen_total", "formula": "sum of all s_gen", "unit": "kJ/(kg·K)", "weight": 3},
]
_VCRA_C = [
    {"id": "x_dest_comp", "formula": "T0 * s_gen_comp", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_cond", "formula": "T0 * s_gen_cond", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_throttle", "formula": "T0 * s_gen_throttle", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_evap", "formula": "T0 * s_gen_evap", "unit": "kJ/kg", "weight": 2},
    {"id": "x_dest_total", "formula": "T0 * s_gen_total", "unit": "kJ/kg", "weight": 3},
    {"id": "COP_Carnot", "formula": "T_L / (T_H - T_L)", "unit": "-", "weight": 3},
    {"id": "eta_II", "formula": "COP_R / COP_Carnot", "unit": "-", "weight": 3},
]


# ══════════════════════════════════════════════════════════
# QUESTION TEMPLATES
# ══════════════════════════════════════════════════════════

# --- Rankine Ideal ---

RNKI_A = CycleTemplate(
    template_id="RNK-I-A", cycle_type="RNK-I", depth="A",
    fluid="Water", id_prefix="RNK-I", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An ideal Rankine cycle uses water as the working fluid. The condenser pressure is {P_cond_kPa} kPa and the boiler operates at {P_boiler_MPa} MPa. Steam enters the turbine at {T3_C}°C. The mass flow rate is {m_dot_kgs} kg/s. Both the pump and turbine are isentropic.\n\nDetermine:\n(a) The specific enthalpy at each state point (h₁, h₂, h₃, h₄)\n(b) The pump work, heat input, and turbine work per unit mass\n(c) The net work, thermal efficiency, and net power output",
        "Consider an ideal Rankine power cycle operating with water. The steam leaves the boiler at {T3_C}°C and {P_boiler_MPa} MPa, and the condenser operates at {P_cond_kPa} kPa. The mass flow rate through the cycle is {m_dot_kgs} kg/s. The pump and turbine operate isentropically.\n\nCalculate:\n(a) h₁, h₂, h₃, and h₄\n(b) w_pump, q_in, w_turb, and w_net\n(c) The thermal efficiency and net power output",
    ],
    steps=_steps_a(_RNKI_A), difficulty="easy",
)
RNKI_B = CycleTemplate(
    template_id="RNK-I-B", cycle_type="RNK-I", depth="B",
    fluid="Water", id_prefix="RNK-I", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An ideal Rankine cycle uses water as the working fluid. The condenser pressure is {P_cond_kPa} kPa and the boiler operates at {P_boiler_MPa} MPa with a turbine inlet temperature of {T3_C}°C. The mass flow rate is {m_dot_kgs} kg/s. Both the pump and turbine are isentropic. Heat is supplied by a source at {T_source_K} K and rejected to a sink at {T_sink_K} K.\n\nDetermine:\n(a) The specific enthalpy and entropy at each state point\n(b) The pump work, heat input, turbine work, net work, and thermal efficiency\n(c) The entropy generation in each component and the total entropy generation per unit mass",
        "Consider an ideal Rankine power cycle with water. Steam exits the boiler at {T3_C}°C and {P_boiler_MPa} MPa. The condenser pressure is {P_cond_kPa} kPa and ṁ = {m_dot_kgs} kg/s. The pump and turbine are isentropic. The heat source temperature is {T_source_K} K and the heat sink temperature is {T_sink_K} K.\n\nCalculate all state enthalpies, entropies, component works, heat transfers, thermal efficiency, and the entropy generation in each component (pump, boiler, turbine, condenser) and the total.",
    ],
    steps=_steps_b(_RNKI_A, _RNKI_B), difficulty="medium",
)
RNKI_C = CycleTemplate(
    template_id="RNK-I-C", cycle_type="RNK-I", depth="C",
    fluid="Water", id_prefix="RNK-I", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An ideal Rankine cycle uses water as the working fluid. The condenser pressure is {P_cond_kPa} kPa and the boiler operates at {P_boiler_MPa} MPa with a turbine inlet temperature of {T3_C}°C. The mass flow rate is {m_dot_kgs} kg/s. Both the pump and turbine are isentropic. Heat is supplied by a source at {T_source_K} K and rejected to a sink at {T_sink_K} K. The dead state is T₀ = 25°C (298.15 K), P₀ = 0.1 MPa.\n\nDetermine:\n(a) All state enthalpies, entropies, and specific flow exergies\n(b) Component works, heat transfers, thermal efficiency, and net power\n(c) Entropy generation and exergy destruction in each component\n(d) Total exergy destruction and second-law efficiency",
    ],
    steps=_steps_c(_RNKI_A, _RNKI_B, _RNKI_C), difficulty="hard",
)

# --- Rankine Actual ---

RNKA_A = CycleTemplate(
    template_id="RNK-A-A", cycle_type="RNK-A", depth="A",
    fluid="Water", id_prefix="RNK-A", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "eta_pump": (0.75, 0.90),
                  "eta_turb": (0.80, 0.92), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An actual Rankine cycle uses water as the working fluid. The condenser pressure is {P_cond_kPa} kPa and the boiler operates at {P_boiler_MPa} MPa. Steam enters the turbine at {T3_C}°C. The pump isentropic efficiency is {eta_pump_pct}% and the turbine isentropic efficiency is {eta_turb_pct}%. The mass flow rate is {m_dot_kgs} kg/s.\n\nNote: η_pump = w_pump,s / w_pump,actual and η_turb = w_turb,actual / w_turb,s.\n\nDetermine:\n(a) The specific enthalpy at each state point (h₁, h₂s, h₂, h₃, h₄s, h₄)\n(b) The pump work, heat input, turbine work, and net work per unit mass\n(c) The thermal efficiency and net power output",
        "A steam power plant operates on the Rankine cycle. Water leaves the condenser as saturated liquid at {P_cond_kPa} kPa and is pumped to {P_boiler_MPa} MPa. The turbine inlet temperature is {T3_C}°C. The pump has an isentropic efficiency of {eta_pump_pct}% and the turbine has an isentropic efficiency of {eta_turb_pct}%. The mass flow rate is {m_dot_kgs} kg/s.\n\nCalculate h₁, h₂s, h₂, h₃, h₄s, h₄, w_pump, q_in, w_turb, w_net, η_th, and Ẇ_net.",
    ],
    steps=_steps_a(_RNKA_A), difficulty="easy",
)
RNKA_B = CycleTemplate(
    template_id="RNK-A-B", cycle_type="RNK-A", depth="B",
    fluid="Water", id_prefix="RNK-A", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "eta_pump": (0.75, 0.90),
                  "eta_turb": (0.80, 0.92), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An actual Rankine cycle uses water. Condenser pressure: {P_cond_kPa} kPa. Boiler pressure: {P_boiler_MPa} MPa. Turbine inlet: {T3_C}°C. η_pump = {eta_pump_pct}%, η_turb = {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source at {T_source_K} K, heat sink at {T_sink_K} K.\n\nDetermine all state enthalpies and entropies, component works, heat transfers, thermal efficiency, net power, and the entropy generation in each component (pump, boiler, turbine, condenser) and total.",
    ],
    steps=_steps_b(_RNKA_A, _RNKA_B), difficulty="medium",
)
RNKA_C = CycleTemplate(
    template_id="RNK-A-C", cycle_type="RNK-A", depth="C",
    fluid="Water", id_prefix="RNK-A", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (2, 15),
                  "T3_C": (350, 600), "eta_pump": (0.75, 0.90),
                  "eta_turb": (0.80, 0.92), "m_dot_kgs": (5, 100)},
    question_templates=[
        "An actual Rankine cycle uses water. Condenser: {P_cond_kPa} kPa. Boiler: {P_boiler_MPa} MPa, {T3_C}°C. η_pump = {eta_pump_pct}%, η_turb = {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. Dead state: T₀ = 25°C, P₀ = 0.1 MPa.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate component works, heat transfers, thermal efficiency. Find entropy generation and exergy destruction in each component (pump, boiler, turbine, condenser), total exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_RNKA_A, _RNKA_B, _RNKA_C), difficulty="hard",
)

# --- Rankine Reheat ---

RNKRH_A = CycleTemplate(
    template_id="RNK-RH-A", cycle_type="RNK-RH", depth="A",
    fluid="Water", id_prefix="RNK-RH", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (6, 15),
                  "P_reheat_MPa": (0.5, 3), "T3_C": (400, 600),
                  "T5_C": (400, 600), "eta_pump": (0.75, 0.90),
                  "eta_HPT": (0.80, 0.92), "eta_LPT": (0.80, 0.92),
                  "m_dot_kgs": (10, 100)},
    question_templates=[
        "A reheat Rankine cycle uses water. The condenser pressure is {P_cond_kPa} kPa. Steam is generated at {P_boiler_MPa} MPa and {T3_C}°C, expanded through the HPT to {P_reheat_MPa} MPa, reheated to {T5_C}°C, then expanded through the LPT to the condenser pressure. η_pump = {eta_pump_pct}%, η_HPT = {eta_HPT_pct}%, η_LPT = {eta_LPT_pct}%. ṁ = {m_dot_kgs} kg/s.\n\nDetermine:\n(a) h₁, h₂s, h₂, h₃, h₄, h₅, h₆\n(b) w_pump, q_in, w_HPT, w_LPT, w_net\n(c) η_th and Ẇ_net",
        "Consider a reheat Rankine power cycle with water. Operating conditions: P_cond = {P_cond_kPa} kPa, P_boiler = {P_boiler_MPa} MPa, T₃ = {T3_C}°C, P_reheat = {P_reheat_MPa} MPa, T₅ = {T5_C}°C. Component efficiencies: η_pump = {eta_pump_pct}%, η_HPT = {eta_HPT_pct}%, η_LPT = {eta_LPT_pct}%. Mass flow rate: {m_dot_kgs} kg/s.\n\nCalculate all state enthalpies, component works, total heat input, net work, thermal efficiency, and net power output.",
    ],
    steps=_steps_a(_RNKRH_A), difficulty="medium",
)
RNKRH_B = CycleTemplate(
    template_id="RNK-RH-B", cycle_type="RNK-RH", depth="B",
    fluid="Water", id_prefix="RNK-RH", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (6, 15),
                  "P_reheat_MPa": (0.5, 3), "T3_C": (400, 600),
                  "T5_C": (400, 600), "eta_pump": (0.75, 0.90),
                  "eta_HPT": (0.80, 0.92), "eta_LPT": (0.80, 0.92),
                  "m_dot_kgs": (10, 100)},
    question_templates=[
        "A reheat Rankine cycle with water. P_cond = {P_cond_kPa} kPa, P_boiler = {P_boiler_MPa} MPa, T₃ = {T3_C}°C, P_reheat = {P_reheat_MPa} MPa, T₅ = {T5_C}°C. η_pump = {eta_pump_pct}%, η_HPT = {eta_HPT_pct}%, η_LPT = {eta_LPT_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K.\n\nDetermine all state enthalpies and entropies, component works, heat transfers, thermal efficiency, net power, and entropy generation in each component (pump, boiler, HPT, reheater, LPT, condenser) and total.",
    ],
    steps=_steps_b(_RNKRH_A, _RNKRH_B), difficulty="hard",
)
RNKRH_C = CycleTemplate(
    template_id="RNK-RH-C", cycle_type="RNK-RH", depth="C",
    fluid="Water", id_prefix="RNK-RH", fluid_code="WA",
    param_ranges={"P_cond_kPa": (5, 50), "P_boiler_MPa": (6, 15),
                  "P_reheat_MPa": (0.5, 3), "T3_C": (400, 600),
                  "T5_C": (400, 600), "eta_pump": (0.75, 0.90),
                  "eta_HPT": (0.80, 0.92), "eta_LPT": (0.80, 0.92),
                  "m_dot_kgs": (10, 100)},
    question_templates=[
        "A reheat Rankine cycle with water. P_cond = {P_cond_kPa} kPa, P_boiler = {P_boiler_MPa} MPa, T₃ = {T3_C}°C, P_reheat = {P_reheat_MPa} MPa, T₅ = {T5_C}°C. η_pump = {eta_pump_pct}%, η_HPT = {eta_HPT_pct}%, η_LPT = {eta_LPT_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. Dead state: T₀ = 25°C, P₀ = 0.1 MPa.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate component works, heat transfers, and thermal efficiency. Find entropy generation and exergy destruction in each component, total exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_RNKRH_A, _RNKRH_B, _RNKRH_C), difficulty="hard",
)

# --- Brayton Ideal ---

BRYI_A = CycleTemplate(
    template_id="BRY-I-A", cycle_type="BRY-I", depth="A",
    fluid="Air", id_prefix="BRY-I", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600), "m_dot_kgs": (10, 200)},
    question_templates=[
        "An ideal Brayton cycle uses air as the working fluid (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4). Air enters the compressor at {T1_K} K and {P1_kPa} kPa. The pressure ratio is {r_p}. The turbine inlet temperature is {T3_K} K. The mass flow rate is {m_dot_kgs} kg/s. Both the compressor and turbine are isentropic.\n\nDetermine:\n(a) The specific enthalpy at each state point (h₁, h₂, h₃, h₄)\n(b) The compressor work, heat input, turbine work, and net work per unit mass\n(c) The thermal efficiency and net power output",
        "Consider an ideal air-standard Brayton cycle (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). Compressor inlet: {T1_K} K, {P1_kPa} kPa. Pressure ratio: r_p = {r_p}. Turbine inlet temperature: {T3_K} K. ṁ = {m_dot_kgs} kg/s. Both compressor and turbine are isentropic.\n\nCalculate h₁, h₂, h₃, h₄, w_comp, q_in, w_turb, w_net, η_th, and Ẇ_net.",
    ],
    steps=_steps_a(_BRYI_A), difficulty="easy",
)
BRYI_B = CycleTemplate(
    template_id="BRY-I-B", cycle_type="BRY-I", depth="B",
    fluid="Air", id_prefix="BRY-I", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600), "m_dot_kgs": (10, 200)},
    question_templates=[
        "An ideal Brayton cycle uses air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). Compressor inlet: {T1_K} K, {P1_kPa} kPa. r_p = {r_p}. T₃ = {T3_K} K. ṁ = {m_dot_kgs} kg/s. Isentropic compressor and turbine. Heat source: {T_source_K} K, heat sink: {T_sink_K} K.\n\nDetermine all state enthalpies and entropies, component works, heat transfers, thermal efficiency, net power, and entropy generation in each component (compressor, combustion chamber, turbine, heat rejection) and total.",
    ],
    steps=_steps_b(_BRYI_A, _BRYI_B), difficulty="medium",
)
BRYI_C = CycleTemplate(
    template_id="BRY-I-C", cycle_type="BRY-I", depth="C",
    fluid="Air", id_prefix="BRY-I", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600), "m_dot_kgs": (10, 200)},
    question_templates=[
        "An ideal Brayton cycle uses air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). Compressor inlet: {T1_K} K, {P1_kPa} kPa. r_p = {r_p}. T₃ = {T3_K} K. ṁ = {m_dot_kgs} kg/s. Isentropic compressor and turbine. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. Dead state: T₀ = 298.15 K, P₀ = 100 kPa.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate component works, heat transfers, thermal efficiency, net power. Find entropy generation and exergy destruction in each component, total exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_BRYI_A, _BRYI_B, _BRYI_C), difficulty="hard",
)

# --- Brayton Actual ---

BRYA_A = CycleTemplate(
    template_id="BRY-A-A", cycle_type="BRY-A", depth="A",
    fluid="Air", id_prefix="BRY-A", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "m_dot_kgs": (10, 200)},
    question_templates=[
        "An actual Brayton cycle uses air (c_p = 1.005 kJ/(kg·K), k = 1.4). Compressor inlet: {T1_K} K, {P1_kPa} kPa. Pressure ratio: r_p = {r_p}. Turbine inlet: {T3_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s.\n\nNote: η_comp = w_comp,s / w_comp,actual, η_turb = w_turb,actual / w_turb,s.\n\nDetermine:\n(a) h₁, h₂s, h₂, h₃, h₄s, h₄\n(b) w_comp, q_in, w_turb, w_net\n(c) η_th and Ẇ_net",
        "A gas turbine power plant operates on the Brayton cycle with air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4). Air enters the compressor at {T1_K} K and {P1_kPa} kPa with a pressure ratio of {r_p}. The turbine inlet temperature is {T3_K} K. The compressor isentropic efficiency is {eta_comp_pct}% and the turbine isentropic efficiency is {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s.\n\nCalculate all state enthalpies, component works, net work, thermal efficiency, and net power.",
    ],
    steps=_steps_a(_BRYA_A), difficulty="easy",
)
BRYA_B = CycleTemplate(
    template_id="BRY-A-B", cycle_type="BRY-A", depth="B",
    fluid="Air", id_prefix="BRY-A", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "m_dot_kgs": (10, 200)},
    question_templates=[
        "An actual Brayton cycle with air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). T₁ = {T1_K} K, P₁ = {P1_kPa} kPa, r_p = {r_p}, T₃ = {T3_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K.\n\nDetermine all state enthalpies and entropies, component works, heat transfers, thermal efficiency, net power, and entropy generation in each component and total.",
    ],
    steps=_steps_b(_BRYA_A, _BRYA_B), difficulty="medium",
)
BRYA_C = CycleTemplate(
    template_id="BRY-A-C", cycle_type="BRY-A", depth="C",
    fluid="Air", id_prefix="BRY-A", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 18), "T3_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "m_dot_kgs": (10, 200)},
    question_templates=[
        "An actual Brayton cycle with air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). T₁ = {T1_K} K, P₁ = {P1_kPa} kPa, r_p = {r_p}, T₃ = {T3_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. Dead state: T₀ = 298.15 K, P₀ = 100 kPa.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate component works, heat transfers, thermal efficiency, net power. Find entropy generation and exergy destruction in each component, total exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_BRYA_A, _BRYA_B, _BRYA_C), difficulty="hard",
)

# --- Brayton Regenerative ---

BRYRG_A = CycleTemplate(
    template_id="BRY-RG-A", cycle_type="BRY-RG", depth="A",
    fluid="Air", id_prefix="BRY-RG", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 14), "T4_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "epsilon_regen": (0.70, 0.90), "m_dot_kgs": (10, 200)},
    question_templates=[
        "A regenerative Brayton cycle uses air (c_p = 1.005 kJ/(kg·K), k = 1.4). Compressor inlet: {T1_K} K, {P1_kPa} kPa. Pressure ratio: r_p = {r_p}. Turbine inlet temperature (state 4): {T4_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%. Regenerator effectiveness: ε = {epsilon_regen_pct}%. ṁ = {m_dot_kgs} kg/s.\n\nStates: 1→compressor inlet, 2→compressor exit, 3→regenerator cold exit, 4→turbine inlet, 5→turbine exit, 6→regenerator hot exit.\nε = (T₃ - T₂) / (T₅ - T₂).\n\nDetermine:\n(a) h₁, h₂s, h₂, h₃, h₄, h₅s, h₅, h₆\n(b) w_comp, q_in, w_turb, w_net\n(c) η_th and Ẇ_net",
        "Consider a regenerative Brayton cycle with air (ideal gas, c_p = 1.005 kJ/(kg·K), k = 1.4). Operating conditions: T₁ = {T1_K} K, P₁ = {P1_kPa} kPa, r_p = {r_p}, T₄ = {T4_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%, ε_regen = {epsilon_regen_pct}%. ṁ = {m_dot_kgs} kg/s. State numbering: 1-comp in, 2-comp out, 3-regen cold out, 4-turb in, 5-turb out, 6-regen hot out.\n\nCalculate all state enthalpies, component works, heat input, net work, thermal efficiency, and net power.",
    ],
    steps=_steps_a(_BRYRG_A), difficulty="medium",
)
BRYRG_B = CycleTemplate(
    template_id="BRY-RG-B", cycle_type="BRY-RG", depth="B",
    fluid="Air", id_prefix="BRY-RG", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 14), "T4_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "epsilon_regen": (0.70, 0.90), "m_dot_kgs": (10, 200)},
    question_templates=[
        "A regenerative Brayton cycle with air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). T₁ = {T1_K} K, P₁ = {P1_kPa} kPa, r_p = {r_p}, T₄ = {T4_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%, ε = {epsilon_regen_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. States: 1-comp in, 2-comp out, 3-regen cold out, 4-turb in, 5-turb out, 6-regen hot out.\n\nDetermine all state enthalpies and entropies, component works, heat transfers, thermal efficiency, net power, and entropy generation in each component (compressor, regenerator, combustion chamber, turbine, heat rejection) and total.",
    ],
    steps=_steps_b(_BRYRG_A, _BRYRG_B), difficulty="hard",
)
BRYRG_C = CycleTemplate(
    template_id="BRY-RG-C", cycle_type="BRY-RG", depth="C",
    fluid="Air", id_prefix="BRY-RG", fluid_code="AR",
    param_ranges={"T1_K": (290, 310), "P1_kPa": (95, 105),
                  "r_p": (6, 14), "T4_K": (1100, 1600),
                  "eta_comp": (0.78, 0.88), "eta_turb": (0.82, 0.92),
                  "epsilon_regen": (0.70, 0.90), "m_dot_kgs": (10, 200)},
    question_templates=[
        "A regenerative Brayton cycle with air (c_p = 1.005 kJ/(kg·K), k = 1.4, R = 0.287 kJ/(kg·K)). T₁ = {T1_K} K, P₁ = {P1_kPa} kPa, r_p = {r_p}, T₄ = {T4_K} K. η_comp = {eta_comp_pct}%, η_turb = {eta_turb_pct}%, ε = {epsilon_regen_pct}%. ṁ = {m_dot_kgs} kg/s. Heat source: {T_source_K} K, heat sink: {T_sink_K} K. Dead state: T₀ = 298.15 K, P₀ = 100 kPa. States: 1-comp in, 2-comp out, 3-regen cold out, 4-turb in, 5-turb out, 6-regen hot out.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate component works, heat transfers, thermal efficiency, net power. Find entropy generation and exergy destruction in each component, total exergy destruction, and second-law efficiency.",
    ],
    steps=_steps_c(_BRYRG_A, _BRYRG_B, _BRYRG_C), difficulty="hard",
)

# --- VCR Actual ---

VCRA_A = CycleTemplate(
    template_id="VCR-A-A", cycle_type="VCR-A", depth="A",
    fluid="R-134a", id_prefix="VCR-A", fluid_code="RF",
    param_ranges={"T_evap_C": (-25, 5), "T_cond_C": (30, 50),
                  "eta_comp": (0.75, 0.88), "m_dot_kgs": (0.01, 0.5)},
    question_templates=[
        "An actual vapor-compression refrigeration cycle uses R-134a. The evaporator temperature is {T_evap_C}°C and the condenser temperature is {T_cond_C}°C. The compressor has an isentropic efficiency of {eta_comp_pct}%. The mass flow rate of refrigerant is {m_dot_kgs} kg/s. The refrigerant leaves the evaporator as saturated vapor and leaves the condenser as saturated liquid. The expansion valve is isenthalpic.\n\nDetermine:\n(a) h₁, h₂s, h₂, h₃, h₄\n(b) w_comp, q_L (cooling effect), q_H (heat rejection)\n(c) Quality after throttle (x₄), COP_R, Ẇ_comp, and Q̇_L",
        "A refrigeration system operates on the vapor-compression cycle with R-134a. Operating conditions: T_evap = {T_evap_C}°C, T_cond = {T_cond_C}°C. The compressor isentropic efficiency is {eta_comp_pct}%. ṁ = {m_dot_kgs} kg/s. State 1: saturated vapor at evaporator. State 3: saturated liquid at condenser. Throttle is isenthalpic (h₄ = h₃).\n\nCalculate all state enthalpies, compressor work, cooling effect, heat rejection, throttle exit quality (x₄), COP_R, compressor power, and cooling capacity.",
    ],
    steps=_steps_a(_VCRA_A), difficulty="easy",
)
VCRA_B = CycleTemplate(
    template_id="VCR-A-B", cycle_type="VCR-A", depth="B",
    fluid="R-134a", id_prefix="VCR-A", fluid_code="RF",
    param_ranges={"T_evap_C": (-25, 5), "T_cond_C": (30, 50),
                  "eta_comp": (0.75, 0.88), "m_dot_kgs": (0.01, 0.5)},
    question_templates=[
        "An actual VCR cycle with R-134a. T_evap = {T_evap_C}°C, T_cond = {T_cond_C}°C. η_comp = {eta_comp_pct}%. ṁ = {m_dot_kgs} kg/s. Sat. vapor at evaporator exit, sat. liquid at condenser exit. Isenthalpic throttle. Environment (condenser heat sink) at {T_H_K} K, cooled space at {T_L_K} K.\n\nDetermine all state enthalpies, entropies, compressor work, cooling effect, heat rejection, x₄, COP_R, power and capacity. Also find entropy generation in each component (compressor, condenser, throttle valve, evaporator) and total entropy generation per unit mass.",
    ],
    steps=_steps_b(_VCRA_A, _VCRA_B), difficulty="medium",
)
VCRA_C = CycleTemplate(
    template_id="VCR-A-C", cycle_type="VCR-A", depth="C",
    fluid="R-134a", id_prefix="VCR-A", fluid_code="RF",
    param_ranges={"T_evap_C": (-25, 5), "T_cond_C": (30, 50),
                  "eta_comp": (0.75, 0.88), "m_dot_kgs": (0.01, 0.5)},
    question_templates=[
        "An actual VCR cycle with R-134a. T_evap = {T_evap_C}°C, T_cond = {T_cond_C}°C. η_comp = {eta_comp_pct}%. ṁ = {m_dot_kgs} kg/s. Sat. vapor at evaporator exit, sat. liquid at condenser exit. Isenthalpic throttle. Environment at {T_H_K} K, cooled space at {T_L_K} K. Dead state: T₀ = 25°C, P₀ = 0.1 MPa.\n\nDetermine all state enthalpies, entropies, and flow exergies. Calculate compressor work, cooling effect, heat rejection, x₄, and COP_R. Find entropy generation and exergy destruction in each component (compressor, condenser, throttle, evaporator), total exergy destruction, Carnot COP, and second-law efficiency (η_II = COP_R / COP_Carnot).",
    ],
    steps=_steps_c(_VCRA_A, _VCRA_B, _VCRA_C), difficulty="hard",
)


# ══════════════════════════════════════════════════════════
# MASTER TEMPLATE LIST & COUNTS
# ══════════════════════════════════════════════════════════

TIER3_TEMPLATES: list[CycleTemplate] = [
    # Rankine Ideal: 15 questions
    RNKI_A, RNKI_B, RNKI_C,
    # Rankine Actual: 15 questions
    RNKA_A, RNKA_B, RNKA_C,
    # Rankine Reheat: 10 questions
    RNKRH_A, RNKRH_B, RNKRH_C,
    # Brayton Ideal: 15 questions
    BRYI_A, BRYI_B, BRYI_C,
    # Brayton Actual: 15 questions
    BRYA_A, BRYA_B, BRYA_C,
    # Brayton Regenerative: 10 questions
    BRYRG_A, BRYRG_B, BRYRG_C,
    # VCR Actual: 15 questions
    VCRA_A, VCRA_B, VCRA_C,
]

# Questions per template — total ~95
TIER3_TEMPLATE_COUNTS: dict[str, int] = {
    # Rankine Ideal: 15
    "RNK-I-A": 5, "RNK-I-B": 5, "RNK-I-C": 5,
    # Rankine Actual: 15
    "RNK-A-A": 5, "RNK-A-B": 5, "RNK-A-C": 5,
    # Rankine Reheat: 10
    "RNK-RH-A": 4, "RNK-RH-B": 3, "RNK-RH-C": 3,
    # Brayton Ideal: 15
    "BRY-I-A": 5, "BRY-I-B": 5, "BRY-I-C": 5,
    # Brayton Actual: 15
    "BRY-A-A": 5, "BRY-A-B": 5, "BRY-A-C": 5,
    # Brayton Regenerative: 10
    "BRY-RG-A": 4, "BRY-RG-B": 3, "BRY-RG-C": 3,
    # VCR Actual: 15
    "VCR-A-A": 5, "VCR-A-B": 5, "VCR-A-C": 5,
}


def get_templates_by_cycle(cycle_type: str) -> list[CycleTemplate]:
    return [t for t in TIER3_TEMPLATES if t.cycle_type == cycle_type]


def get_template_by_id(template_id: str) -> CycleTemplate | None:
    for t in TIER3_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None
