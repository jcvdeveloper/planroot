#!/usr/bin/env python
"""Test the beginner-facing 'Prompt para IA' rendering for the Planroot/PIF interview.

Invariantes por caso:
- contem o preambulo e as 5 secoes esperadas;
- NAO contem sinais crus ("sinais:" nem nomes de signal como clarity_risk);
- NAO contem o marcador "[PENDENTE]";
- NAO vaza ids internos de preset/overlay (devem aparecer so na forma humana);
- um label respondido do caminho ativo aparece na secao de requisitos;
- uma pergunta nao respondida do caminho ativo aparece na secao de pendencias.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_blueprint import plan_sections, render_ai_prompt  # noqa: E402
from app.pif_question_bank import OPTION_INDEX, QUESTIONS  # noqa: E402
from tools.pif_router import load_json, resolve_routing  # noqa: E402


REQUIRED_HEADINGS = [
    "# Prompt para sua IA construir este projeto",
    "## O projeto em poucas palavras",
    "## O que já foi decidido",
    "## O que ainda precisamos decidir",
    "## O que eu preciso de você",
]


def _all_signal_names() -> set[str]:
    names: set[str] = set()
    for question in QUESTIONS:
        for option in question["options"]:
            names.update(option.get("signals", {}).keys())
    return names


SIGNAL_NAMES = _all_signal_names()


def _active_path_question_ids(routing: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for section in plan_sections(routing):
        ids.extend(section.question_ids)
    return ids


def run_case(case: dict[str, Any], matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    answers = case.get("answers", {})
    routing = resolve_routing(answers, matrix, input_mode="answers")
    if not routing.get("ok"):
        return [f"router error: {routing.get('errors')}"]

    text = render_ai_prompt(answers, routing, brief=case.get("brief"))

    # (1) Preambulo + 5 secoes
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading!r}")

    # (2) Sem sinais crus
    if "sinais:" in text:
        errors.append("AI prompt leaked raw signals block ('sinais:')")
    for name in SIGNAL_NAMES:
        if name in text:
            errors.append(f"AI prompt leaked raw signal name: {name}")

    # (3) Sem [PENDENTE]
    if "[PENDENTE]" in text:
        errors.append("AI prompt contains raw [PENDENTE] marker")

    # (4) Sem vazamento de ids internos de preset/overlay
    preset = routing.get("primary_preset")
    if preset and preset in text:
        errors.append(f"AI prompt leaked internal preset id: {preset}")
    for overlay in routing.get("active_overlays", []):
        # overlays sao tokens snake_case especificos; checa o id literal.
        if overlay in text:
            errors.append(f"AI prompt leaked internal overlay id: {overlay}")

    # (5) Coerencia: um label respondido do caminho ativo aparece;
    #     uma pergunta nao respondida do caminho ativo aparece nas pendencias.
    active_ids = _active_path_question_ids(routing)
    answered_active = [qid for qid in active_ids if answers.get(qid)]
    unanswered_active = [qid for qid in active_ids if not answers.get(qid)]

    if answered_active:
        sample = answered_active[0]
        label = OPTION_INDEX[sample][answers[sample]]["label"]
        if label not in text:
            errors.append(f"answered active-path label missing from requirements: {sample} -> {label!r}")

    if unanswered_active:
        sample = unanswered_active[0]
        prompt = next(q["prompt"] for q in QUESTIONS if q["id"] == sample)
        if prompt not in text:
            errors.append(f"unanswered active-path prompt missing from 'o que falta': {sample}")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the beginner 'Prompt para IA' rendering.")
    parser.add_argument("--matrix", default=str(ROOT / "PIF_Decision_Matrix.json"))
    parser.add_argument("--cases", default=str(ROOT / "PIF_Blueprint_Test_Cases.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    matrix = load_json(Path(args.matrix))
    cases = load_json(Path(args.cases))
    if not isinstance(cases, list):
        print("Prompt test cases file must contain a list.", file=sys.stderr)
        return 2

    passed = 0
    failed = 0
    for case in cases:
        case_id = case.get("id", "<unnamed>")
        errors = run_case(case, matrix)
        if errors:
            failed += 1
            print(f"FAIL {case_id}")
            for err in errors:
                print(f"     - {err}")
        else:
            passed += 1
            print(f"PASS {case_id}")

    print(f"\nCases: {passed + failed} | Passed: {passed} | Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
