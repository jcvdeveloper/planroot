"""Adapter over the existing deterministic PIF engine.

Reuses (does not reimplement):
  - app.pif_question_bank : QUESTIONS / QUESTION_INDEX / OPTION_INDEX
  - tools.pif_router       : resolve_routing
  - app.pif_blueprint      : plan_sections (for the active-path / sections)

Adds three site-specific concerns:
  - serializing the question bank for the browser wizard;
  - splitting questions into phase 1 (always asked, drives routing) and
    phase 2 (the adaptive Motor Final + chosen preset + active overlays);
  - a deterministic "ambiguity reduction" meter (target >= 90%).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_answers import is_answered, legacy_option_id, to_legacy_answers  # noqa: E402
from app.pif_decisions import resolve_interview_plan  # noqa: E402
from app.pif_question_bank import OPTION_INDEX, QUESTION_INDEX, QUESTIONS  # noqa: E402
from tools.pif_router import resolve_routing  # noqa: E402

# Questions asked before routing. They cover the mandatory core of the Motor
# Inicial plus every classifier; together they let the router pick a preset.
PHASE1_BLOCK_TYPES = ("classifier",)
PHASE1_PHASES = ("Motor Inicial", "Classificadores")

AMBIGUITY_GATE = 90.0
_HIGH_RISK_PENALTY = 0.02   # per high-ambiguity answer (clarity_risk >= 2)
_PENALTY_CAP = 0.15


def serialize_questions() -> list[dict[str, Any]]:
    """Browser-friendly view of the bank: ids, prompts and option labels only."""
    out: list[dict[str, Any]] = []
    for q in QUESTIONS:
        out.append(
            {
                "id": q["id"],
                "phase": q["phase"],
                "block": q["block"],
                "block_type": q["block_type"],
                "title": q["title"],
                "prompt": q["prompt"],
                "detail_hint": q.get("detail_hint"),
                "detail_schema": q.get("detail_schema"),
                "options": [
                    {"id": opt["id"], "label": opt["label"]} for opt in q["options"]
                ],
            }
        )
    return out


def phase1_question_ids() -> list[str]:
    return [q["id"] for q in QUESTIONS if q["phase"] in PHASE1_PHASES]


def route(answers: dict[str, Any]) -> dict[str, Any]:
    """Run the deterministic router over partial/complete answers.

    Aceita tanto o formato legado (`{"deadline": "fixed_business_date"}`) quanto
    o estruturado (`{"deadline": {"option": ..., "details": ...}}`). O roteador
    continua vendo apenas ids de opcao -- detalhes nunca influenciam a rota.
    """
    return resolve_routing(to_legacy_answers(answers), input_mode="answers")


def active_path_question_ids(routing: dict[str, Any], answers: dict[str, Any] | None = None) -> list[str]:
    """Perguntas que ainda fazem parte da rota, segundo o resolver central.

    Delega a `resolve_interview_plan` -- nenhum consumidor deve reconstruir o
    caminho ativo por conta propria.
    """
    return resolve_interview_plan(answers or {}, routing).active_question_ids


def next_question_ids(routing: dict[str, Any], answers: dict[str, Any] | None = None) -> list[str]:
    """Phase 2: active-path questions that were NOT already asked in phase 1."""
    asked = set(phase1_question_ids())
    return [qid for qid in active_path_question_ids(routing, answers) if qid not in asked]


def compute_ambiguity(answers: dict[str, Any], routing: dict[str, Any]) -> float:
    """Deterministic ambiguity-reduction score in [0, 100].

    Base = fraction of active-path questions answered.
    Penalty = small deduction for each answer that itself carries high
    clarity_risk (the option pushes clarity_risk >= 2), capped.
    """
    path = active_path_question_ids(routing, answers)
    total = len(path)
    if total == 0:
        return 0.0

    answered = [qid for qid in path if is_answered(answers.get(qid))]
    base = len(answered) / total

    high_risk = 0
    for qid in answered:
        opt = OPTION_INDEX.get(qid, {}).get(legacy_option_id(answers[qid]))
        if opt and int(opt.get("signals", {}).get("clarity_risk", 0)) >= 2:
            high_risk += 1
    penalty = min(_PENALTY_CAP, high_risk * _HIGH_RISK_PENALTY)

    return round(max(0.0, base - penalty) * 100, 1)


def route_summary(answers: dict[str, Any]) -> dict[str, Any]:
    """Routing + the wizard-facing extras (next questions + ambiguity)."""
    routing = route(answers)
    ambiguity = compute_ambiguity(answers, routing) if routing.get("ok") else 0.0
    plan = resolve_interview_plan(answers, routing) if routing.get("ok") else None
    return {
        "decision_progress": plan.progress if plan else 0.0,
        "unresolved_decisions": plan.unresolved_decision_keys if plan else [],
        # Sequencia completa que o wizard deve exibir. E o mesmo plano que
        # governa blueprint e pendencias -- a UI nao monta caminho por conta.
        "active_question_ids": plan.active_question_ids if plan else [],
        "ok": routing.get("ok", False),
        "primary_preset": routing.get("primary_preset"),
        "active_overlays": routing.get("active_overlays", []),
        "depth_profile": routing.get("depth_profile"),
        "pending_questions": routing.get("pending_questions", []),
        "next_question_ids": next_question_ids(routing, answers) if routing.get("ok") else [],
        "ambiguity_reduction": ambiguity,
        "gate": AMBIGUITY_GATE,
        "errors": routing.get("errors", []),
        "warnings": routing.get("warnings", []),
        "_routing": routing,
    }
