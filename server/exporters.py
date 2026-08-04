"""Blueprint exporters: Markdown (reuses render_blueprint) and structured JSON."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_answers import answer_details, answer_source, legacy_option_id  # noqa: E402
from app.pif_blueprint import plan_sections, render_ai_prompt, render_blueprint  # noqa: E402
from app.pif_question_bank import OPTION_INDEX, QUESTION_INDEX  # noqa: E402


def build_md(answers: dict[str, Any], routing: dict[str, Any]) -> str:
    """Authoritative Markdown blueprint (identical to the CLI renderer)."""
    return render_blueprint(
        answers,
        routing,
        pending_questions=routing.get("pending_questions", []),
    )


def build_prompt(answers: dict[str, Any], routing: dict[str, Any], brief: str = "") -> str:
    """Copy-paste-ready 'Prompt para IA' (beginner-facing, no raw signals)."""
    return render_ai_prompt(answers, routing, brief=brief or None)


def _selected_label(question_id: str, option_id: str) -> str:
    opt = OPTION_INDEX.get(question_id, {}).get(option_id)
    return opt["label"] if opt else option_id


def build_json(answers: dict[str, Any], routing: dict[str, Any], brief: str = "") -> dict[str, Any]:
    """Machine-readable blueprint: routing + answered sections + pendings."""
    project_answer = answers.get("project_name")
    project_option = legacy_option_id(project_answer)
    project_details = answer_details(project_answer)
    project_name = project_details.get("name") or project_details.get("nome")

    sections: list[dict[str, Any]] = []
    for section in plan_sections(routing, answers):
        items = []
        for qid in section.question_ids:
            option_id = legacy_option_id(answers.get(qid))
            items.append(
                {
                    "question_id": qid,
                    "title": QUESTION_INDEX[qid]["title"],
                    "answer_id": option_id,
                    "answer_label": _selected_label(qid, option_id) if option_id else None,
                    "answer_details": answer_details(answers.get(qid)) or None,
                    "answer_source": answer_source(answers.get(qid)) if option_id else None,
                    "pending": option_id is None,
                }
            )
        sections.append(
            {
                "block_id": section.block_id,
                "block_type": section.block_type,
                "title": section.title,
                "items": items,
            }
        )

    return {
        "schema": "planroot.blueprint/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": project_name,
        "project_name_status": _selected_label("project_name", project_option) if project_option else None,
        "brief": brief or None,
        "routing": {
            "primary_preset": routing.get("primary_preset"),
            "active_overlays": routing.get("active_overlays", []),
            "depth_profile": routing.get("depth_profile"),
            "blueprint_profile": routing.get("blueprint_profile", {}),
            "preset_rationale": routing.get("preset_rationale"),
        },
        "classifiers": routing.get("classifiers", {}),
        "signals": routing.get("signals", {}),
        "answers": answers,
        "sections": sections,
        "pending_questions": routing.get("pending_questions", []),
    }
