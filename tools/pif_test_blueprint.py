#!/usr/bin/env python
"""Test parsimonious blueprint rendering for the deterministic Planroot/PIF interview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_blueprint import render_blueprint, render_minimal_blueprint  # noqa: E402
from app.pif_question_bank import QUESTIONS  # noqa: E402
from tools.pif_router import load_json, resolve_routing  # noqa: E402


def _is_section_present(text: str, heading: str) -> bool:
    return f"## {heading}" in text


def _line_count(text: str) -> int:
    return sum(1 for _ in text.splitlines() if _.strip())


def _answered_question_ids(answers: dict[str, Any]) -> set[str]:
    return {qid for qid, value in answers.items() if value not in (None, "")}


def _check_preset_parsimony(routing: dict[str, Any], text: str) -> list[str]:
    errors: list[str] = []
    primary_preset = routing.get("primary_preset")
    expected_preset_titles = {
        "design_discovery_service": "Preset: design & discovery",
        "local_offline_tool": "Preset: ferramenta local offline",
        "local_small_team_app": "Preset: app local de equipe",
        "api_integration_service": "Preset: API / integração",
        "onprem_business_system": "Preset: sistema on-prem",
        "commerce_frontend_app": "Preset: experiência comercial",
        "cloud_business_app": "Preset: app cloud de negócio",
        "cloud_corporate_integrated": "Preset: cloud corporativo integrado",
    }
    if primary_preset is None:
        return errors
    expected_title = expected_preset_titles.get(primary_preset)
    if expected_title and not _is_section_present(text, expected_title):
        errors.append(f"missing preset section: {expected_title}")
    for title in expected_preset_titles.values():
        if title == expected_title:
            continue
        if _is_section_present(text, title):
            errors.append(f"unexpected preset section rendered: {title}")
    return errors


def _check_overlay_parsimony(routing: dict[str, Any], text: str) -> list[str]:
    errors: list[str] = []
    expected_overlay_titles = {
        "frontend_light": "Overlay: frontend leve",
        "offline_sync": "Overlay: sincronização offline",
        "integrations_heavy": "Overlay: integrações pesadas",
        "security_strong": "Overlay: segurança forte",
        "ops_advanced": "Overlay: operação avançada",
        "multi_tenant": "Overlay: multi-tenant",
        "ai_hitl": "Overlay: IA com HITL",
        "low_code_workflow": "Overlay: low-code / workflow",
    }
    for overlay in routing.get("active_overlays", []):
        title = expected_overlay_titles.get(overlay)
        if title and not _is_section_present(text, title):
            errors.append(f"missing overlay section: {title}")
    for overlay, title in expected_overlay_titles.items():
        if overlay in routing.get("active_overlays", []):
            continue
        if _is_section_present(text, title):
            errors.append(f"inactive overlay rendered: {title}")
    return errors


def _check_no_pendente_garbage(routing: dict[str, Any], answers: dict[str, str], text: str) -> list[str]:
    errors: list[str] = []
    block_lookup = {q["id"]: q["block"] for q in QUESTIONS}
    active_preset = routing.get("primary_preset")
    active_overlays = set(routing.get("active_overlays", []))
    active_preset_block = f"preset_{active_preset}" if active_preset else None
    active_overlay_blocks = {f"overlay_{overlay}" for overlay in active_overlays}

    for line in text.splitlines():
        if "[PENDENTE]" not in line:
            continue
        for qid in block_lookup:
            if f"({qid})" in line or f"`{qid}`" in line:
                block = block_lookup[qid]
                if block.startswith("core_"):
                    continue
                if block == active_preset_block:
                    continue
                if block in active_overlay_blocks:
                    continue
                errors.append(f"[PENDENTE] marker shown for inactive block: {qid} ({block})")
                break
    return errors


def run_case(case: dict[str, Any], matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    answers = case.get("answers", {})
    routing = resolve_routing(answers, matrix, input_mode="answers")
    if not routing.get("ok"):
        return [f"router error: {routing.get('errors')}"]

    minimal_text = render_minimal_blueprint(answers, routing)
    full_text = render_blueprint(answers, routing, pending_questions=[])

    expected_minimum = case.get("expected", {})
    if "minimal_line_count_max" in expected_minimum:
        if _line_count(minimal_text) > expected_minimum["minimal_line_count_max"]:
            errors.append(
                f"minimal blueprint exceeded max lines: {_line_count(minimal_text)} > {expected_minimum['minimal_line_count_max']}"
            )
    if "minimal_required_sections" in expected_minimum:
        for heading in expected_minimum["minimal_required_sections"]:
            if not _is_section_present(minimal_text, heading):
                errors.append(f"minimal blueprint missing section: {heading}")
    if "minimal_forbidden_sections" in expected_minimum:
        for heading in expected_minimum["minimal_forbidden_sections"]:
            if _is_section_present(minimal_text, heading):
                errors.append(f"minimal blueprint has forbidden section: {heading}")

    expected_full = case.get("expected_full", {})
    if "full_required_sections" in expected_full:
        for heading in expected_full["full_required_sections"]:
            if not _is_section_present(full_text, heading):
                errors.append(f"full blueprint missing section: {heading}")
    if "full_forbidden_sections" in expected_full:
        for heading in expected_full["full_forbidden_sections"]:
            if _is_section_present(full_text, heading):
                errors.append(f"full blueprint has forbidden section: {heading}")

    if "minimal_line_count_max" not in expected_minimum and not expected_minimum.get("allow_minimal_empty", False):
        answered = _answered_question_ids(answers)
        if not answered:
            errors.append("test case must provide at least one answer or allow_minimal_empty=true")
        else:
            sections_count = full_text.count("\n## ")
            if sections_count < 1:
                errors.append("full blueprint emitted no sections")

    errors.extend(_check_preset_parsimony(routing, full_text))
    errors.extend(_check_overlay_parsimony(routing, full_text))
    errors.extend(_check_no_pendente_garbage(routing, answers, full_text))

    scope_target = answers.get("scope_target")
    if scope_target in {"mvp_then_iterate", "mvp_plus_near_roadmap", "full_version"}:
        if not _is_section_present(full_text, "Para versão completa"):
            errors.append("full_version scope requires 'Para versão completa' annex")
    else:
        if _is_section_present(full_text, "Para versão completa"):
            errors.append("MVP scope must not emit 'Para versão completa' annex")

    if "max_full_line_count" in expected_minimum:
        if _line_count(full_text) > expected_minimum["max_full_line_count"]:
            errors.append(
                f"full blueprint exceeded max lines: {_line_count(full_text)} > {expected_minimum['max_full_line_count']}"
            )

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate parsimonious blueprint rendering.")
    parser.add_argument("--matrix", default=str(ROOT / "PIF_Decision_Matrix.json"))
    parser.add_argument("--cases", default=str(ROOT / "PIF_Blueprint_Test_Cases.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    matrix = load_json(Path(args.matrix))
    cases = load_json(Path(args.cases))
    if not isinstance(cases, list):
        print("Blueprint test cases file must contain a list.", file=sys.stderr)
        return 2

    failures: list[tuple[str, list[str]]] = []
    for case in cases:
        case_id = case.get("id", "[missing-id]")
        errors = run_case(case, matrix)
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


if __name__ == "__main__":
    raise SystemExit(main())
