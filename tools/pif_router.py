#!/usr/bin/env python
"""Executable router for the deterministic Planroot/PIF interview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX_PATH = ROOT / "PIF_Decision_Matrix.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_question_bank import OPTION_INDEX, QUESTION_INDEX, QUESTIONS  # noqa: E402


class RoutingError(ValueError):
    """Raised when the routing matrix is structurally invalid."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _condition_label(condition: dict[str, Any]) -> str:
    if "field" in condition:
        op = condition.get("op")
        if op == "in":
            values = ", ".join(condition.get("values", []))
            return f"{condition['field']} in {{{values}}}"
        if op == "eq":
            return f"{condition['field']} = {condition.get('value')}"
        if op == "gte":
            return f"{condition['field']} >= {condition.get('value')}"
        if op == "lte":
            return f"{condition['field']} <= {condition.get('value')}"
        return f"{condition['field']} {op}"

    match = condition.get("match", "all")
    nested = condition.get("conditions", [])
    separator = " OR " if match == "any" else " AND "
    return "(" + separator.join(_condition_label(item) for item in nested) + ")"


def _rule_label(rule: dict[str, Any]) -> str:
    match = rule.get("match", "all")
    conditions = rule.get("conditions", [])
    if match == "always":
        return "always"

    separator = " OR " if match == "any" else " AND "
    return separator.join(_condition_label(condition) for condition in conditions)


def _eval_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    if "field" not in condition:
        return _eval_conditions(condition.get("match", "all"), condition.get("conditions", []), context)

    value = context.get(condition["field"])
    op = condition.get("op")

    if op == "eq":
        return value == condition.get("value")
    if op == "in":
        return value in condition.get("values", [])
    if op == "gte":
        return isinstance(value, (int, float)) and value >= condition.get("value")
    if op == "lte":
        return isinstance(value, (int, float)) and value <= condition.get("value")

    raise RoutingError(f"Unsupported condition operator: {op!r}")


def _eval_conditions(match: str, conditions: list[dict[str, Any]], context: dict[str, Any]) -> bool:
    if match == "always":
        return True
    if match == "all":
        return all(_eval_condition(condition, context) for condition in conditions)
    if match == "any":
        return any(_eval_condition(condition, context) for condition in conditions)

    raise RoutingError(f"Unsupported match mode: {match!r}")


def _sorted_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rules, key=lambda rule: rule.get("priority", 9999))


def _block_id_for_preset(preset: str) -> str:
    return f"preset_{preset}"


def _block_id_for_overlay(overlay: str) -> str:
    return f"overlay_{overlay}"


def validate_classifiers(
    matrix: dict[str, Any],
    classifiers: dict[str, Any],
) -> tuple[dict[str, str], list[str], list[str]]:
    normalized: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []

    domains = matrix.get("domains", {})
    for field, accepted_values in domains.items():
        raw_value = classifiers.get(field)
        if raw_value in (None, ""):
            warnings.append(f"Missing classifier: {field}")
            continue

        value = str(raw_value).strip()
        normalized[field] = value

        if value not in accepted_values:
            accepted = ", ".join(accepted_values)
            errors.append(f"Invalid value for {field}: {value!r}. Accepted: {accepted}")

    extra_fields = sorted(set(classifiers) - set(domains))
    for field in extra_fields:
        warnings.append(f"Ignored unknown classifier: {field}")

    return normalized, warnings, errors


def _build_label_index(question_id: str) -> dict[str, dict[str, Any]]:
    return {option["label"]: option for option in QUESTION_INDEX[question_id]["options"]}


# Sinais que cada valor de classificador carrega, lidos do proprio banco de
# perguntas: {campo: {valor: {sinal: peso}}}.
CLASSIFIER_SIGNALS: dict[str, dict[str, dict[str, int]]] = {}
for _question in QUESTIONS:
    _field = _question.get("classifier_field")
    if not _field:
        continue
    CLASSIFIER_SIGNALS[_field] = {
        option["classifier_value"]: option.get("signals", {})
        for option in _question["options"]
        if option.get("classifier_value")
    }


def derive_signals_from_classifiers(
    matrix: dict[str, Any],
    classifiers: dict[str, str],
) -> dict[str, int]:
    """Sinais implicados por um conjunto de classificadores.

    Existe porque `input_mode="classifiers"` nao passa pela entrevista e, sem
    isto, entraria nas regras com todos os sinais em zero -- fazendo a mesma
    rota decidir diferente conforme o modo de entrada. A consolidacao tornou
    isso critico: campos como `operational_criticality` foram substituidos por
    sinais, que neste modo simplesmente nao existiriam.

    Cobre apenas o que os classificadores implicam. Um chamador que queira o
    peso das respostas de nucleo deve usar `input_mode="answers"`.
    """
    signals = {field: 0 for field in matrix.get("signal_fields", [])}
    for field, value in classifiers.items():
        for signal_field, increment in CLASSIFIER_SIGNALS.get(field, {}).get(value, {}).items():
            signals[signal_field] = signals.get(signal_field, 0) + int(increment)
    return signals


