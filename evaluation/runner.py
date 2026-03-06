"""
Multi-provider LLM evaluation runner for ThermoQA.

Supports: Anthropic, OpenAI, Google, MiniMax, DeepSeek, Ollama.
All SDK imports are lazy — missing packages only break the provider that needs them.
"""

import json
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from evaluation.extractor import extract_properties, strip_thinking_tags
from evaluation.scorer import (
    DatasetResults,
    QuestionResult,
    load_questions,
    score_dataset,
    score_question,
)


SYSTEM_PROMPT = (
    "You are a thermodynamics expert. Answer the following thermodynamics question. "
    "Provide numerical values with their units. For steam/water properties, use "
    "standard steam table values."
)


@dataclass
class ProviderResponse:
    text: str  # Final answer only (thinking stripped)
    raw_text: str  # Full response including thinking
    thinking_text: str | None
    model: str
    latency_s: float
    input_tokens: int | None
    output_tokens: int | None


class BaseProvider(ABC):
    """Abstract base for LLM providers."""

    name: str
    model: str
    is_thinking: bool
    timeout: float
    max_retries: int

    def __init__(self, model: str | None = None, timeout: float = 120.0,
                 max_retries: int = 3):
        if model is not None:
            self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def generate(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        """Call the API with retry and exponential backoff."""
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                return self._call_api(system_prompt, user_prompt)
            except Exception as exc:
                last_exc = exc
                if not self._is_retryable(exc) or attempt == self.max_retries - 1:
                    raise
                wait = min(2 ** attempt * 2, 60)
                print(f"  Retry {attempt + 1}/{self.max_retries} after {wait}s: {exc}")
                time.sleep(wait)
        raise last_exc  # unreachable, but keeps type checker happy

    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        ...

    def _is_retryable(self, exc: Exception) -> bool:
        """Override per provider for provider-specific retryable errors."""
        # Default: retry on connection/timeout errors
        exc_name = type(exc).__name__.lower()
        return any(k in exc_name for k in ("timeout", "connection", "rate", "server"))


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    model = "claude-opus-4-6-20250612"
    is_thinking = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self._client = anthropic.Anthropic(api_key=api_key, timeout=self.timeout)

    def _call_api(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        t0 = time.monotonic()
        message = self._client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000,
            },
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency = time.monotonic() - t0

        text_parts = []
        thinking_parts = []
        for block in message.content:
            if block.type == "thinking":
                thinking_parts.append(block.thinking)
            elif block.type == "text":
                text_parts.append(block.text)

        text = "\n".join(text_parts)
        thinking = "\n".join(thinking_parts) if thinking_parts else None
        raw = (thinking + "\n" + text) if thinking else text

        return ProviderResponse(
            text=text,
            raw_text=raw,
            thinking_text=thinking,
            model=self.model,
            latency_s=latency,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )

    def _is_retryable(self, exc: Exception) -> bool:
        exc_name = type(exc).__name__
        return exc_name in ("RateLimitError", "APITimeoutError", "APIConnectionError",
                            "InternalServerError", "OverloadedError") or super()._is_retryable(exc)


class OpenAICompatibleProvider(BaseProvider):
    """Base for OpenAI-compatible APIs (OpenAI, MiniMax, DeepSeek)."""

    base_url: str | None = None
    api_key_env: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        import openai
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")
        client_kwargs = {"api_key": api_key, "timeout": self.timeout}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self._client = openai.OpenAI(**client_kwargs)

    def _call_api(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        t0 = time.monotonic()
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=16000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        latency = time.monotonic() - t0

        choice = response.choices[0]
        text = choice.message.content or ""
        thinking = getattr(choice.message, "reasoning_content", None)
        raw = (thinking + "\n" + text) if thinking else text

        # Strip inline thinking tags (e.g. MiniMax <think>...</think>)
        text_clean = strip_thinking_tags(text)
        if text_clean != text and not thinking:
            thinking = text  # preserve original as thinking_text
        text = text_clean

        usage = response.usage
        return ProviderResponse(
            text=text,
            raw_text=raw,
            thinking_text=thinking,
            model=self.model,
            latency_s=latency,
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        )

    def _is_retryable(self, exc: Exception) -> bool:
        exc_name = type(exc).__name__
        return exc_name in ("RateLimitError", "APITimeoutError", "APIConnectionError",
                            "InternalServerError") or super()._is_retryable(exc)


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    model = "gpt-5.3"
    is_thinking = True
    api_key_env = "OPENAI_API_KEY"


class MiniMaxProvider(OpenAICompatibleProvider):
    name = "minimax"
    model = "MiniMax-M2.5"
    is_thinking = False
    base_url = "https://api.minimaxi.chat/v1"
    api_key_env = "MINIMAX_API_KEY"


class DeepSeekProvider(OpenAICompatibleProvider):
    name = "deepseek"
    model = "deepseek-reasoner"
    is_thinking = True
    base_url = "https://api.deepseek.com/v1"
    api_key_env = "DEEPSEEK_API_KEY"


class GoogleProvider(BaseProvider):
    name = "google"
    model = "gemini-2.5-flash"
    is_thinking = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self._client = genai.Client(api_key=api_key)
        self._genai = genai

    def _call_api(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        t0 = time.monotonic()
        response = self._client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=self._genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=8000,
            ),
        )
        latency = time.monotonic() - t0

        text = strip_thinking_tags(response.text or "")
        # Collect all parts for raw_text
        raw_parts = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    raw_parts.append(part.text)
        raw = "\n".join(raw_parts) if raw_parts else text

        usage = getattr(response, "usage_metadata", None)
        return ProviderResponse(
            text=text,
            raw_text=raw,
            thinking_text=None,
            model=self.model,
            latency_s=latency,
            input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
            output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
        )


class OllamaProvider(BaseProvider):
    name = "ollama"
    model = "llama3"
    is_thinking = False

    def __init__(self, model: str | None = None, base_url: str = "http://localhost:11434",
                 **kwargs):
        super().__init__(model=model, **kwargs)
        self._base_url = base_url.rstrip("/")

    def _call_api(self, system_prompt: str, user_prompt: str) -> ProviderResponse:
        import urllib.request

        url = f"{self._base_url}/api/generate"
        payload = json.dumps({
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )

        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read())
        latency = time.monotonic() - t0

        raw_text = body.get("response", "")
        text = strip_thinking_tags(raw_text)
        return ProviderResponse(
            text=text,
            raw_text=raw_text,
            thinking_text=None,
            model=self.model,
            latency_s=latency,
            input_tokens=body.get("prompt_eval_count"),
            output_tokens=body.get("eval_count"),
        )


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, type[BaseProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "minimax": MiniMaxProvider,
    "deepseek": DeepSeekProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str, **kwargs) -> BaseProvider:
    """Instantiate a provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)


# ---------------------------------------------------------------------------
# Evaluation orchestration
# ---------------------------------------------------------------------------

def _load_completed_ids(path: str) -> set[str]:
    """Read question IDs already answered in a responses.jsonl file."""
    ids = set()
    if not os.path.exists(path):
        return ids
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ids.add(entry["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def _print_progress(current: int, total: int, qid: str, running_score: float) -> None:
    """Print a progress bar with running score."""
    bar_len = 30
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stdout.write(
        f"\r[{bar}] {current}/{total} {qid} | Running score: {running_score:.1%}"
    )
    sys.stdout.flush()


def run_evaluation(
    provider: BaseProvider,
    questions_path: str,
    output_dir: str,
    n_runs: int = 1,
    delay_s: float = 1.0,
) -> str:
    """
    Run a provider against all questions, score responses, write results.

    Returns the path to the provider results directory.
    """
    questions = load_questions(questions_path)
    provider_dir = os.path.join(output_dir, provider.name)
    os.makedirs(provider_dir, exist_ok=True)
    responses_path = os.path.join(provider_dir, "responses.jsonl")

    for run_idx in range(n_runs):
        if n_runs > 1:
            print(f"\n--- Run {run_idx + 1}/{n_runs} ---")

        completed = _load_completed_ids(responses_path)
        pending = [q for q in questions if q["id"] not in completed]

        if not pending:
            print("All questions already answered. Skipping.")
            continue

        print(f"Questions: {len(questions)} total, {len(completed)} done, {len(pending)} remaining")

        total_score = 0.0
        n_scored = len(completed)
        # Approximate running score from existing responses
        running_score = 0.0

        with open(responses_path, "a") as f_out:
            for i, q in enumerate(pending, 1):
                qid = q["id"]
                expected_keys = list(q["expected"].keys())

                # Show progress before the (potentially slow) API call
                sys.stdout.write(
                    f"\r  [{len(completed) + i}/{len(questions)}] {qid} ..."
                )
                sys.stdout.flush()

                try:
                    resp = provider.generate(SYSTEM_PROMPT, q["question"])
                except Exception as exc:
                    print(f"\n  ERROR on {qid}: {exc}")
                    # Write a failed entry so we can skip on resume if desired
                    entry = {
                        "id": qid,
                        "question": q["question"],
                        "raw_response": "",
                        "response_text": "",
                        "thinking_text": None,
                        "extracted": {},
                        "scores": [],
                        "question_score": 0.0,
                        "model": provider.model,
                        "latency_s": 0.0,
                        "input_tokens": None,
                        "output_tokens": None,
                        "error": str(exc),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    f_out.flush()
                    n_scored += 1
                    _print_progress(len(completed) + i, len(questions), qid, running_score)
                    if delay_s > 0:
                        time.sleep(delay_s)
                    continue

                extracted = extract_properties(resp.text, expected_keys)
                qr = score_question(q, extracted)

                n_scored += 1
                total_score += qr.score
                running_score = total_score / (n_scored - len(completed)) if (n_scored - len(completed)) > 0 else 0.0

                # Build per-property score list
                scores = []
                for pr in qr.property_results:
                    scores.append({
                        "key": pr.prop_key,
                        "expected": pr.expected,
                        "extracted": pr.extracted,
                        "passed": pr.passed,
                        "error_pct": pr.error_pct,
                        "error_type": pr.error_type,
                    })

                entry = {
                    "id": qid,
                    "question": q["question"],
                    "raw_response": resp.raw_text,
                    "response_text": resp.text,
                    "thinking_text": resp.thinking_text,
                    "extracted": {k: v for k, v in extracted.items()},
                    "scores": scores,
                    "question_score": qr.score,
                    "model": resp.model,
                    "latency_s": resp.latency_s,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f_out.flush()

                _print_progress(len(completed) + i, len(questions), qid, running_score)

                if delay_s > 0 and i < len(pending):
                    time.sleep(delay_s)

        print()  # newline after progress bar

    # Generate summary
    summary = _build_summary(questions, responses_path, provider)
    summary_path = os.path.join(provider_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {provider_dir}/")
    print(f"  responses.jsonl: {summary['total_responses']} responses")
    print(f"  summary.json: overall score {summary['mean_question_score']:.1%}")

    return provider_dir


def _build_summary(questions: list[dict], responses_path: str,
                   provider: BaseProvider) -> dict:
    """Build summary.json from responses."""
    # Load responses
    responses = {}
    latencies = []
    input_tokens_list = []
    output_tokens_list = []
    errors = 0

    with open(responses_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            qid = entry["id"]
            if entry.get("error"):
                errors += 1
            responses[qid] = entry.get("response_text", "")
            latencies.append(entry.get("latency_s", 0))
            if entry.get("input_tokens") is not None:
                input_tokens_list.append(entry["input_tokens"])
            if entry.get("output_tokens") is not None:
                output_tokens_list.append(entry["output_tokens"])

    # Score via scorer
    ds = score_dataset(questions, responses)

    summary = {
        "provider": provider.name,
        "model": provider.model,
        "total_questions": ds.total_questions,
        "total_responses": len(responses),
        "total_properties": ds.total_properties,
        "total_correct_properties": ds.total_correct_properties,
        "property_accuracy": round(ds.property_accuracy, 4),
        "mean_question_score": round(ds.mean_question_score, 4),
        "per_category": {
            cat: {k: round(v, 4) if isinstance(v, float) else v for k, v in d.items()}
            for cat, d in ds.per_category.items()
        },
        "per_difficulty": {
            diff: {k: round(v, 4) if isinstance(v, float) else v for k, v in d.items()}
            for diff, d in ds.per_difficulty.items()
        },
        "errors": errors,
        "timing": {
            "mean_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_s": round(min(latencies), 2) if latencies else 0,
            "max_latency_s": round(max(latencies), 2) if latencies else 0,
        },
        "tokens": {
            "total_input": sum(input_tokens_list) if input_tokens_list else None,
            "total_output": sum(output_tokens_list) if output_tokens_list else None,
            "mean_input": round(sum(input_tokens_list) / len(input_tokens_list), 1) if input_tokens_list else None,
            "mean_output": round(sum(output_tokens_list) / len(output_tokens_list), 1) if output_tokens_list else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return summary
