#!/usr/bin/env python
"""Validate deterministic question bank structure."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_question_bank import QUESTIONS  # noqa: E402


BANNED_LABELS = {
    "Já está definido",
    "Precisa ser descoberto",
    "Existe parcialmente",
    "Ainda não sei / precisa validar",
    "Não entra no MVP",
}


def validate() -> list[str]:
    errors: list[str] = []
    seen_question_ids: set[str] = set()

    for question in QUESTIONS:
        question_id = question["id"]
        if question_id in seen_question_ids:
            errors.append(f"Duplicate question id: {question_id}")
        seen_question_ids.add(question_id)

        options = question.get("options", [])
        if not 3 <= len(options) <= 5:
            errors.append(f"{question_id}: expected 3-5 options, found {len(options)}")

        seen_option_ids: set[str] = set()
        for option in options:
            option_id = option.get("id")
            label = option.get("label")
            if option_id in seen_option_ids:
                errors.append(f"{question_id}: duplicate option id {option_id}")
            seen_option_ids.add(option_id)

            if label in BANNED_LABELS:
                errors.append(f"{question_id}: banned generic label {label!r}")

            if not option.get("signals") and option.get("classifier_value") is None:
                errors.append(f"{question_id}: option {option_id} must contribute signals or classifier_value")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Question bank validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Question bank validation passed: {len(QUESTIONS)} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
