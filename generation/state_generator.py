"""
Tier 2 state generation engine for ThermoQA.

Implements anchor-derive pattern for 7 steady-state components:
turbine, compressor, pump, heat exchanger, boiler, mixing chamber, nozzle.

Each generator anchors an inlet state, applies process constraints,
and derives all intermediate/exit properties via CoolProp (or analytical
for ideal gas). Returns a ComponentState with step-level results for
weighted scoring.
"""

import math
from dataclasses import dataclass, field

from CoolProp.CoolProp import PropsSI

from generation.ground_truth import _to_K, _to_C, _to_Pa, _to_kPa

# ── Constants ──────────────────────────────────────────────

T0_K = 298.15       # Dead state temperature (25°C) in K
P0_PA = 100000.0    # Dead state pressure (0.1 MPa) in Pa

# Ideal gas (Air) constants
AIR_CP = 1.005      # kJ/(kg·K)
AIR_R = 0.287       # kJ/(kg·K)
AIR_K = 1.4         # ratio of specific heats
AIR_T_REF = 298.15  # K, reference for entropy


@dataclass
class StepResult:
    step_id: str
    value: float
    unit: str
    weight: float
    formula: str
    tolerance_pct: float = 2.0
    abs_tolerance: float = 0.5


@dataclass
class ComponentState:
    component: str
    depth: str          # "A", "B", "C"
    fluid: str
    given: dict
    steps: list[StepResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validated: bool = False


# ── Dead state cache ───────────────────────────────────────

_DEAD_STATE_CACHE: dict[str, dict] = {}


def get_dead_state(fluid: str) -> dict:
    """Return {h0, s0} at T0=298.15K, P0=100kPa for the given fluid."""
    if fluid in _DEAD_STATE_CACHE:
        return _DEAD_STATE_CACHE[fluid]
    if fluid == "Air":
        ds = {"h0": AIR_CP * _to_C(T0_K), "s0": 0.0}  # ref state
    else:
        h0 = PropsSI("H", "T", T0_K, "P", P0_PA, fluid) / 1000
        s0 = PropsSI("S", "T", T0_K, "P", P0_PA, fluid) / 1000
        ds = {"h0": h0, "s0": s0}
    _DEAD_STATE_CACHE[fluid] = ds
    return ds


def _flow_exergy(h, s, h0, s0, V=0.0):
    """Flow exergy: psi = (h-h0) - T0*(s-s0) + V^2/(2*1000).
    h, h0 in kJ/kg; s, s0 in kJ/(kg·K); V in m/s.
    Returns kJ/kg."""
    return (h - h0) - (T0_K / 1000 * 1000) * (s - s0) + V**2 / (2 * 1000)
    # T0_K is 298.15 K; T0*(s-s0) when s in kJ/(kg·K) → result in kJ/kg


def _flow_exergy_kJ(h, s, h0, s0, V=0.0):
    """Flow exergy in kJ/kg. T0 in K, s in kJ/(kg·K)."""
    return (h - h0) - T0_K * (s - s0) + V**2 / (2 * 1000)


# ── Ideal gas helpers ──────────────────────────────────────

def _air_h(T_K):
    """Enthalpy of air (ideal gas) in kJ/kg, relative to 0 K."""
    return AIR_CP * T_K


def _air_s(T_K, P_MPa):
    """Entropy of air (ideal gas) in kJ/(kg·K), relative to ref state."""
    return AIR_CP * math.log(T_K / AIR_T_REF) - AIR_R * math.log(P_MPa / 0.1)


def _air_isentropic_T(T1_K, P1_MPa, P2_MPa):
    """Isentropic exit temperature for ideal gas."""
    return T1_K * (P2_MPa / P1_MPa) ** ((AIR_K - 1) / AIR_K)


# ── CoolProp wrappers (engineering units) ──────────────────

def _cp_h(T_C, P_MPa, fluid):
    """Enthalpy in kJ/kg from T(°C), P(MPa)."""
    return PropsSI("H", "T", _to_K(T_C), "P", P_MPa * 1e6, fluid) / 1000


def _cp_s(T_C, P_MPa, fluid):
    """Entropy in kJ/(kg·K) from T(°C), P(MPa)."""
    return PropsSI("S", "T", _to_K(T_C), "P", P_MPa * 1e6, fluid) / 1000


def _cp_v(T_C, P_MPa, fluid):
    """Specific volume in m³/kg from T(°C), P(MPa)."""
    return 1.0 / PropsSI("D", "T", _to_K(T_C), "P", P_MPa * 1e6, fluid)


def _cp_h_from_sP(s_kJ, P_MPa, fluid):
    """Enthalpy from s(kJ/(kg·K)) and P(MPa)."""
    return PropsSI("H", "S", s_kJ * 1000, "P", P_MPa * 1e6, fluid) / 1000


def _cp_s_from_hP(h_kJ, P_MPa, fluid):
    """Entropy from h(kJ/kg) and P(MPa)."""
    return PropsSI("S", "H", h_kJ * 1000, "P", P_MPa * 1e6, fluid) / 1000


def _cp_T_from_hP(h_kJ, P_MPa, fluid):
    """Temperature in °C from h(kJ/kg) and P(MPa)."""
    return _to_C(PropsSI("T", "H", h_kJ * 1000, "P", P_MPa * 1e6, fluid))


def _cp_T_sat(P_MPa, fluid):
    """Saturation temperature in °C from P(MPa)."""
    return _to_C(PropsSI("T", "P", P_MPa * 1e6, "Q", 0, fluid))


def _cp_h_from_TP(T_C, P_MPa, fluid):
    """Alias for _cp_h."""
    return _cp_h(T_C, P_MPa, fluid)


# ── Step builder helpers ───────────────────────────────────

# Step weight maps from taxonomy (depth A steps, B extends A, C extends B)
# These match tier2_components.yaml exactly

TURBINE_STEPS = {
    "A": [
        ("h1", "kJ/kg", 0.15, "CoolProp(T1, P1)"),
        ("s1", "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"),
        ("h2s", "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"),
        ("h2", "kJ/kg", 0.15, "h1 - eta_s*(h1-h2s)"),
        ("w_out", "kJ/kg", 0.30, "h1 - h2"),
    ],
    "B": [
        ("s2", "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"),
        ("s_gen", "kJ/(kg*K)", 0.20, "s2 - s1"),
    ],
    "C": [
        ("x_dest", "kJ/kg", 0.10, "T0_K * s_gen"),
        ("eta_II", "-", 0.10, "w_out / (w_out + x_dest)"),
    ],
}

COMPRESSOR_STEPS = {
    "A": [
        ("h1", "kJ/kg", 0.15, "CoolProp(T1, P1)"),
        ("s1", "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"),
        ("h2s", "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"),
        ("h2", "kJ/kg", 0.15, "h1 + (h2s-h1)/eta_s"),
        ("w_in", "kJ/kg", 0.30, "h2 - h1"),
    ],
    "B": [
        ("s2", "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"),
        ("s_gen", "kJ/(kg*K)", 0.20, "s2 - s1"),
    ],
    "C": [
        ("x_dest", "kJ/kg", 0.10, "T0_K * s_gen"),
        ("eta_II", "-", 0.10, "1 - x_dest / w_in"),
    ],
}

PUMP_STEPS = {
    "A": [
        ("h1", "kJ/kg", 0.15, "CoolProp(T1, P1)"),
        ("s1", "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"),
        ("h2s", "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"),
        ("h2", "kJ/kg", 0.15, "h1 + (h2s-h1)/eta_s"),
        ("w_in", "kJ/kg", 0.30, "h2 - h1"),
    ],
    "B": [
        ("s2", "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"),
        ("s_gen", "kJ/(kg*K)", 0.20, "s2 - s1"),
    ],
    "C": [
        ("x_dest", "kJ/kg", 0.10, "T0_K * s_gen"),
        ("eta_II", "-", 0.10, "1 - x_dest / w_in"),
    ],
}

HX_STEPS = {
    "A": [
        ("h_h_in", "kJ/kg", 0.10, "CoolProp(T_h_in, P_h)"),
        ("h_h_out", "kJ/kg", 0.10, "CoolProp(T_h_out, P_h)"),
        ("h_c_in", "kJ/kg", 0.10, "CoolProp(T_c_in, P_c)"),
        ("Q_dot", "kW", 0.20, "m_h * (h_h_in - h_h_out)"),
        ("h_c_out", "kJ/kg", 0.10, "h_c_in + Q_dot/m_c"),
        ("T_c_out", "C", 0.10, "CoolProp(h=h_c_out, P_c)"),
    ],
    "B": [
        ("s_h_in", "kJ/(kg*K)", 0.05, "CoolProp(T_h_in, P_h)"),
        ("s_h_out", "kJ/(kg*K)", 0.05, "CoolProp(T_h_out, P_h)"),
        ("s_c_in", "kJ/(kg*K)", 0.05, "CoolProp(T_c_in, P_c)"),
        ("s_c_out", "kJ/(kg*K)", 0.05, "CoolProp(h=h_c_out, P_c)"),
        ("S_gen_dot", "kW/K", 0.20, "m_h*(s_h_out-s_h_in) + m_c*(s_c_out-s_c_in)"),
    ],
    "C": [
        ("X_dest_dot", "kW", 0.10, "T0_K * S_gen_dot"),
        ("eta_II", "-", 0.10, "m_c*(psi_c_out-psi_c_in) / (m_h*(psi_h_in-psi_h_out))"),
    ],
}

BOILER_STEPS = {
    "A": [
        ("h_in", "kJ/kg", 0.15, "CoolProp(T_in, P)"),
        ("h_out", "kJ/kg", 0.15, "CoolProp(T_out, P)"),
        ("q_in", "kJ/kg", 0.30, "h_out - h_in"),
    ],
    "B": [
        ("s_in", "kJ/(kg*K)", 0.10, "CoolProp(T_in, P)"),
        ("s_out", "kJ/(kg*K)", 0.10, "CoolProp(T_out, P)"),
        ("s_gen", "kJ/(kg*K)", 0.20, "(s_out - s_in) - q_in/T_source"),
    ],
    "C": [
        ("x_dest", "kJ/kg", 0.10, "T0_K * s_gen"),
        ("eta_II", "-", 0.10, "(psi_out - psi_in) / (q_in * (1 - T0_K/T_source))"),
    ],
}

MIXER_STEPS = {
    "A": [
        ("h1", "kJ/kg", 0.10, "CoolProp(T1, P)"),
        ("h2", "kJ/kg", 0.10, "CoolProp(T2, P)"),
        ("m3", "kg/s", 0.05, "m1 + m2"),
        ("h3", "kJ/kg", 0.20, "(m1*h1 + m2*h2) / m3"),
        ("T3", "C", 0.15, "CoolProp(h=h3, P)"),
    ],
    "B": [
        ("s1", "kJ/(kg*K)", 0.05, "CoolProp(T1, P)"),
        ("s2", "kJ/(kg*K)", 0.05, "CoolProp(T2, P)"),
        ("s3", "kJ/(kg*K)", 0.05, "CoolProp(h=h3, P)"),
        ("S_gen_dot", "kW/K", 0.20, "m3*s3 - m1*s1 - m2*s2"),
    ],
    "C": [
        ("X_dest_dot", "kW", 0.10, "T0_K * S_gen_dot"),
        ("eta_II", "-", 0.10, "m3*psi3 / (m1*psi1 + m2*psi2)"),
    ],
}

NOZZLE_STEPS = {
    "A": [
        ("h1", "kJ/kg", 0.10, "CoolProp(T1, P1)"),
        ("s1", "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"),
        ("h2s", "kJ/kg", 0.10, "CoolProp(s=s1, P=P2)"),
        ("V2", "m/s", 0.20, "sqrt(V1^2 + 2*eta*(h1-h2s)*1000)"),
        ("h2", "kJ/kg", 0.15, "h1 - (V2^2-V1^2)/(2*1000)"),
    ],
    "B": [
        ("s2", "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"),
        ("s_gen", "kJ/(kg*K)", 0.20, "s2 - s1"),
    ],
    "C": [
        ("x_dest", "kJ/kg", 0.10, "T0_K * s_gen"),
        ("eta_II", "-", 0.10, "KE_gain / exergy_decrease"),
    ],
}

STEP_DEFS = {
    "turbine": TURBINE_STEPS,
    "compressor": COMPRESSOR_STEPS,
    "pump": PUMP_STEPS,
    "heat_exchanger": HX_STEPS,
    "boiler": BOILER_STEPS,
    "mixing_chamber": MIXER_STEPS,
    "nozzle": NOZZLE_STEPS,
}


def _get_steps_for_depth(component: str, depth: str) -> list[tuple]:
    """Return flat step list for given depth (A includes A, B includes A+B, etc)."""
    defs = STEP_DEFS[component]
    steps = list(defs["A"])
    if depth in ("B", "C"):
        steps.extend(defs["B"])
    if depth == "C":
        steps.extend(defs["C"])
    return steps


def _make_step(step_id, value, unit, weight, formula, tol_pct=2.0, abs_tol=0.5):
    return StepResult(
        step_id=step_id,
        value=round(value, 4),
        unit=unit,
        weight=weight,
        formula=formula,
        tolerance_pct=tol_pct,
        abs_tolerance=abs_tol,
    )


# ── Component generators ──────────────────────────────────

def generate_turbine_state(T1_C, P1_MPa, P2_MPa, eta_s, fluid, depth) -> ComponentState:
    """Adiabatic turbine: anchor (T1, P1), expand to P2 with eta_s."""
    state = ComponentState(
        component="turbine", depth=depth, fluid=fluid,
        given={"T1_C": T1_C, "P1_MPa": P1_MPa, "P2_MPa": P2_MPa,
               "eta_s": eta_s, "fluid": fluid},
    )

    if fluid == "Air":
        T1_K = T1_C  # For air, T1 is given in K directly
        P1, P2 = P1_MPa, P2_MPa
        h1 = _air_h(T1_K)
        s1 = _air_s(T1_K, P1)
        T2s_K = _air_isentropic_T(T1_K, P1, P2)
        h2s = _air_h(T2s_K)
        h2 = h1 - eta_s * (h1 - h2s)
        T2_K = h2 / AIR_CP
        s2 = _air_s(T2_K, P2)
        w_out = h1 - h2
    else:
        h1 = _cp_h(T1_C, P1_MPa, fluid)
        s1 = _cp_s(T1_C, P1_MPa, fluid)
        h2s = _cp_h_from_sP(s1, P2_MPa, fluid)
        h2 = h1 - eta_s * (h1 - h2s)
        s2 = _cp_s_from_hP(h2, P2_MPa, fluid)
        w_out = h1 - h2

    state.steps.append(_make_step("h1", h1, "kJ/kg", 0.15, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("s1", s1, "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("h2s", h2s, "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"))
    state.steps.append(_make_step("h2", h2, "kJ/kg", 0.15, "h1 - eta_s*(h1-h2s)"))
    state.steps.append(_make_step("w_out", w_out, "kJ/kg", 0.30, "h1 - h2"))

    if depth in ("B", "C"):
        s_gen = s2 - s1
        state.steps.append(_make_step("s2", s2, "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"))
        state.steps.append(_make_step("s_gen", s_gen, "kJ/(kg*K)", 0.20, "s2 - s1"))

    if depth == "C":
        x_dest = T0_K * s_gen
        eta_II = w_out / (w_out + x_dest) if (w_out + x_dest) != 0 else 0.0
        state.steps.append(_make_step("x_dest", x_dest, "kJ/kg", 0.10, "T0_K * s_gen"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "w_out / (w_out + x_dest)", abs_tol=0.03))

    _validate_state(state)
    return state


def generate_compressor_state(T1_C, P1_MPa, P2_MPa, eta_s, fluid, depth) -> ComponentState:
    """Adiabatic compressor: anchor (T1, P1), compress to P2 with eta_s."""
    state = ComponentState(
        component="compressor", depth=depth, fluid=fluid,
        given={"T1_C": T1_C, "P1_MPa": P1_MPa, "P2_MPa": P2_MPa,
               "eta_s": eta_s, "fluid": fluid},
    )

    if fluid == "Air":
        T1_K = T1_C  # For air, T1 given in K
        P1, P2 = P1_MPa, P2_MPa
        h1 = _air_h(T1_K)
        s1 = _air_s(T1_K, P1)
        T2s_K = _air_isentropic_T(T1_K, P1, P2)
        h2s = _air_h(T2s_K)
        h2 = h1 + (h2s - h1) / eta_s  # division for compressor
        T2_K = h2 / AIR_CP
        s2 = _air_s(T2_K, P2)
        w_in = h2 - h1
    else:
        h1 = _cp_h(T1_C, P1_MPa, fluid)
        s1 = _cp_s(T1_C, P1_MPa, fluid)
        h2s = _cp_h_from_sP(s1, P2_MPa, fluid)
        h2 = h1 + (h2s - h1) / eta_s
        s2 = _cp_s_from_hP(h2, P2_MPa, fluid)
        w_in = h2 - h1

    state.steps.append(_make_step("h1", h1, "kJ/kg", 0.15, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("s1", s1, "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("h2s", h2s, "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"))
    state.steps.append(_make_step("h2", h2, "kJ/kg", 0.15, "h1 + (h2s-h1)/eta_s"))
    state.steps.append(_make_step("w_in", w_in, "kJ/kg", 0.30, "h2 - h1"))

    if depth in ("B", "C"):
        s_gen = s2 - s1
        state.steps.append(_make_step("s2", s2, "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"))
        state.steps.append(_make_step("s_gen", s_gen, "kJ/(kg*K)", 0.20, "s2 - s1"))

    if depth == "C":
        x_dest = T0_K * s_gen
        eta_II = 1.0 - x_dest / w_in if w_in != 0 else 0.0
        state.steps.append(_make_step("x_dest", x_dest, "kJ/kg", 0.10, "T0_K * s_gen"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "1 - x_dest / w_in", abs_tol=0.03))

    _validate_state(state)
    return state


def generate_pump_state(T1_C, P1_MPa, P2_MPa, eta_s, depth) -> ComponentState:
    """Pump: liquid at (T1, P1) pressurized to P2 with eta_s. Water only."""
    fluid = "Water"
    state = ComponentState(
        component="pump", depth=depth, fluid=fluid,
        given={"T1_C": T1_C, "P1_MPa": P1_MPa, "P2_MPa": P2_MPa,
               "eta_s": eta_s, "fluid": fluid},
    )

    h1 = _cp_h(T1_C, P1_MPa, fluid)
    s1 = _cp_s(T1_C, P1_MPa, fluid)
    h2s = _cp_h_from_sP(s1, P2_MPa, fluid)
    h2 = h1 + (h2s - h1) / eta_s
    w_in = h2 - h1
    s2 = _cp_s_from_hP(h2, P2_MPa, fluid)

    state.steps.append(_make_step("h1", h1, "kJ/kg", 0.15, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("s1", s1, "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("h2s", h2s, "kJ/kg", 0.15, "CoolProp(s=s1, P=P2)"))
    state.steps.append(_make_step("h2", h2, "kJ/kg", 0.15, "h1 + (h2s-h1)/eta_s"))
    state.steps.append(_make_step("w_in", w_in, "kJ/kg", 0.30, "h2 - h1"))

    if depth in ("B", "C"):
        s_gen = s2 - s1
        state.steps.append(_make_step("s2", s2, "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"))
        state.steps.append(_make_step("s_gen", s_gen, "kJ/(kg*K)", 0.20, "s2 - s1"))

    if depth == "C":
        x_dest = T0_K * s_gen
        eta_II = 1.0 - x_dest / w_in if w_in != 0 else 0.0
        state.steps.append(_make_step("x_dest", x_dest, "kJ/kg", 0.10, "T0_K * s_gen"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "1 - x_dest / w_in", abs_tol=0.03))

    _validate_state(state)
    return state


def generate_hx_state(T_h_in, T_h_out, T_c_in, P_h_MPa, P_c_MPa,
                      m_h, m_c, fluid_hot, fluid_cold, depth) -> ComponentState:
    """Heat exchanger: two liquid streams, no phase change."""
    state = ComponentState(
        component="heat_exchanger", depth=depth,
        fluid=f"{fluid_hot}/{fluid_cold}",
        given={"T_h_in": T_h_in, "T_h_out": T_h_out, "T_c_in": T_c_in,
               "P_h_MPa": P_h_MPa, "P_c_MPa": P_c_MPa,
               "m_h": m_h, "m_c": m_c,
               "fluid_hot": fluid_hot, "fluid_cold": fluid_cold},
    )

    h_h_in = _cp_h(T_h_in, P_h_MPa, fluid_hot)
    h_h_out = _cp_h(T_h_out, P_h_MPa, fluid_hot)
    h_c_in = _cp_h(T_c_in, P_c_MPa, fluid_cold)

    Q_dot = m_h * (h_h_in - h_h_out)  # kW
    h_c_out = h_c_in + Q_dot / m_c
    T_c_out = _cp_T_from_hP(h_c_out, P_c_MPa, fluid_cold)

    # Validate cold outlet stays liquid
    try:
        T_sat_cold = _cp_T_sat(P_c_MPa, fluid_cold)
        if T_c_out >= T_sat_cold - 2:
            state.warnings.append(
                f"T_c_out ({T_c_out:.1f}°C) exceeds saturation ({T_sat_cold:.1f}°C)")
    except Exception:
        pass

    state.steps.append(_make_step("h_h_in", h_h_in, "kJ/kg", 0.10, "CoolProp(T_h_in, P_h)"))
    state.steps.append(_make_step("h_h_out", h_h_out, "kJ/kg", 0.10, "CoolProp(T_h_out, P_h)"))
    state.steps.append(_make_step("h_c_in", h_c_in, "kJ/kg", 0.10, "CoolProp(T_c_in, P_c)"))
    state.steps.append(_make_step("Q_dot", Q_dot, "kW", 0.20, "m_h * (h_h_in - h_h_out)"))
    state.steps.append(_make_step("h_c_out", h_c_out, "kJ/kg", 0.10, "h_c_in + Q_dot/m_c"))
    state.steps.append(_make_step("T_c_out", T_c_out, "C", 0.10, "CoolProp(h=h_c_out, P_c)"))

    if depth in ("B", "C"):
        s_h_in = _cp_s(T_h_in, P_h_MPa, fluid_hot)
        s_h_out = _cp_s(T_h_out, P_h_MPa, fluid_hot)
        s_c_in = _cp_s(T_c_in, P_c_MPa, fluid_cold)
        s_c_out = _cp_s_from_hP(h_c_out, P_c_MPa, fluid_cold)
        S_gen_dot = m_h * (s_h_out - s_h_in) + m_c * (s_c_out - s_c_in)

        state.steps.append(_make_step("s_h_in", s_h_in, "kJ/(kg*K)", 0.05, "CoolProp(T_h_in, P_h)"))
        state.steps.append(_make_step("s_h_out", s_h_out, "kJ/(kg*K)", 0.05, "CoolProp(T_h_out, P_h)"))
        state.steps.append(_make_step("s_c_in", s_c_in, "kJ/(kg*K)", 0.05, "CoolProp(T_c_in, P_c)"))
        state.steps.append(_make_step("s_c_out", s_c_out, "kJ/(kg*K)", 0.05, "CoolProp(h=h_c_out, P_c)"))
        state.steps.append(_make_step("S_gen_dot", S_gen_dot, "kW/K", 0.20,
                                       "m_h*(s_h_out-s_h_in) + m_c*(s_c_out-s_c_in)"))

    if depth == "C":
        ds_hot = get_dead_state(fluid_hot)
        ds_cold = get_dead_state(fluid_cold)
        psi_h_in = _flow_exergy_kJ(h_h_in, s_h_in, ds_hot["h0"], ds_hot["s0"])
        psi_h_out = _flow_exergy_kJ(h_h_out, s_h_out, ds_hot["h0"], ds_hot["s0"])
        psi_c_in = _flow_exergy_kJ(h_c_in, s_c_in, ds_cold["h0"], ds_cold["s0"])
        psi_c_out = _flow_exergy_kJ(h_c_out, s_c_out, ds_cold["h0"], ds_cold["s0"])

        X_dest_dot = T0_K * S_gen_dot
        exergy_gained = m_c * (psi_c_out - psi_c_in)
        exergy_lost = m_h * (psi_h_in - psi_h_out)
        eta_II = exergy_gained / exergy_lost if exergy_lost != 0 else 0.0

        state.steps.append(_make_step("X_dest_dot", X_dest_dot, "kW", 0.10, "T0_K * S_gen_dot"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "m_c*(psi_c_out-psi_c_in) / (m_h*(psi_h_in-psi_h_out))",
                                       abs_tol=0.03))

    _validate_state(state)
    return state


def generate_boiler_state(T_in_C, P_MPa, T_out_C, T_source_K, depth) -> ComponentState:
    """Boiler: compressed liquid in → superheated steam out, external heat source."""
    fluid = "Water"
    state = ComponentState(
        component="boiler", depth=depth, fluid=fluid,
        given={"T_in_C": T_in_C, "P_MPa": P_MPa, "T_out_C": T_out_C,
               "T_source_K": T_source_K, "fluid": fluid},
    )

    h_in = _cp_h(T_in_C, P_MPa, fluid)
    h_out = _cp_h(T_out_C, P_MPa, fluid)
    q_in = h_out - h_in

    state.steps.append(_make_step("h_in", h_in, "kJ/kg", 0.15, "CoolProp(T_in, P)"))
    state.steps.append(_make_step("h_out", h_out, "kJ/kg", 0.15, "CoolProp(T_out, P)"))
    state.steps.append(_make_step("q_in", q_in, "kJ/kg", 0.30, "h_out - h_in"))

    if depth in ("B", "C"):
        s_in = _cp_s(T_in_C, P_MPa, fluid)
        s_out = _cp_s(T_out_C, P_MPa, fluid)
        s_gen = (s_out - s_in) - q_in / T_source_K

        state.steps.append(_make_step("s_in", s_in, "kJ/(kg*K)", 0.10, "CoolProp(T_in, P)"))
        state.steps.append(_make_step("s_out", s_out, "kJ/(kg*K)", 0.10, "CoolProp(T_out, P)"))
        state.steps.append(_make_step("s_gen", s_gen, "kJ/(kg*K)", 0.20,
                                       "(s_out - s_in) - q_in/T_source"))

    if depth == "C":
        x_dest = T0_K * s_gen
        ds = get_dead_state(fluid)
        psi_in = _flow_exergy_kJ(h_in, s_in, ds["h0"], ds["s0"])
        psi_out = _flow_exergy_kJ(h_out, s_out, ds["h0"], ds["s0"])
        carnot = 1.0 - T0_K / T_source_K
        eta_II = (psi_out - psi_in) / (q_in * carnot) if (q_in * carnot) != 0 else 0.0

        state.steps.append(_make_step("x_dest", x_dest, "kJ/kg", 0.10, "T0_K * s_gen"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "(psi_out - psi_in) / (q_in * (1 - T0_K/T_source))",
                                       abs_tol=0.03))

    _validate_state(state)
    return state


def generate_mixer_state(T1_C, T2_C, P_MPa, m1, m2, depth) -> ComponentState:
    """Mixing chamber: two streams at same P, adiabatic. Water only."""
    fluid = "Water"
    state = ComponentState(
        component="mixing_chamber", depth=depth, fluid=fluid,
        given={"T1_C": T1_C, "T2_C": T2_C, "P_MPa": P_MPa,
               "m1": m1, "m2": m2, "fluid": fluid},
    )

    h1 = _cp_h(T1_C, P_MPa, fluid)
    h2 = _cp_h(T2_C, P_MPa, fluid)
    m3 = m1 + m2
    h3 = (m1 * h1 + m2 * h2) / m3
    T3 = _cp_T_from_hP(h3, P_MPa, fluid)

    state.steps.append(_make_step("h1", h1, "kJ/kg", 0.10, "CoolProp(T1, P)"))
    state.steps.append(_make_step("h2", h2, "kJ/kg", 0.10, "CoolProp(T2, P)"))
    state.steps.append(_make_step("m3", m3, "kg/s", 0.05, "m1 + m2"))
    state.steps.append(_make_step("h3", h3, "kJ/kg", 0.20, "(m1*h1 + m2*h2) / m3"))
    state.steps.append(_make_step("T3", T3, "C", 0.15, "CoolProp(h=h3, P)"))

    if depth in ("B", "C"):
        s1 = _cp_s(T1_C, P_MPa, fluid)
        s2 = _cp_s(T2_C, P_MPa, fluid)
        s3 = _cp_s_from_hP(h3, P_MPa, fluid)
        S_gen_dot = m3 * s3 - m1 * s1 - m2 * s2

        state.steps.append(_make_step("s1", s1, "kJ/(kg*K)", 0.05, "CoolProp(T1, P)"))
        state.steps.append(_make_step("s2", s2, "kJ/(kg*K)", 0.05, "CoolProp(T2, P)"))
        state.steps.append(_make_step("s3", s3, "kJ/(kg*K)", 0.05, "CoolProp(h=h3, P)"))
        state.steps.append(_make_step("S_gen_dot", S_gen_dot, "kW/K", 0.20,
                                       "m3*s3 - m1*s1 - m2*s2"))

    if depth == "C":
        X_dest_dot = T0_K * S_gen_dot
        ds = get_dead_state(fluid)
        psi1 = _flow_exergy_kJ(h1, s1, ds["h0"], ds["s0"])
        psi2 = _flow_exergy_kJ(h2, s2, ds["h0"], ds["s0"])
        psi3 = _flow_exergy_kJ(h3, s3, ds["h0"], ds["s0"])
        exergy_in = m1 * psi1 + m2 * psi2
        exergy_out = m3 * psi3
        eta_II = exergy_out / exergy_in if exergy_in != 0 else 0.0

        state.steps.append(_make_step("X_dest_dot", X_dest_dot, "kW", 0.10, "T0_K * S_gen_dot"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "m3*psi3 / (m1*psi1 + m2*psi2)",
                                       abs_tol=0.03))

    _validate_state(state)
    return state


def generate_nozzle_state(T1_C, P1_MPa, P2_MPa, V1, eta_nozzle, fluid, depth) -> ComponentState:
    """Nozzle: converts enthalpy to kinetic energy."""
    state = ComponentState(
        component="nozzle", depth=depth, fluid=fluid,
        given={"T1_C": T1_C, "P1_MPa": P1_MPa, "P2_MPa": P2_MPa,
               "V1": V1, "eta_nozzle": eta_nozzle, "fluid": fluid},
    )

    if fluid == "Air":
        T1_K = T1_C  # For air, T1 given in K
        h1 = _air_h(T1_K)
        s1 = _air_s(T1_K, P1_MPa)
        T2s_K = _air_isentropic_T(T1_K, P1_MPa, P2_MPa)
        h2s = _air_h(T2s_K)
    else:
        h1 = _cp_h(T1_C, P1_MPa, fluid)
        s1 = _cp_s(T1_C, P1_MPa, fluid)
        h2s = _cp_h_from_sP(s1, P2_MPa, fluid)

    # V2^2 = V1^2 + 2 * eta * (h1 - h2s) * 1000  (kJ→J conversion)
    V2_sq = V1**2 + 2 * eta_nozzle * (h1 - h2s) * 1000
    if V2_sq < 0:
        state.warnings.append(f"V2^2 negative: {V2_sq}")
        V2_sq = 0
    V2 = math.sqrt(V2_sq)

    # Actual exit enthalpy from energy balance
    h2 = h1 - (V2**2 - V1**2) / (2 * 1000)

    if fluid == "Air":
        T2_K = h2 / AIR_CP
        s2 = _air_s(T2_K, P2_MPa)
    else:
        s2 = _cp_s_from_hP(h2, P2_MPa, fluid)

    state.steps.append(_make_step("h1", h1, "kJ/kg", 0.10, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("s1", s1, "kJ/(kg*K)", 0.10, "CoolProp(T1, P1)"))
    state.steps.append(_make_step("h2s", h2s, "kJ/kg", 0.10, "CoolProp(s=s1, P=P2)"))
    state.steps.append(_make_step("V2", V2, "m/s", 0.20, "sqrt(V1^2 + 2*eta*(h1-h2s)*1000)"))
    state.steps.append(_make_step("h2", h2, "kJ/kg", 0.15, "h1 - (V2^2-V1^2)/(2*1000)"))

    if depth in ("B", "C"):
        s_gen = s2 - s1
        state.steps.append(_make_step("s2", s2, "kJ/(kg*K)", 0.10, "CoolProp(h=h2, P=P2)"))
        state.steps.append(_make_step("s_gen", s_gen, "kJ/(kg*K)", 0.20, "s2 - s1"))

    if depth == "C":
        x_dest = T0_K * s_gen

        # Nozzle eta_II = KE_gain / (KE_gain + x_dest)
        # This is the standard exergetic efficiency for a nozzle:
        # useful output (KE gain) over total exergy consumed (KE gain + destroyed)
        KE_gain = (V2**2 - V1**2) / (2 * 1000)  # kJ/kg
        denom = KE_gain + x_dest
        eta_II = KE_gain / denom if denom != 0 else 0.0

        state.steps.append(_make_step("x_dest", x_dest, "kJ/kg", 0.10, "T0_K * s_gen"))
        state.steps.append(_make_step("eta_II", eta_II, "-", 0.10,
                                       "KE_gain / (KE_gain + x_dest)", abs_tol=0.03))

    _validate_state(state)
    return state


# ── Validation ─────────────────────────────────────────────

def _validate_state(state: ComponentState) -> None:
    """Run validation checks on a generated state."""
    step_map = {s.step_id: s.value for s in state.steps}
    warnings = state.warnings

    # Check for NaN
    for s in state.steps:
        if math.isnan(s.value):
            warnings.append(f"NaN in step {s.step_id}")
            state.validated = False
            return

    # s_gen > 0 (second law)
    s_gen = step_map.get("s_gen") or step_map.get("S_gen_dot")
    if s_gen is not None and s_gen < -1e-6:
        warnings.append(f"s_gen negative: {s_gen}")

    # x_dest > 0
    x_dest = step_map.get("x_dest") or step_map.get("X_dest_dot")
    if x_dest is not None and x_dest < -1e-6:
        warnings.append(f"x_dest negative: {x_dest}")

    # eta_II in [0, 1]
    eta_II = step_map.get("eta_II")
    if eta_II is not None:
        if eta_II < -0.01 or eta_II > 1.05:
            warnings.append(f"eta_II out of range: {eta_II}")

    # Nozzle: V2 > V1
    if state.component == "nozzle":
        V2 = step_map.get("V2")
        V1 = state.given.get("V1", 0)
        if V2 is not None and V2 < V1:
            warnings.append(f"V2 ({V2}) < V1 ({V1})")

    # Work values should be positive
    w_out = step_map.get("w_out")
    if w_out is not None and w_out < 0:
        warnings.append(f"w_out negative: {w_out}")
    w_in = step_map.get("w_in")
    if w_in is not None and w_in < 0:
        warnings.append(f"w_in negative: {w_in}")

    state.validated = len(warnings) == 0


# ── Generator dispatcher ──────────────────────────────────

GENERATORS = {
    "turbine": generate_turbine_state,
    "compressor": generate_compressor_state,
    "pump": generate_pump_state,
    "heat_exchanger": generate_hx_state,
    "boiler": generate_boiler_state,
    "mixing_chamber": generate_mixer_state,
    "nozzle": generate_nozzle_state,
}
