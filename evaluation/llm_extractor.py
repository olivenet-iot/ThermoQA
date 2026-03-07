"""
LLM-based extractor using Claude Sonnet for robust value extraction from model responses.

Falls back gracefully on parse failures. Returns dicts compatible with extract_properties().
"""

import json
import logging
import os
import time

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a precise data extractor. Extract ONLY the final numerical answers "
    "from thermodynamics problem solutions. Never extract intermediate calculations, "
    "cross-checks, or trial values. Return valid JSON only, no other text."
)


class LLMExtractor:
    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-6-20250514"

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

        for attempt in range(2):
            try:
                msg = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = msg.content[0].text.strip()
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
                logger.warning(f"LLM extraction failed after 2 attempts: {e}")
                return {}
            except anthropic.APIError as e:
                logger.warning(f"Anthropic API error during extraction: {e}")
                return {}

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
