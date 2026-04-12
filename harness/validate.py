"""Prompt sensitivity benchmark harness.

The initial public harness supports E9 specificity-gradient runs against any
Ollama-compatible model.

Usage:
    uv run python validate.py e9 --model-name qwen2.5-coder:1.5b
    uv run python validate.py e9 --model-name mistral:7b --host http://localhost:11434 --k 3
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from statistics import mean

from data import Task, TestCase, get_e9_prompts

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / ".output" / "experiments"
DEFAULT_HOST = "http://localhost:11434"


def ollama_generate(
    model_name: str,
    host: str,
    prompt: str,
    *,
    temperature: float,
    max_tokens: int = 4096,
    timeout: int = 300,
) -> tuple[str, float]:
    """Call an Ollama-compatible `/api/generate` endpoint."""
    wrapped = f"Respond with only Python code. No explanations.\n\n{prompt}"
    body: dict[str, object] = {
        "model": model_name,
        "prompt": wrapped,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if "qwen" in model_name.lower():
        body["think"] = False

    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = str(data.get("response", ""))
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text, time.monotonic() - start
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}", time.monotonic() - start


def extract_function(response: str, func_name: str) -> str | None:
    """Extract a generated Python function from a model response."""
    for match in re.finditer(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL):
        code = match.group(1)
        if f"def {func_name}" in code:
            return code

    lines = response.split("\n")
    captured: list[str] = []
    in_func = False
    for line in lines:
        if re.match(rf"\s*def {func_name}\s*\(", line):
            in_func = True
            captured = [line]
        elif in_func:
            if line.strip() == "" or line[0] in " \t":
                captured.append(line)
            else:
                break
    return "\n".join(captured) if captured else None


def run_test(code: str, test: TestCase) -> bool:
    """Execute generated code against one test case."""
    script = f"{code}\n\n_result = {test.call}\nprint(repr(_result))"
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() == test.expected
    except Exception:
        return False


def evaluate_prompt(
    model_name: str,
    host: str,
    prompt_text: str,
    task: Task,
    *,
    temperature: float,
) -> dict[str, object]:
    """Run one prompt and return executable-test results."""
    response, elapsed = ollama_generate(
        model_name,
        host,
        prompt_text,
        temperature=temperature,
    )
    code = extract_function(response, task.func_name) or response
    passed = sum(1 for test in task.tests if run_test(code, test))
    total = len(task.tests)
    return {
        "pass_rate": passed / total if total else 0.0,
        "passed": passed,
        "total": total,
        "elapsed_seconds": round(elapsed, 2),
        "response_chars": len(response),
        "code_extracted": f"def {task.func_name}" in code,
    }


def run_e9(
    *,
    model_name: str,
    host: str,
    k: int,
    temperature: float,
    hardware: str | None,
) -> dict[str, object]:
    """Run the E9 specificity-gradient experiment."""
    if k < 3:
        raise SystemExit("k must be >= 3 for contributed runs")

    prompts = get_e9_prompts()
    results: list[dict[str, object]] = []

    print(f"E9 specificity gradient: {model_name}, k={k}, temperature={temperature}")
    for level, task_name, prompt, task in prompts:
        pass_rates: list[float] = []
        trial_results: list[dict[str, object]] = []
        for trial in range(k):
            result = evaluate_prompt(
                model_name,
                host,
                prompt,
                task,
                temperature=temperature,
            )
            pass_rate = float(result["pass_rate"])
            pass_rates.append(pass_rate)
            trial_results.append({"trial": trial + 1, **result})

        avg_rate = mean(pass_rates)
        print(f"  {task_name:<20} {level:<10} {' '.join(f'{r:.2f}' for r in pass_rates)}")
        results.append(
            {
                "task": task_name,
                "level": level,
                "model_name": model_name,
                "pass_rates": pass_rates,
                "avg_pass_rate": avg_rate,
                "prompt_len": len(prompt),
                "trials": trial_results,
            }
        )

    output: dict[str, object] = {
        "experiment": "e9_specificity",
        "harness_version": "0.1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_name": model_name,
        "model_provider": _provider_from_name(model_name),
        "model_hardware": hardware or "unspecified",
        "host": host,
        "temperature": temperature,
        "k": k,
        "total_calls": len(results) * k,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"e9_specificity_custom_{_slug(model_name)}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nwrote {out_path}")
    return output


def _provider_from_name(model_name: str) -> str:
    head = model_name.split(":", 1)[0].split("/", 1)[0]
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", head).strip("-").lower() or "unknown"


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prompt sensitivity benchmark harness")
    parser.add_argument("experiment", choices=["e9"], help="Experiment to run")
    parser.add_argument("--model-name", required=True, help="Ollama model name")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Ollama API base URL")
    parser.add_argument("--k", type=int, default=3, help="Trials per condition, must be >= 3")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--hardware", default=None, help="Optional hardware description")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_e9(
        model_name=args.model_name,
        host=args.host,
        k=args.k,
        temperature=args.temperature,
        hardware=args.hardware,
    )


if __name__ == "__main__":
    main()
