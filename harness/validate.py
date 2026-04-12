"""Prompt sensitivity benchmark harness.

The public harness supports E7 format, E8 complexity, E9 specificity, and an
experimental E15 context-budget sweep against any Ollama-compatible model.

Usage:
    uv run python validate.py e7 --model-name qwen2.5-coder:1.5b
    uv run python validate.py e8 --model-name qwen2.5-coder:1.5b
    uv run python validate.py e9 --model-name mistral:7b --host http://localhost:11434 --k 3
    uv run python validate.py e15 --model-name qwen2.5-coder:1.5b --k 3
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import time
from typing import Optional
import urllib.request
from pathlib import Path
from statistics import mean

from data import TASKS, Task, TestCase, get_e9_prompts

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / ".output" / "experiments"
DEFAULT_HOST = "http://localhost:11434"
E7_TASK_NAMES = ("fizzbuzz", "reverse_words", "flatten", "two_sum")
E8_TASK_NAMES = ("fizzbuzz", "flatten", "two_sum", "run_length_encode")
E15_TASK_NAMES = ("fizzbuzz", "flatten", "two_sum", "run_length_encode")
E7_FORMATS = ("xml", "markdown", "plain")
E8_LEVELS = ("minimal", "role+constr", "examples", "maximal")
E15_CONDITIONS = ("short_sparse", "long_sparse", "short_dense", "long_dense")

_XML_TEMPLATE = (
    "<task>\n{task}\n</task>\n\n"
    "<constraints>\n{constraints}\n</constraints>\n\n"
    "<examples>\n{examples}\n</examples>"
)
_MD_TEMPLATE = "## Task\n{task}\n\n## Constraints\n{constraints}\n\n## Examples\n{examples}"
_PLAIN_TEMPLATE = "{task}\n\n{constraints}\n\n{examples}"


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
    lowered = model_name.lower()
    if "qwen" in lowered or "gemma4" in lowered:
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


def extract_function(response: str, func_name: str) -> Optional[str]:
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

def task_subset(task_names: tuple[str, ...]) -> list[Task]:
    by_name = {task.name: task for task in TASKS}
    return [by_name[name] for name in task_names]


def parse_name_subset(raw: Optional[str], allowed: tuple[str, ...], label: str) -> tuple[str, ...]:
    """Parse a comma-separated subset and validate against allowed names."""
    if not raw:
        return allowed

    names = tuple(part.strip() for part in raw.split(",") if part.strip())
    invalid = [name for name in names if name not in allowed]
    if invalid:
        allowed_text = ", ".join(allowed)
        invalid_text = ", ".join(invalid)
        raise SystemExit(f"unknown {label}: {invalid_text}; allowed values: {allowed_text}")
    return names


def prompt_parts(task: Task) -> tuple[str, str, str]:
    """Extract a stable task/constraints/examples decomposition from public prompts."""
    prompt = task.prompts["strong"]
    lines = [line.strip() for line in prompt.strip().splitlines() if line.strip()]

    task_line = ""
    constraints: list[str] = []
    examples: list[str] = []
    in_examples = False

    for line in lines:
        lower = line.lower()
        if not task_line and not line.startswith("- "):
            task_line = line
            continue
        if lower.startswith("examples:"):
            in_examples = True
            continue
        if in_examples or "->" in line or "returns" in lower:
            examples.append(line)
            continue
        if line.startswith("- "):
            constraints.append(line)

    task_text = task_line or task.prompts["basic"]
    constraints_text = "\n".join(constraints) if constraints else "No specific constraints."
    examples_text = "\n".join(examples) if examples else "No examples."
    return task_text, constraints_text, examples_text


def make_e7_variants(task: Task) -> dict[str, str]:
    """Reformat the same task content into delimiter-only format variants."""
    task_text, constraints_text, examples_text = prompt_parts(task)
    return {
        "xml": _XML_TEMPLATE.format(
            task=task_text,
            constraints=constraints_text,
            examples=examples_text,
        ),
        "markdown": _MD_TEMPLATE.format(
            task=task_text,
            constraints=constraints_text,
            examples=examples_text,
        ),
        "plain": _PLAIN_TEMPLATE.format(
            task=task_text,
            constraints=constraints_text,
            examples=examples_text,
        ),
    }


def make_e8_variants(task: Task) -> dict[str, str]:
    """Create a public complexity sweep with the same task semantics."""
    task_text, constraints_text, examples_text = prompt_parts(task)
    return {
        "minimal": task.prompts["basic"],
        "role+constr": (
            "You are a careful Python developer.\n\n"
            f"{task_text}\n\n"
            f"Constraints:\n{constraints_text}"
        ),
        "examples": (
            f"{task_text}\n\n"
            f"Examples:\n{examples_text}"
        ),
        "maximal": task.prompts["expert"],
    }


def make_e15_variants(task: Task) -> dict[str, str]:
    """Factor prompt length and semantic density into a 2x2 sweep."""
    task_text, constraints_text, examples_text = prompt_parts(task)
    constraint_lines = [line.strip("- ").strip() for line in constraints_text.splitlines() if line.strip()]
    example_lines = [line.strip("- ").strip() for line in examples_text.splitlines() if line.strip()]
    compact_constraints = "; ".join(constraint_lines) if constraint_lines else "No additional constraints."
    compact_examples = "; ".join(example_lines) if example_lines else "No examples."

    return {
        "short_sparse": task.prompts["basic"],
        "long_sparse": (
            "Write a Python function for the following task.\n\n"
            f"Task: {task.prompts['basic']}\n\n"
            "Keep the implementation direct and readable. Return only Python code. "
            "The task sentence above is the full requirement; there are no extra "
            "examples or hidden constraints in this version."
        ),
        "short_dense": (
            f"{task_text}\n\n"
            f"Constraints: {compact_constraints}\n"
            f"Examples: {compact_examples}"
        ),
        "long_dense": (
            "You are a careful Python developer implementing a small utility.\n\n"
            f"Task:\n{task_text}\n\n"
            "Follow the full task contract below and match the examples exactly.\n\n"
            f"Constraints:\n{constraints_text}\n\n"
            f"Examples:\n{examples_text}\n\n"
            "Return only the Python function implementation."
        ),
    }


def _clip(text: Optional[str], limit: int = 240) -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit - 3]}..."


def _literal_type(value_repr: Optional[str]) -> Optional[str]:
    if value_repr is None:
        return None
    try:
        return type(ast.literal_eval(value_repr)).__name__
    except Exception:  # noqa: BLE001
        return None


def _stderr_error_type(stderr_text: str) -> Optional[str]:
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*Error|SyntaxError|IndentationError|TabError)", stderr_text)
    return match.group(1) if match else None


def _is_edge_case_call(call: str) -> bool:
    markers = ("[]", "''", '""', "(0)", "('')", "flatten([])", "fizzbuzz(0)")
    return any(marker in call for marker in markers)


def classify_failure_heuristic(
    *,
    response: str,
    code_extracted: bool,
    test_results: list[dict[str, object]],
) -> str:
    """Assign a coarse, explainable failure label for future E14 analysis."""
    failed = [item for item in test_results if not bool(item["passed"])]
    if not failed:
        return "no_failure"
    if response.startswith("ERROR:"):
        return "generation_error"
    if not code_extracted:
        return "extraction_failure"

    error_types = {str(item["error_type"]) for item in failed if item.get("error_type")}
    if {"SyntaxError", "IndentationError", "TabError"} & error_types:
        return "syntax_error"
    if error_types:
        return "runtime_error"

    if any(
        item.get("actual_type") and item.get("expected_type") and item["actual_type"] != item["expected_type"]
        for item in failed
    ):
        return "wrong_output_type"
    if failed and all(_is_edge_case_call(str(item["call"])) for item in failed):
        return "likely_edge_case"
    return "wrong_algorithm_or_logic"


def run_test(code: str, test: TestCase) -> dict[str, object]:
    """Execute generated code against one test case and keep failure artifacts."""
    script = (
        "import json\n"
        "__out = {'ok': False, 'actual_repr': None, 'error_type': None, 'error_message': None}\n"
        f"__code = {code!r}\n"
        f"__call = {test.call!r}\n"
        "try:\n"
        "    __ns = {}\n"
        "    exec(__code, __ns, __ns)\n"
        "    _result = eval(__call, __ns, __ns)\n"
        "    __out['ok'] = True\n"
        "    __out['actual_repr'] = repr(_result)\n"
        "except Exception as exc:\n"
        "    __out['error_type'] = type(exc).__name__\n"
        "    __out['error_message'] = str(exc)\n"
        "print(json.dumps(__out))\n"
    )
    base: dict[str, object] = {
        "call": test.call,
        "expected_repr": test.expected,
        "expected_type": _literal_type(test.expected),
        "actual_repr": None,
        "actual_type": None,
        "passed": False,
        "error_type": None,
        "error_message": None,
    }
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {**base, "error_type": "TimeoutExpired", "error_message": "test execution exceeded 5s"}
    except Exception as exc:  # noqa: BLE001
        return {**base, "error_type": type(exc).__name__, "error_message": str(exc)}

    if result.returncode != 0:
        stderr_text = (result.stderr or "").strip()
        return {
            **base,
            "error_type": _stderr_error_type(stderr_text) or "InterpreterError",
            "error_message": _clip(stderr_text) or "python -c execution failed",
        }

    try:
        payload = json.loads((result.stdout.strip().splitlines() or ["{}"])[-1])
    except json.JSONDecodeError:
        return {
            **base,
            "error_type": "HarnessDecodeError",
            "error_message": _clip(result.stdout or result.stderr),
        }

    actual_repr = payload.get("actual_repr")
    actual_type = _literal_type(actual_repr) if isinstance(actual_repr, str) else None
    passed = bool(payload.get("ok")) and actual_repr == test.expected
    return {
        **base,
        "actual_repr": actual_repr,
        "actual_type": actual_type,
        "passed": passed,
        "error_type": payload.get("error_type"),
        "error_message": _clip(payload.get("error_message")),
    }


def evaluate_prompt(
    model_name: str,
    host: str,
    prompt_text: str,
    task: Task,
    *,
    temperature: float,
    timeout: int,
    max_tokens: int,
) -> dict[str, object]:
    """Run one prompt and return executable-test results."""
    response, elapsed = ollama_generate(
        model_name,
        host,
        prompt_text,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    code = extract_function(response, task.func_name) or response
    code_extracted = f"def {task.func_name}" in code
    test_results = [run_test(code, test) for test in task.tests]
    passed = sum(1 for item in test_results if bool(item["passed"]))
    total = len(test_results)
    failure_mode = classify_failure_heuristic(
        response=response,
        code_extracted=code_extracted,
        test_results=test_results,
    )
    output: dict[str, object] = {
        "pass_rate": passed / total if total else 0.0,
        "passed": passed,
        "total": total,
        "elapsed_seconds": round(elapsed, 2),
        "response_chars": len(response),
        "code_extracted": code_extracted,
        "failure_mode_heuristic": failure_mode,
        "response_preview": _clip(response, limit=160),
        "code_preview": _clip(code, limit=160),
        "test_results": test_results,
    }
    if passed < total:
        output["raw_response"] = response
        output["extracted_code"] = code
    return output


def run_e9(
    *,
    model_name: str,
    host: str,
    k: int,
    temperature: float,
    hardware: Optional[str],
    timeout: int = 300,
    max_tokens: int = 4096,
    progress: bool = False,
    **_: object,
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
            if progress:
                print(f"    trial {trial + 1}/{k} task={task_name} level={level}", flush=True)
            result = evaluate_prompt(
                model_name,
                host,
                prompt,
                task,
                temperature=temperature,
                timeout=timeout,
                max_tokens=max_tokens,
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
                "prompt": prompt,
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
        "max_tokens": max_tokens,
        "k": k,
        "total_calls": len(results) * k,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"e9_specificity_custom_{_slug(model_name)}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nwrote {out_path}")
    return output


def run_e7(
    *,
    model_name: str,
    host: str,
    k: int,
    temperature: float,
    hardware: Optional[str],
    timeout: int = 300,
    max_tokens: int = 4096,
    progress: bool = False,
    **_: object,
) -> dict[str, object]:
    """Run the E7 delimiter-only format comparison."""
    if k < 3:
        raise SystemExit("k must be >= 3 for contributed or comparative runs")

    tasks = task_subset(E7_TASK_NAMES)
    results: list[dict[str, object]] = []

    print(f"E7 format comparison: {model_name}, k={k}, temperature={temperature}")
    for task in tasks:
        variants = make_e7_variants(task)
        for fmt_name in E7_FORMATS:
            prompt = variants[fmt_name]
            pass_rates: list[float] = []
            trial_results: list[dict[str, object]] = []
            for trial in range(k):
                if progress:
                    print(
                        f"    trial {trial + 1}/{k} task={task.name} format={fmt_name}",
                        flush=True,
                    )
                result = evaluate_prompt(
                    model_name,
                    host,
                    prompt,
                    task,
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
                pass_rate = float(result["pass_rate"])
                pass_rates.append(pass_rate)
                trial_results.append({"trial": trial + 1, **result})

            avg_rate = mean(pass_rates)
            print(f"  {task.name:<20} {fmt_name:<10} {' '.join(f'{r:.2f}' for r in pass_rates)}")
            results.append(
                {
                    "task": task.name,
                    "format": fmt_name,
                    "model_name": model_name,
                    "prompt": prompt,
                    "pass_rates": pass_rates,
                    "avg_pass_rate": avg_rate,
                    "prompt_len": len(prompt),
                    "trials": trial_results,
                }
            )

    output: dict[str, object] = {
        "experiment": "e7_format",
        "harness_version": "0.1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_name": model_name,
        "model_provider": _provider_from_name(model_name),
        "model_hardware": hardware or "unspecified",
        "host": host,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "k": k,
        "formats": list(E7_FORMATS),
        "tasks": [task.name for task in tasks],
        "total_calls": len(results) * k,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"e7_format_custom_{_slug(model_name)}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nwrote {out_path}")
    return output


def run_e8(
    *,
    model_name: str,
    host: str,
    k: int,
    temperature: float,
    hardware: Optional[str],
    timeout: int = 300,
    max_tokens: int = 4096,
    progress: bool = False,
    **_: object,
) -> dict[str, object]:
    """Run the E8 prompt-complexity comparison."""
    if k < 3:
        raise SystemExit("k must be >= 3 for contributed or comparative runs")

    tasks = task_subset(E8_TASK_NAMES)
    results: list[dict[str, object]] = []

    print(f"E8 complexity sweep: {model_name}, k={k}, temperature={temperature}")
    for task in tasks:
        variants = make_e8_variants(task)
        for level in E8_LEVELS:
            prompt = variants[level]
            pass_rates: list[float] = []
            trial_results: list[dict[str, object]] = []
            for trial in range(k):
                if progress:
                    print(
                        f"    trial {trial + 1}/{k} task={task.name} level={level}",
                        flush=True,
                    )
                result = evaluate_prompt(
                    model_name,
                    host,
                    prompt,
                    task,
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
                pass_rate = float(result["pass_rate"])
                pass_rates.append(pass_rate)
                trial_results.append({"trial": trial + 1, **result})

            avg_rate = mean(pass_rates)
            print(f"  {task.name:<20} {level:<12} {' '.join(f'{r:.2f}' for r in pass_rates)}")
            results.append(
                {
                    "task": task.name,
                    "level": level,
                    "model_name": model_name,
                    "prompt": prompt,
                    "pass_rates": pass_rates,
                    "avg_pass_rate": avg_rate,
                    "prompt_len": len(prompt),
                    "trials": trial_results,
                }
            )

    output: dict[str, object] = {
        "experiment": "e8_complexity",
        "harness_version": "0.1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_name": model_name,
        "model_provider": _provider_from_name(model_name),
        "model_hardware": hardware or "unspecified",
        "host": host,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "k": k,
        "levels": list(E8_LEVELS),
        "tasks": [task.name for task in tasks],
        "total_calls": len(results) * k,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"e8_complexity_custom_{_slug(model_name)}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nwrote {out_path}")
    return output


def run_e15(
    *,
    model_name: str,
    host: str,
    k: int,
    temperature: float,
    hardware: Optional[str],
    timeout: int = 300,
    max_tokens: int = 4096,
    progress: bool = False,
    task_names: tuple[str, ...] = E15_TASK_NAMES,
    condition_names: tuple[str, ...] = E15_CONDITIONS,
    **_: object,
) -> dict[str, object]:
    """Run the E15 context-budget decomposition sweep."""
    if k < 1:
        raise SystemExit("k must be >= 1")
    if k < 3:
        print("warning: k < 3 makes this an exploratory/diagnostic E15 run", flush=True)

    tasks = task_subset(task_names)
    results: list[dict[str, object]] = []

    print(
        f"E15 context-budget sweep: {model_name}, k={k}, temperature={temperature}, "
        f"timeout={timeout}, max_tokens={max_tokens}"
    )
    for task in tasks:
        variants = make_e15_variants(task)
        for condition in condition_names:
            prompt = variants[condition]
            pass_rates: list[float] = []
            trial_results: list[dict[str, object]] = []
            for trial in range(k):
                if progress:
                    print(
                        f"    trial {trial + 1}/{k} task={task.name} condition={condition}",
                        flush=True,
                    )
                result = evaluate_prompt(
                    model_name,
                    host,
                    prompt,
                    task,
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
                pass_rate = float(result["pass_rate"])
                pass_rates.append(pass_rate)
                trial_results.append({"trial": trial + 1, **result})

            avg_rate = mean(pass_rates)
            print(f"  {task.name:<20} {condition:<14} {' '.join(f'{r:.2f}' for r in pass_rates)}")
            results.append(
                {
                    "task": task.name,
                    "condition": condition,
                    "length_bucket": "long" if condition.startswith("long_") else "short",
                    "density_bucket": "dense" if condition.endswith("_dense") else "sparse",
                    "model_name": model_name,
                    "prompt": prompt,
                    "pass_rates": pass_rates,
                    "avg_pass_rate": avg_rate,
                    "prompt_len": len(prompt),
                    "trials": trial_results,
                }
            )

    output: dict[str, object] = {
        "experiment": "e15_context_budget",
        "harness_version": "0.1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_name": model_name,
        "model_provider": _provider_from_name(model_name),
        "model_hardware": hardware or "unspecified",
        "host": host,
        "temperature": temperature,
        "k": k,
        "timeout": timeout,
        "max_tokens": max_tokens,
        "conditions": list(condition_names),
        "tasks": [task.name for task in tasks],
        "total_calls": len(results) * k,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"e15_context_budget_custom_{_slug(model_name)}.json"
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
    parser.add_argument("experiment", choices=["e7", "e8", "e9", "e15"], help="Experiment to run")
    parser.add_argument("--model-name", required=True, help="Ollama model name")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Ollama API base URL")
    parser.add_argument("--k", type=int, default=3, help="Trials per condition, must be >= 3")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=300, help="Per-call timeout in seconds")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Maximum generated tokens")
    parser.add_argument("--hardware", default=None, help="Optional hardware description")
    parser.add_argument("--progress", action="store_true", help="Print per-trial progress")
    parser.add_argument(
        "--tasks",
        default=None,
        help="Optional comma-separated E15 task subset "
        f"({', '.join(E15_TASK_NAMES)})",
    )
    parser.add_argument(
        "--conditions",
        default=None,
        help="Optional comma-separated E15 condition subset "
        f"({', '.join(E15_CONDITIONS)})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task_names = parse_name_subset(args.tasks, E15_TASK_NAMES, "tasks")
    condition_names = parse_name_subset(args.conditions, E15_CONDITIONS, "conditions")
    runner = {
        "e7": run_e7,
        "e8": run_e8,
        "e9": run_e9,
        "e15": run_e15,
    }[args.experiment]
    runner(
        model_name=args.model_name,
        host=args.host,
        k=args.k,
        temperature=args.temperature,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        hardware=args.hardware,
        progress=args.progress,
        task_names=task_names,
        condition_names=condition_names,
    )


if __name__ == "__main__":
    main()
