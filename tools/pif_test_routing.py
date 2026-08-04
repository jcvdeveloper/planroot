#!/usr/bin/env python
"""Run PIF routing cases against the executable router."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pif_router import DEFAULT_MATRIX_PATH, load_json, resolve_routing


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "PIF_Routing_Test_Cases.json"


def _compare_case(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = case.get("expected", {})

    for key in ("primary_preset", "depth_profile"):
        if result.get(key) != expected.get(key):
            errors.append(f"{key}: expected {expected.get(key)!r}, got {result.get(key)!r}")

    expected_overlays = sorted(expected.get("active_overlays", []))
    actual_overlays = sorted(result.get("active_overlays", []))
    if actual_overlays != expected_overlays:
        errors.append(f"active_overlays: expected {expected_overlays!r}, got {actual_overlays!r}")

    if "blueprint_profile" in expected and result.get("blueprint_profile") != expected.get("blueprint_profile"):
        errors.append(
            f"blueprint_profile: expected {expected.get('blueprint_profile')!r}, got {result.get('blueprint_profile')!r}"
        )

    if "fallbacks" in expected:
        expected_fallbacks = sorted(expected.get("fallbacks", []))
        actual_fallbacks = sorted(result.get("fallbacks", []))
        if actual_fallbacks != expected_fallbacks:
            errors.append(f"fallbacks: expected {expected_fallbacks!r}, got {actual_fallbacks!r}")

    if not result.get("ok"):
        errors.append(f"router returned errors: {result.get('errors', [])}")

    return errors


def run_cases(matrix_path: Path, cases_path: Path) -> int:
    matrix = load_json(matrix_path)
    cases = load_json(cases_path)
    if not isinstance(cases, list):
        raise ValueError("Routing test cases file must contain a list.")

    failures: list[tuple[str, list[str]]] = []

    for case in cases:
        case_id = case.get("id", "[missing-id]")
        if "answers" in case:
            result = resolve_routing(case.get("answers", {}), matrix, input_mode="answers")
        else:
            result = resolve_routing(case.get("classifiers", {}), matrix, input_mode="classifiers")
        errors = _compare_case(case, result)
        if errors:
            failures.append((case_id, errors))
            print(f"FAIL {case_id}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {case_id}")

    print()
    print(f"Cases: {len(cases)} | Passed: {len(cases) - len(failures)} | Failed: {len(failures)}")

    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate PIF routing test cases.")
    parser.add_argument(
        "--matrix",
        default=str(DEFAULT_MATRIX_PATH),
        help="Path to PIF_Decision_Matrix.json.",
    )
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_CASES_PATH),
        help="Path to PIF_Routing_Test_Cases.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return run_cases(Path(args.matrix), Path(args.cases))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
