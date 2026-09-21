import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.orchestrator import answer_question


ROOT = Path(__file__).resolve().parent


def _equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, list) and isinstance(actual, list):
        if all(isinstance(item, str) for item in expected + actual):
            return set(expected) == set(actual)
        return expected == actual
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.upper() == actual.upper()
    return expected == actual


def _arguments_match(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    return all(key in actual and _equal(value, actual[key]) for key, value in expected.items())


def grade_case(case: dict[str, Any], result: dict[str, Any], strict: bool) -> dict[str, Any]:
    calls = result.get("tool_calls", [])
    actual_names = [call["name"] for call in calls]
    expected_names = case["expected_tools"]
    tools_pass = (
        sorted(actual_names) == sorted(expected_names)
        if strict or not expected_names
        else all(name in actual_names for name in expected_names)
    )

    argument_failures = []
    for tool_name, expected_args in case.get("expected_arguments", {}).items():
        matching_calls = [call for call in calls if call["name"] == tool_name]
        if not matching_calls or not any(
            _arguments_match(expected_args, call.get("arguments", {}))
            for call in matching_calls
        ):
            argument_failures.append(
                {"tool": tool_name, "expected": expected_args, "actual": matching_calls}
            )

    answer_pass = bool(result.get("summary", "").strip())
    expected_plan = case.get("expected_plan", {})
    actual_plan = result.get("query_plan") or {}
    plan_failures = {
        key: {"expected": value, "actual": actual_plan.get(key)}
        for key, value in expected_plan.items()
        if not _equal(value, actual_plan.get(key))
    }
    sources_pass = not case.get("requires_sources") or bool(result.get("sources"))
    return {
        "passed": tools_pass and not argument_failures and answer_pass and not plan_failures and sources_pass,
        "tools_pass": tools_pass,
        "arguments_pass": not argument_failures,
        "answer_present": answer_pass,
        "plan_pass": not plan_failures,
        "plan_failures": plan_failures,
        "sources_pass": sources_pass,
        "expected_tools": expected_names,
        "actual_tools": actual_names,
        "argument_failures": argument_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live FinSight Gemini evaluations")
    parser.add_argument("--case", help="Run one case by id")
    parser.add_argument("--limit", type=int, help="Run only the first N selected cases")
    parser.add_argument(
        "--strict-tools",
        action="store_true",
        help="Fail when Gemini calls additional tools beyond those expected",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Do not write evals/reports/latest.json"
    )
    args = parser.parse_args()

    cases = json.loads((ROOT / "cases.json").read_text())
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            print(f"Unknown case: {args.case}", file=sys.stderr)
            return 2
    if args.limit is not None:
        cases = cases[: max(0, args.limit)]

    rows = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']} ... ", end="", flush=True)
        started = time.perf_counter()
        try:
            result = answer_question(case["question"])
            grade = grade_case(case, result, args.strict_tools)
            error = None
        except Exception as exc:
            result = {"summary": "", "tool_calls": []}
            grade = {"passed": False, "tools_pass": False, "arguments_pass": False}
            error = f"{type(exc).__name__}: {exc}"
        latency = round(time.perf_counter() - started, 3)
        status = "PASS" if grade["passed"] else "FAIL"
        print(f"{status} ({latency}s)")
        if not grade["passed"]:
            print(f"  expected={case['expected_tools']}")
            print(f"  actual={result.get('tool_calls', [])}")
            if error:
                print(f"  error={error}")
        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "latency_seconds": latency,
                "grade": grade,
                "error": error,
                "response": result,
            }
        )

    passed = sum(row["grade"]["passed"] for row in rows)
    total = len(rows)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy_percent": round(passed / total * 100, 2) if total else 0,
        "average_latency_seconds": (
            round(sum(row["latency_seconds"] for row in rows) / total, 3)
            if total
            else 0
        ),
        "cases": rows,
    }
    print(
        f"\nResult: {passed}/{total} passed "
        f"({summary['accuracy_percent']}%), avg {summary['average_latency_seconds']}s"
    )
    if not args.no_report:
        report_dir = ROOT / "reports"
        report_dir.mkdir(exist_ok=True)
        (report_dir / "latest.json").write_text(json.dumps(summary, indent=2))
        print(f"Report: {report_dir / 'latest.json'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
