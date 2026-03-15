"""
LLM-based extractor using Claude Sonnet for robust value extraction from model responses.

Falls back gracefully on parse failures. Returns dicts compatible with extract_properties().
Supports configurable models including OpenAI-compatible APIs (e.g. gpt-5-mini).
"""

import json
import logging
import os
import time

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_EXTRACTOR_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a precise data extractor. Extract ONLY the final numerical answers "
    "from thermodynamics problem solutions. Never extract intermediate calculations, "
    "cross-checks, or trial values. Return valid JSON only, no other text."
)


class LLMExtractor:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.model = model or DEFAULT_EXTRACTOR_MODEL
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self._openai_client = None

    def _call_llm(self, system: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call the configured LLM and return raw response text."""
        if self.model.startswith("gpt") or self.model.startswith("o"):
            # OpenAI-compatible path
            if self._openai_client is None:
                from openai import OpenAI
                self._openai_client = OpenAI()
            response = self._openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_completion_tokens=max_tokens,
            )
            return response.choices[0].message.content
        else:
            # Anthropic path (default)
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return msg.content[0].text

    def _parse_json_response(self, system: str, user_prompt: str,
                             max_tokens: int = 500, label: str = "LLM") -> dict:
        """Call LLM and parse JSON response with retry."""
        for attempt in range(2):
            try:
                text = self._call_llm(system, user_prompt, max_tokens).strip()
                # Strip markdown code fences if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                return json.loads(text)
            except (json.JSONDecodeError, IndexError) as e:
                if attempt == 0:
                    logger.debug(f"JSON parse failed, retrying: {e}")
                    continue
                logger.warning(f"{label} extraction failed: {e}")
                return {}
            except Exception as e:
                logger.warning(f"API error during {label} extraction: {e}")
                return {}

    def extract(
        self,
        response_text: str,
        expected_keys: list[str],
        question_text: str = "",
    ) -> dict[str, float | str | None]:
        """Extract property values from a model response using Sonnet."""
        phase_rule = ""
        if "phase_name" in expected_keys:
            phase_rule = (
                '\n- For "phase_name": use one of these exact strings: '
                '"subcooled_liquid", "saturated_liquid", "wet_steam", '
                '"saturated_vapor", "superheated_vapor", "supercritical"'
            )

        keys_str = ", ".join(f'"{k}"' for k in expected_keys)
        user_prompt = (
            f"QUESTION:\n{question_text}\n\n"
            f"FULL RESPONSE:\n{response_text}\n\n"
            f"Extract the final answer values for these keys: [{keys_str}]\n\n"
            f"Rules:\n"
            f"- Return a JSON object with exactly those keys\n"
            f"- For numerical properties, return the number (float)\n"
            f"- Use null for any value not found in the response\n"
            f"- Extract ONLY final answers, not intermediate steps{phase_rule}\n"
            f"- Return ONLY the JSON object, no explanation"
        )

        return self._parse_json_response(SYSTEM_PROMPT, user_prompt, 500, "LLM")

    def extract_tier2(
        self,
        response_text: str,
        expected_step_ids: list[str],
        question_text: str = "",
    ) -> dict[str, float | None]:
        """Extract Tier 2 step values using Sonnet."""
        keys_str = ", ".join(f'"{k}"' for k in expected_step_ids)

        # Build unit hints for the prompt
        unit_hints = {
            "h1": "kJ/kg", "s1": "kJ/(kg·K)", "h2s": "kJ/kg", "h2": "kJ/kg",
            "s2": "kJ/(kg·K)", "w_out": "kJ/kg", "w_in": "kJ/kg",
            "s_gen": "kJ/(kg·K)", "x_dest": "kJ/kg", "eta_II": "dimensionless (0-1)",
            "h_in": "kJ/kg", "h_out": "kJ/kg", "s_in": "kJ/(kg·K)",
            "s_out": "kJ/(kg·K)", "q_in": "kJ/kg",
            "h_h_in": "kJ/kg", "h_h_out": "kJ/kg", "h_c_in": "kJ/kg",
            "h_c_out": "kJ/kg", "Q_dot": "kW", "T_c_out": "°C",
            "s_h_in": "kJ/(kg·K)", "s_h_out": "kJ/(kg·K)",
            "s_c_in": "kJ/(kg·K)", "s_c_out": "kJ/(kg·K)",
            "S_gen_dot": "kW/K", "X_dest_dot": "kW",
            "V2": "m/s", "h3": "kJ/kg", "T3": "°C", "m3": "kg/s",
            "s3": "kJ/(kg·K)",
        }
        hints = [f'  "{k}": {unit_hints.get(k, "numeric")}' for k in expected_step_ids]

        user_prompt = (
            f"QUESTION:\n{question_text}\n\n"
            f"FULL RESPONSE:\n{response_text}\n\n"
            f"Extract the FINAL answer values for these step variables:\n"
            + "\n".join(hints) + "\n\n"
            f"Rules:\n"
            f"- Return a JSON object with keys: [{keys_str}]\n"
            f"- All values should be numbers (float)\n"
            f"- Use null if not found\n"
            f"- Extract ONLY final answers, ignore intermediate calculations\n"
            f"- eta_II should be a fraction (0-1), not a percentage\n"
            f"- Return ONLY the JSON object"
        )

        return self._parse_json_response(SYSTEM_PROMPT, user_prompt, 500, "LLM Tier 2")

    def extract_tier3(
        self,
        response_text: str,
        expected_step_ids: list[str],
        question_text: str = "",
    ) -> dict[str, float | None]:
        """Extract Tier 3 cycle analysis step values using Sonnet."""
        keys_str = ", ".join(f'"{k}"' for k in expected_step_ids)

        unit_hints = {
            "h1": "kJ/kg", "h2": "kJ/kg", "h3": "kJ/kg", "h4": "kJ/kg",
            "h5": "kJ/kg", "h6": "kJ/kg",
            "h2s": "kJ/kg", "h4s": "kJ/kg", "h5s": "kJ/kg",
            "s1": "kJ/(kg·K)", "s2": "kJ/(kg·K)", "s3": "kJ/(kg·K)",
            "s4": "kJ/(kg·K)", "s5": "kJ/(kg·K)", "s6": "kJ/(kg·K)",
            "ef1": "kJ/kg", "ef2": "kJ/kg", "ef3": "kJ/kg",
            "ef4": "kJ/kg", "ef5": "kJ/kg", "ef6": "kJ/kg",
            "w_pump": "kJ/kg", "w_comp": "kJ/kg", "w_turb": "kJ/kg",
            "w_HPT": "kJ/kg", "w_LPT": "kJ/kg", "w_net": "kJ/kg",
            "q_in": "kJ/kg", "q_L": "kJ/kg", "q_H": "kJ/kg",
            "eta_th": "dimensionless (0-1)", "COP_R": "dimensionless (>1)",
            "COP_Carnot": "dimensionless (>1)", "eta_II": "dimensionless (0-1)",
            "x4": "dimensionless (0-1)",
            "W_dot_net": "kW", "W_dot_comp": "kW", "Q_dot_L": "kW",
            "h7": "kJ/kg", "h8": "kJ/kg", "h9": "kJ/kg",
            "h7s": "kJ/kg", "h9s": "kJ/kg",
            "s7": "kJ/(kg·K)", "s8": "kJ/(kg·K)", "s9": "kJ/(kg·K)",
            "ef7": "kJ/kg", "ef8": "kJ/kg", "ef9": "kJ/kg",
            "T2": "K", "T4": "K", "T5": "K",
            "m_dot_steam": "kg/s",
            "w_gas_turb": "kJ/kg", "w_steam_turb": "kJ/kg",
            "q_combustion": "kJ/kg",
            "W_net_combined": "kW",
            "eta_combined": "dimensionless (0-1)",
            "eta_II_combined": "dimensionless (0-1)",
            "energy_balance_error": "dimensionless (near 0)",
            "energy_balance_error_gas": "dimensionless (near 0)",
            "energy_balance_error_steam": "dimensionless (near 0)",
        }
        # s_gen and x_dest component patterns
        for comp in ["pump", "boiler", "turb", "cond", "HPT", "LPT", "reheater",
                      "comp", "cc", "hr", "regen", "throttle", "evap", "total",
                      "gas_turb", "steam_turb", "HRSG"]:
            unit_hints[f"s_gen_{comp}"] = "kJ/(kg·K)"
            unit_hints[f"x_dest_{comp}"] = "kJ/kg"

        hints = [f'  "{k}": {unit_hints.get(k, "numeric")}' for k in expected_step_ids]

        user_prompt = (
            f"QUESTION:\n{question_text}\n\n"
            f"FULL RESPONSE:\n{response_text}\n\n"
            f"Extract the FINAL answer values for these step variables:\n"
            + "\n".join(hints) + "\n\n"
            f"Rules:\n"
            f"- Return a JSON object with keys: [{keys_str}]\n"
            f"- All values should be numbers (float)\n"
            f"- Use null if not found\n"
            f"- Extract ONLY final answers, ignore intermediate calculations\n"
            f"- eta_th and eta_II should be fractions (0-1), not percentages\n"
            f"- COP values are typically > 1\n"
            f"- Return ONLY the JSON object"
        )

        return self._parse_json_response(SYSTEM_PROMPT, user_prompt, 1000, "LLM Tier 3")

    def extract_batch(
        self, items: list[dict]
    ) -> list[dict[str, float | str | None]]:
        """Extract values from a list of items sequentially.

        Each item should have keys: response_text, expected_keys, question_text
        """
        results = []
        total = len(items)
        for i, item in enumerate(items):
            print(f"  Extracting {i + 1}/{total}...", end="\r")
            extracted = self.extract(
                response_text=item["response_text"],
                expected_keys=item["expected_keys"],
                question_text=item.get("question_text", ""),
            )
            results.append(extracted)
            if i < total - 1:
                time.sleep(0.5)
        print()
        return results