def normalize_answers(
    matrix: dict[str, Any],
    answers: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, int], list[str], list[str], list[str]]:
    normalized_answers: dict[str, str] = {}
    classifiers: dict[str, str] = {}
    signals = {field: 0 for field in matrix.get("signal_fields", [])}
    warnings: list[str] = []
    errors: list[str] = []
    pending_questions: list[str] = []

    question_ids = {question["id"] for question in QUESTIONS}
    for question in QUESTIONS:
        question_id = question["id"]
        raw_answer = answers.get(question_id)
        if raw_answer in (None, ""):
            warnings.append(f"Missing answer: {question_id}")
            pending_questions.append(question_id)
            continue

        option = OPTION_INDEX[question_id].get(str(raw_answer))
        if option is None:
            option = _build_label_index(question_id).get(str(raw_answer))
        if option is None:
            accepted = ", ".join(sorted(OPTION_INDEX[question_id]))
            errors.append(f"Invalid answer for {question_id}: {raw_answer!r}. Accepted option ids: {accepted}")
            continue

        normalized_answers[question_id] = option["id"]

        for signal_field, increment in option.get("signals", {}).items():
            signals[signal_field] = signals.get(signal_field, 0) + int(increment)

        classifier_field = question.get("classifier_field")
        classifier_value = option.get("classifier_value")
        if classifier_field and classifier_value:
            classifiers[classifier_field] = classifier_value

    extra_answers = sorted(set(answers) - question_ids)
    for question_id in extra_answers:
        warnings.append(f"Ignored unknown answer: {question_id}")

    return normalized_answers, classifiers, signals, warnings, errors, pending_questions


def _build_context(
    matrix: dict[str, Any],
    classifiers: dict[str, str],
    signals: dict[str, int],
) -> dict[str, Any]:
    context: dict[str, Any] = {field: 0 for field in matrix.get("signal_fields", [])}
    context.update(signals)
    context.update(classifiers)
    return context


def _resolve_blueprint_profile(matrix: dict[str, Any], context: dict[str, Any]) -> dict[str, str]:
    profile: dict[str, str] = {}
    for field, rules in matrix.get("blueprint_profile_rules", {}).items():
        for rule in _sorted_rules(rules):
            if _eval_conditions(rule.get("match", "all"), rule.get("conditions", []), context):
                profile[field] = rule["result"]
                break
    return profile


