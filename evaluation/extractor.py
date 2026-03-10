"""
Extract numerical values and phase names from free-form LLM text responses.
"""

import re

from generation.question_generator import PHASE_ALIASES


def strip_thinking_tags(text: str) -> str:
    """Remove <think>...</think> and <reasoning>...</reasoning> blocks from text."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL)
    return text


# Regex patterns for each property key.
# Each key maps to a list of (pattern, conversion_factor) tuples.
# Patterns are tried in order; the LAST match in the text wins
# (LLMs tend to state final answers last).

def _num(name_patterns: str) -> str:
    """Build a regex that captures a number after a symbol/name."""
    return name_patterns + r"\s*[=:≈~]\s*([+-]?\d[\d,]*\.?\d*(?:[eE][+-]?\d+)?)"


def _prose(name_patterns: str) -> str:
    """Build a regex that captures a number after prose like 'is approximately'."""
    return name_patterns + r"\s+(?:is|=|equals|:)\s*(?:approximately\s+|about\s+|roughly\s+)?([+-]?\d[\d,]*\.?\d*(?:[eE][+-]?\d+)?)"


# Shared number capture group
_NUMCAP = r"([+-]?\d[\d,]*\.?\d*(?:[eE][+-]?\d+)?)"

PROPERTY_PATTERNS: dict[str, list[tuple[str, float]]] = {
    # --- Enthalpy ---
    "h_kJ_kg": [
        (r"\bh\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"enthalpy\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
        (r"\bh\s*=\s*" + _NUMCAP + r"\s*kJ", 1.0),
    ],
    "h_f_kJ_kg": [
        (r"\bh[_\s]?f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h_f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"saturated\s+liquid\s+enthalpy\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "h_g_kJ_kg": [
        (r"\bh[_\s]?g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h_g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"saturated\s+vapor\s+enthalpy\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # --- Entropy ---
    "s_kJ_kgK": [
        (r"\bs\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"entropy\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
        (r"\bs\s*=\s*" + _NUMCAP + r"\s*kJ", 1.0),
    ],
    "s_f_kJ_kgK": [
        (r"\bs[_\s]?f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s_f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s_g_kJ_kgK": [
        (r"\bs[_\s]?g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s_g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    # --- Specific volume ---
    "v_m3_kg": [
        (r"\bv\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"specific\s+volume\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    "v_f_m3_kg": [
        (r"\bv[_\s]?f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"v_f\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "v_g_m3_kg": [
        (r"\bv[_\s]?g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"v_g\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    # --- Internal energy ---
    "u_kJ_kg": [
        (r"\bu\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"internal\s+energy\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    # --- Density ---
    "rho_kg_m3": [
        (r"[ρρ]\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"\brho\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"density\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    # --- Temperature ---
    "T_C": [
        (r"\bT\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"temperature\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    "T_sat_C": [
        (r"\bT[_\s]?sat\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"T_sat\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"saturation\s+temperature\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    # --- Pressure ---
    "P_kPa": [
        (r"\bP\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"pressure\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    "P_sat_kPa": [
        (r"\bP[_\s]?sat\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"P_sat\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"saturation\s+pressure\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
    # --- Quality ---
    "x": [
        (r"\bx\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"quality\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
        (r"dryness\s+fraction\s*[=:≈~is]*\s*(?:approximately\s+|about\s+)?" + _NUMCAP, 1.0),
    ],
}


def _preprocess(text: str) -> str:
    """Clean up markdown formatting and number separators."""
    # Normalize Unicode subscript digits to ASCII (fixes mixed notation like h₂s)
    _SUBSCRIPT_DIGITS = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')
    text = text.translate(_SUBSCRIPT_DIGITS)
    # Normalize LaTeX subscript braces only around known symbols
    # T_{sat} -> T_sat, h_{fg} -> h_fg, s_{fg} -> s_fg, P_{sat} -> P_sat, etc.
    text = re.sub(r'([A-Za-z])_\{([A-Za-z0-9]+)\}', r'\1_\2', text)
    # Strip bold/italic markers
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    # Strip commas inside numbers (e.g., 2,695.3 -> 2695.3)
    text = re.sub(r"(\d),(\d)", r"\1\2", text)
    return text


def _extract_numeric(text: str, prop_key: str) -> float | None:
    """
    Try each pattern for prop_key. Return the LAST match found in text
    (LLMs typically state final answers last).
    """
    patterns = PROPERTY_PATTERNS.get(prop_key, [])
    best_value = None
    best_pos = -1

    for pattern, factor in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            pos = m.start()
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw) * factor
            except ValueError:
                continue
            if pos >= best_pos:
                best_pos = pos
                best_value = val

    if best_value is None:
        return None

    # Auto-conversion heuristics based on surrounding text context
    best_value = _auto_convert(text, prop_key, best_value)
    return best_value


def _auto_convert(text: str, prop_key: str, value: float) -> float:
    """Apply unit auto-conversion heuristics."""
    # Enthalpy / internal energy: if > 10000, likely J/kg -> kJ/kg
    if prop_key in ("h_kJ_kg", "h_f_kJ_kg", "h_g_kJ_kg", "u_kJ_kg"):
        if abs(value) > 10000:
            value /= 1000.0

    # Entropy: if > 100, likely J/(kg*K) -> kJ/(kg*K)
    if prop_key in ("s_kJ_kgK", "s_f_kJ_kgK", "s_g_kJ_kgK"):
        if abs(value) > 100:
            value /= 1000.0

    # Quality: percentage -> fraction
    if prop_key == "x":
        if value > 1.0 and value <= 100.0:
            value /= 100.0

    # Pressure: check if in MPa (small values for pressure)
    if prop_key in ("P_kPa", "P_sat_kPa"):
        # Scan for "MPa" near any pressure number
        if re.search(r"\bMPa\b", text, re.IGNORECASE):
            # If value looks like MPa range (< 100 for our dataset range of 100-35000 kPa)
            if value < 100:
                value *= 1000.0

    return value


def _extract_phase(text: str) -> str | None:
    """
    Search text for phase aliases. Return the canonical phase name
    of the longest matching alias (avoids 'steam' matching before 'superheated steam').
    """
    text_lower = text.lower()
    best_canonical = None
    best_len = 0

    for canonical, aliases in PHASE_ALIASES.items():
        for alias in aliases:
            if alias.lower() in text_lower:
                if len(alias) > best_len:
                    best_len = len(alias)
                    best_canonical = canonical
        # Also check canonical name itself
        canon_check = canonical.replace("_", " ")
        if canon_check in text_lower:
            if len(canon_check) > best_len:
                best_len = len(canon_check)
                best_canonical = canonical

    return best_canonical


def extract_properties(
    response_text: str, expected_keys: list[str]
) -> dict[str, float | str | None]:
    """
    Extract property values from a free-form LLM response.

    Args:
        response_text: The raw text response from an LLM.
        expected_keys: List of property keys to extract (e.g., ["h_kJ_kg", "s_kJ_kgK", "phase_name"]).

    Returns:
        Dict mapping each expected key to an extracted value (float, str, or None if not found).
    """
    text = strip_thinking_tags(response_text)
    text = _preprocess(text)
    result: dict[str, float | str | None] = {}

    for key in expected_keys:
        if key == "phase_name":
            result[key] = _extract_phase(text)
        else:
            result[key] = _extract_numeric(text, key)

    return result


# ══════════════════════════════════════════════════════════
# TIER 2: Component Analysis Extraction
# ══════════════════════════════════════════════════════════

TIER2_PROPERTY_PATTERNS: dict[str, list[tuple[str, float]]] = {
    # State properties with subscripts
    "h1": [
        (r"\bh[_\s]?1\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₁\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s1": [
        (r"\bs[_\s]?1\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₁\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h2": [
        (r"\bh[_\s]?2\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₂\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s2": [
        (r"\bs[_\s]?2\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₂\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h2s": [
        (r"\bh[_\s]?2s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₂ₛ\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h[_\s]?2,?s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    # Energy terms
    "w_out": [
        (r"\bw[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"work\s+output\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"\bw\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "w_in": [
        (r"\bw[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"work\s+input\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"\bw[_\s]?pump\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "q_in": [
        (r"\bq[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"heat\s+input\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"heat\s+(?:addition|added|transfer)\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Entropy generation
    "s_gen": [
        (r"\bs[_\s]?gen\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"entropy\s+generation\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"[Ss]_gen\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "S_gen_dot": [
        (r"[SṠ][_\s]?gen(?:\s*dot)?\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Ṡ[_\s]?gen\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"entropy\s+generation\s+rate\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Exergy destruction
    "x_dest": [
        (r"\bx[_\s]?dest\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"exergy\s+destruction\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"[Xx]_dest\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "X_dest_dot": [
        (r"[XẊ][_\s]?dest(?:\s*dot)?\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Ẋ[_\s]?dest\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"exergy\s+destruction\s+rate\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Second-law efficiency
    "eta_II": [
        (r"η[_\s]?II\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"eta[_\s]?II\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"η₂\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"second[- ]law\s+efficiency\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"exergetic\s+efficiency\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Velocity
    "V2": [
        (r"\bV[_\s]?2\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"V₂\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"exit\s+velocity\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # HX-specific
    "h_h_in": [
        (r"\bh[_\s]?h[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h_h_out": [
        (r"\bh[_\s]?h[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h_c_in": [
        (r"\bh[_\s]?c[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h_c_out": [
        (r"\bh[_\s]?c[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "Q_dot": [
        (r"[QQ̇][_\s]?dot\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Q̇\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"heat\s+transfer\s+rate\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
        (r"\bQ\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "T_c_out": [
        (r"\bT[_\s]?c[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"cold\s+(?:stream\s+)?(?:exit|outlet)\s+temperature\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "s_h_in": [(r"\bs[_\s]?h[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0)],
    "s_h_out": [(r"\bs[_\s]?h[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0)],
    "s_c_in": [(r"\bs[_\s]?c[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0)],
    "s_c_out": [(r"\bs[_\s]?c[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0)],
    # Boiler-specific
    "h_in": [
        (r"\bh[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"inlet\s+enthalpy\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "h_out": [
        (r"\bh[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"outlet\s+enthalpy\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "s_in": [
        (r"\bs[_\s]?in\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s_out": [
        (r"\bs[_\s]?out\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    # Mixer-specific
    "h3": [
        (r"\bh[_\s]?3\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₃\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "T3": [
        (r"\bT[_\s]?3\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"T₃\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"exit\s+temperature\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "m3": [
        (r"[mṁ][_\s]?3\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"ṁ₃\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s3": [
        (r"\bs[_\s]?3\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₃\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
}


def _auto_convert_tier2(key: str, value: float) -> float:
    """Apply unit auto-conversion heuristics for Tier 2 step values."""
    # Enthalpy: > 10000 likely J/kg → kJ/kg
    if key in ("h1", "h2", "h2s", "h3", "h_in", "h_out",
               "h_h_in", "h_h_out", "h_c_in", "h_c_out"):
        if abs(value) > 10000:
            value /= 1000.0

    # Entropy: > 100 likely J/(kg·K) → kJ/(kg·K)
    if key in ("s1", "s2", "s3", "s_in", "s_out", "s_gen",
               "s_h_in", "s_h_out", "s_c_in", "s_c_out"):
        if abs(value) > 100:
            value /= 1000.0

    # eta_II: > 1 likely percentage → fraction
    if key == "eta_II":
        if value > 1.0 and value <= 100.0:
            value /= 100.0

    return value



# ══════════════════════════════════════════════════════════
# TIER 3: Cycle Analysis Extraction
# ══════════════════════════════════════════════════════════

def _build_state_patterns(prefix: str, max_n: int = 6) -> dict[str, list[tuple[str, float]]]:
    """Build extraction patterns for state-point properties h1-h6, s1-s6, ef1-ef6."""
    subscripts = {1: "₁", 2: "₂", 3: "₃", 4: "₄", 5: "₅", 6: "₆"}
    result = {}
    for n in range(1, max_n + 1):
        key = f"{prefix}{n}"
        sub = subscripts[n]
        result[key] = [
            (r"\b" + prefix + r"[_\s]?" + str(n) + r"\s*[=:≈~]\s*" + _NUMCAP, 1.0),
            (prefix + sub + r"\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        ]
    return result

def _build_component_patterns(prefix: str, components: list[str]) -> dict[str, list[tuple[str, float]]]:
    """Build patterns for component-level quantities like s_gen_pump, x_dest_boiler."""
    result = {}
    for comp in components:
        key = f"{prefix}_{comp}"
        # e.g., s_gen,pump or s_gen_pump or s_gen pump
        result[key] = [
            (r"\b" + prefix.replace("_", r"[_,\s]?") + r"[_,\s]?" + comp + r"\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        ]
    return result

_TIER3_COMPONENTS = [
    "pump", "boiler", "turb", "cond", "HPT", "LPT", "reheater",
    "comp", "cc", "hr", "regen", "throttle", "evap", "total",
]

TIER3_PROPERTY_PATTERNS: dict[str, list[tuple[str, float]]] = {
    # Reuse Tier 2 patterns for h1, h2, h2s, s1, s2, s3, h3
    **{k: v for k, v in TIER2_PROPERTY_PATTERNS.items()},
    # Additional state properties
    "h4": [
        (r"\bh[_\s]?4\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₄\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h5": [
        (r"\bh[_\s]?5\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₅\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h6": [
        (r"\bh[_\s]?6\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₆\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h4s": [
        (r"\bh[_\s]?4s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₄ₛ\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h[_\s]?4,?s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "h5s": [
        (r"\bh[_\s]?5s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h₅ₛ\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"h[_\s]?5,?s\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s4": [
        (r"\bs[_\s]?4\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₄\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s5": [
        (r"\bs[_\s]?5\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₅\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    "s6": [
        (r"\bs[_\s]?6\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"s₆\s*[=:≈~]\s*" + _NUMCAP, 1.0),
    ],
    # Flow exergies
    **_build_state_patterns("ef"),
    # Component works
    "w_pump": [
        (r"\bw[_\s]?pump\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"pump\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "w_comp": [
        (r"\bw[_\s]?comp\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"compressor\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "w_turb": [
        (r"\bw[_\s]?turb\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"turbine\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "w_HPT": [
        (r"\bw[_\s]?HPT\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"HPT\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "w_LPT": [
        (r"\bw[_\s]?LPT\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"LPT\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "w_net": [
        (r"\bw[_\s]?net\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"net\s+work\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Heat transfers
    "q_L": [
        (r"\bq[_\s]?L\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"cooling\s+effect\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "q_H": [
        (r"\bq[_\s]?H\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"heat\s+rejection\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Cycle metrics
    "eta_th": [
        (r"η[_\s]?th\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"eta[_\s]?th\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"thermal\s+efficiency\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "COP_R": [
        (r"\bCOP[_\s]?R?\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"coefficient\s+of\s+performance\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "COP_Carnot": [
        (r"\bCOP[_\s]?Carnot\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Carnot\s+COP\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "x4": [
        (r"\bx[_\s]?4\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"x₄\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"quality\s+(?:after|at)\s+(?:the\s+)?throttle\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Rate quantities
    "W_dot_net": [
        (r"[WẆ][_\s]?(?:dot[_\s]?)?net\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Ẇ[_\s]?net\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"net\s+power\s*(?:output)?\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "W_dot_comp": [
        (r"[WẆ][_\s]?(?:dot[_\s]?)?comp\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Ẇ[_\s]?comp\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"compressor\s+power\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    "Q_dot_L": [
        (r"[QQ̇][_\s]?(?:dot[_\s]?)?L\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"Q̇[_\s]?L\s*[=:≈~]\s*" + _NUMCAP, 1.0),
        (r"cooling\s+capacity\s*[=:≈~is]*\s*(?:approximately\s+)?" + _NUMCAP, 1.0),
    ],
    # Entropy generation per component
    **_build_component_patterns("s_gen", _TIER3_COMPONENTS),
    # Exergy destruction per component
    **_build_component_patterns("x_dest", _TIER3_COMPONENTS),
}


def _auto_convert_tier3(key: str, value: float) -> float:
    """Apply unit auto-conversion heuristics for Tier 3 step values."""
    # Enthalpy: > 10000 likely J/kg -> kJ/kg
    if key.startswith("h") or key.startswith("ef") or key.startswith("w_") or key.startswith("q_") or key.startswith("x_dest"):
        if abs(value) > 10000:
            value /= 1000.0

    # Entropy: > 100 likely J/(kg·K) -> kJ/(kg·K)
    if key.startswith("s") and not key.startswith("s_gen"):
        if abs(value) > 100:
            value /= 1000.0

    # eta_th, eta_II: > 1 likely percentage -> fraction
    if key in ("eta_th", "eta_II"):
        if value > 1.0 and value <= 100.0:
            value /= 100.0

    # x4: > 1 likely percentage -> fraction
    if key == "x4":
        if value > 1.0 and value <= 100.0:
            value /= 100.0

    return value


def extract_tier3_properties(
    response_text: str, expected_step_ids: list[str]
) -> dict[str, float | None]:
    """Extract Tier 3 step values from an LLM response."""
    text = strip_thinking_tags(response_text)
    text = _preprocess(text)
    result: dict[str, float | None] = {}

    for key in expected_step_ids:
        patterns = TIER3_PROPERTY_PATTERNS.get(key)
        if patterns is None:
            patterns = TIER2_PROPERTY_PATTERNS.get(key, [])

        best_value = None
        best_pos = -1
        for pattern, factor in patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                pos = m.start()
                raw = m.group(1).replace(",", "")
                try:
                    val = float(raw) * factor
                except ValueError:
                    continue
                if pos >= best_pos:
                    best_pos = pos
                    best_value = val

        if best_value is not None:
            best_value = _auto_convert_tier3(key, best_value)

        result[key] = best_value

    return result


def extract_tier2_properties(
    response_text: str, expected_step_ids: list[str]
) -> dict[str, float | None]:
    """
    Extract Tier 2 step values from an LLM response.

    Args:
        response_text: Raw LLM response text.
        expected_step_ids: List of step IDs to extract (e.g., ["h1", "w_out", "s_gen"]).

    Returns:
        Dict mapping step_id -> extracted float value (or None).
    """
    text = strip_thinking_tags(response_text)
    text = _preprocess(text)
    result: dict[str, float | None] = {}

    for key in expected_step_ids:
        patterns = TIER2_PROPERTY_PATTERNS.get(key)
        if patterns is None:
            # Fall back to Tier 1 patterns
            patterns = PROPERTY_PATTERNS.get(key, [])

        best_value = None
        best_pos = -1
        for pattern, factor in patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                pos = m.start()
                raw = m.group(1).replace(",", "")
                try:
                    val = float(raw) * factor
                except ValueError:
                    continue
                if pos >= best_pos:
                    best_pos = pos
                    best_value = val

        if best_value is not None:
            best_value = _auto_convert_tier2(key, best_value)

        result[key] = best_value

    return result
