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