def resolve_routing(
    input_data: dict[str, Any],
    matrix: dict[str, Any] | None = None,
    manual_overlays: list[str] | None = None,
    input_mode: str = "classifiers",
) -> dict[str, Any]:
    matrix = matrix or load_json(DEFAULT_MATRIX_PATH)
    manual_overlays = manual_overlays or []

    signals = {field: 0 for field in matrix.get("signal_fields", [])}
    normalized_answers: dict[str, str] = {}
    pending_questions: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    if input_mode == "answers":
        (
            normalized_answers,
            derived_classifiers,
            signals,
            answer_warnings,
            answer_errors,
            pending_questions,
        ) = normalize_answers(matrix, input_data)
        warnings.extend(answer_warnings)
        errors.extend(answer_errors)
        normalized_classifiers, classifier_warnings, classifier_errors = validate_classifiers(matrix, derived_classifiers)
    elif input_mode == "classifiers":
        normalized_classifiers, classifier_warnings, classifier_errors = validate_classifiers(matrix, input_data)
        if not classifier_errors:
            signals = derive_signals_from_classifiers(matrix, normalized_classifiers)
    else:
        raise RoutingError(f"Unsupported input mode: {input_mode!r}")

    warnings.extend(classifier_warnings)
    errors.extend(classifier_errors)
    if errors:
        return {
            "ok": False,
            "input_mode": input_mode,
            "errors": errors,
            "warnings": warnings,
            "answers": normalized_answers,
            "classifiers": normalized_classifiers if "normalized_classifiers" in locals() else {},
            "signals": signals,
            "pending_questions": pending_questions,
        }

    context = _build_context(matrix, normalized_classifiers, signals)
    decision_trace: list[dict[str, Any]] = []

    depth_profile = None
    for rule in _sorted_rules(matrix.get("depth_rules", [])):
        matched = _eval_conditions(rule.get("match", "all"), rule.get("conditions", []), context)
        decision_trace.append(
            {
                "stage": "depth_profile",
                "priority": rule.get("priority"),
                "rule": _rule_label(rule),
                "matched": matched,
                "result": rule.get("result") if matched else None,
            }
        )
        if matched:
            depth_profile = rule["result"]
            break

    primary_preset = None
    preset_assumption_required = False
    preset_rationale = ""
    for rule in _sorted_rules(matrix.get("preset_rules", [])):
        matched = _eval_conditions(rule.get("match", "all"), rule.get("conditions", []), context)
        decision_trace.append(
            {
                "stage": "primary_preset",
                "priority": rule.get("priority"),
                "rule": _rule_label(rule),
                "matched": matched,
                "result": rule.get("result") if matched else None,
            }
        )
        if matched:
            primary_preset = rule["result"]
            preset_assumption_required = bool(rule.get("assumption_required", False))
            preset_rationale = _rule_label(rule)
            break

    active_overlays: list[str] = []
    inactive_overlays: list[dict[str, str]] = []
    known_overlays = {rule["overlay"] for rule in matrix.get("overlay_rules", [])}

    for rule in matrix.get("overlay_rules", []):
        overlay = rule["overlay"]
        matched = _eval_conditions(rule.get("match", "all"), rule.get("conditions", []), context)
        manually_enabled = overlay in manual_overlays
        decision_trace.append(
            {
                "stage": "active_overlays",
                "overlay": overlay,
                "rule": _rule_label(rule),
                "matched": matched,
                "manual": manually_enabled,
                "result": overlay if matched or manually_enabled else None,
            }
        )

        if matched or manually_enabled:
            active_overlays.append(overlay)
        else:
            inactive_overlays.append(
                {
                    "module": _block_id_for_overlay(overlay),
                    "reason": f"Rule not matched: {_rule_label(rule)}",
                }
            )

    unknown_manual = sorted(set(manual_overlays) - known_overlays)
    for overlay in unknown_manual:
        warnings.append(f"Ignored unknown manual overlay: {overlay}")

    preset_results = [rule["result"] for rule in matrix.get("preset_rules", []) if "result" in rule]
    skipped_modules = [
        {
            "module": _block_id_for_preset(preset),
            "reason": f"Skipped because primary_preset = {primary_preset}",
        }
        for preset in dict.fromkeys(preset_results)
        if preset != primary_preset
    ]
    skipped_modules.extend(inactive_overlays)

    fallbacks: list[str] = []
    if warnings:
        fallbacks.append("missing_or_unknown_input_review_required")
    if preset_assumption_required:
        fallbacks.append("preset_assumption_required")

    return {
        "ok": True,
        "input_mode": input_mode,
        "answers": normalized_answers,
        "pending_questions": pending_questions,
        "classifiers": normalized_classifiers,
        "signals": signals,
        "primary_preset": primary_preset,
        "preset_rationale": preset_rationale,
        "active_overlays": active_overlays,
        "depth_profile": depth_profile,
        "blueprint_profile": _resolve_blueprint_profile(matrix, context),
        "skipped_modules": skipped_modules,
        "decision_trace": decision_trace,
        "warnings": warnings,
        "fallbacks": fallbacks,
    }


def _extract_input(payload: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        raise RoutingError("Input JSON must be an object.")
    if "answers" in payload:
        answers = payload["answers"]
        if not isinstance(answers, dict):
            raise RoutingError("The answers payload must be an object.")
        return "answers", answers
    if "classifiers" in payload:
        classifiers = payload["classifiers"]
        if not isinstance(classifiers, dict):
            raise RoutingError("The classifiers payload must be an object.")
        return "classifiers", classifiers
    return "classifiers", payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve Planroot/PIF routing from interview answers or classifiers.")
    parser.add_argument(
        "--matrix",
        default=str(DEFAULT_MATRIX_PATH),
        help="Path to PIF_Decision_Matrix.json.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON file containing answers, classifiers, or an object with answers/classifiers.",
    )
    parser.add_argument(
        "--manual-overlay",
        action="append",
        default=[],
        help="Force-enable an overlay when a human-approved condition exists outside deterministic answers.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of indented JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        matrix = load_json(Path(args.matrix))
        payload = load_json(Path(args.input))
        input_mode, input_data = _extract_input(payload)
        result = resolve_routing(input_data, matrix, args.manual_overlay, input_mode=input_mode)
    except (OSError, json.JSONDecodeError, RoutingError) as error:
        print(json.dumps({"ok": False, "errors": [str(error)]}, ensure_ascii=False), file=sys.stderr)
        return 2

    indent = None if args.compact else 2
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
