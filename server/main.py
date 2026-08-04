"""Planroot site backend (FastAPI).

Serves the static single-page frontend and the /api surface that drives the
deterministic PIF interview, generates the blueprint, and gates the .md/.json
download behind an Asaas Pix payment.

Run:  cd server && uvicorn main:app --reload
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE_DIR = ROOT / "site"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import payments_asaas as pay  # noqa: E402
import pif_service  # noqa: E402
import store  # noqa: E402
from exporters import build_json, build_md, build_prompt  # noqa: E402

app = FastAPI(title="Planroot PIF", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    store.init_db()


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class SessionCreate(BaseModel):
    brief: str = ""


class AnswersPayload(BaseModel):
    answers: dict[str, Any] = {}


class BlueprintPayload(BaseModel):
    session_id: str
    answers: dict[str, Any] = {}


class CheckoutPayload(BaseModel):
    session_id: str
    name: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[str] = None


# --------------------------------------------------------------------------- #
# Interview API
# --------------------------------------------------------------------------- #
@app.post("/api/session")
def create_session(payload: SessionCreate) -> dict[str, Any]:
    session_id = store.create_session(brief=payload.brief.strip())
    return {"session_id": session_id, "phase1_question_ids": pif_service.phase1_question_ids()}


@app.get("/api/questions")
def get_questions() -> dict[str, Any]:
    return {
        "questions": pif_service.serialize_questions(),
        "phase1_question_ids": pif_service.phase1_question_ids(),
        "gate": pif_service.AMBIGUITY_GATE,
    }


@app.post("/api/route")
def route(payload: AnswersPayload) -> dict[str, Any]:
    summary = pif_service.route_summary(payload.answers)
    summary.pop("_routing", None)  # internal-only
    return summary


@app.post("/api/blueprint")
def blueprint(payload: BlueprintPayload) -> dict[str, Any]:
    session = store.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    summary = pif_service.route_summary(payload.answers)
    routing = summary.pop("_routing")
    if not routing.get("ok"):
        raise HTTPException(status_code=400, detail={"errors": routing.get("errors", [])})

    ambiguity = summary["ambiguity_reduction"]
    if ambiguity < pif_service.AMBIGUITY_GATE:
        raise HTTPException(
            status_code=409,
            detail={
                "reason": "ambiguity_gate_not_met",
                "ambiguity_reduction": ambiguity,
                "gate": pif_service.AMBIGUITY_GATE,
                "pending_questions": summary.get("pending_questions", []),
            },
        )

    brief = session.get("brief") or ""
    md = build_md(payload.answers, routing)
    json_doc = build_json(payload.answers, routing, brief=brief)
    prompt_doc = build_prompt(payload.answers, routing, brief=brief)
    store.update_session(
        payload.session_id,
        answers=payload.answers,
        routing=routing,
        md=md,
        json_doc=json_doc,
        prompt_doc=prompt_doc,
    )

    return {
        "ambiguity_reduction": ambiguity,
        "primary_preset": routing.get("primary_preset"),
        "active_overlays": routing.get("active_overlays", []),
        "depth_profile": routing.get("depth_profile"),
        "section_count": len(json_doc["sections"]),
        "pending_questions": routing.get("pending_questions", []),
        "price": pay.PRICE,
    }


# --------------------------------------------------------------------------- #
# Payment API (Asaas Pix)
# --------------------------------------------------------------------------- #
@app.post("/api/checkout")
def checkout(payload: CheckoutPayload) -> dict[str, Any]:
    session = store.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if not session.get("md"):
        raise HTTPException(status_code=409, detail="Blueprint ainda não foi gerado.")
    if session.get("paid"):
        return {"already_paid": True}

    try:
        charge = pay.create_pix_charge(
            payload.session_id,
            {"name": payload.name, "cpf": payload.cpf, "email": payload.email},
        )
    except Exception as exc:  # noqa: BLE001 - surface gateway errors cleanly to the UI
        raise HTTPException(status_code=502, detail=f"Falha ao criar cobrança Asaas: {exc}")

    store.update_session(payload.session_id, charge_id=charge["charge_id"])
    return {
        "charge_id": charge["charge_id"],
        "qr_base64": charge["qr_base64"],
        "copia_cola": charge["copia_cola"],
        "value": charge["value"],
        "mock": charge.get("mock", False),
    }


@app.get("/api/payment/{session_id}")
def payment_status(session_id: str) -> dict[str, Any]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if session.get("paid"):
        return {"paid": True, "status": "CONFIRMED"}

    charge_id = session.get("charge_id")
    if not charge_id:
        return {"paid": False, "status": "NO_CHARGE"}

    status = pay.get_payment_status(charge_id)
    if status.get("paid"):
        store.update_session(session_id, paid=True)
    return status


@app.post("/api/webhook/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: Optional[str] = Header(default=None),
) -> JSONResponse:
    if not pay.verify_webhook_token(asaas_access_token):
        raise HTTPException(status_code=401, detail="Webhook token inválido.")

    event = await request.json()
    if pay.event_is_paid(event):
        charge_id = (event.get("payment") or {}).get("id")
        external_ref = (event.get("payment") or {}).get("externalReference")
        session_id = None
        if charge_id:
            session_id = store.mark_paid_by_charge(charge_id)
        if not session_id and external_ref:
            store.update_session(external_ref, paid=True)
            session_id = external_ref
        return JSONResponse({"ok": True, "session_id": session_id})
    return JSONResponse({"ok": True, "ignored": event.get("event")})


@app.post("/api/dev/simulate-payment/{session_id}")
def simulate_payment(session_id: str) -> dict[str, Any]:
    """Dev-only: flips a session to paid (use only in mock/sandbox testing)."""
    if not pay.is_mock():
        raise HTTPException(status_code=403, detail="Disponível apenas em ASAAS_MODE=mock.")
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    store.update_session(session_id, paid=True)
    return {"paid": True}


# --------------------------------------------------------------------------- #
# Gated downloads
# --------------------------------------------------------------------------- #
def _require_paid(session_id: str) -> dict[str, Any]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if not session.get("paid"):
        raise HTTPException(status_code=403, detail="Pagamento não confirmado.")
    if not session.get("md"):
        raise HTTPException(status_code=409, detail="Blueprint indisponível.")
    return session


# Declarado ANTES de .md para o sufixo mais especifico casar primeiro.
@app.get("/api/download/{session_id}.prompt.md")
def download_prompt(session_id: str) -> Response:
    session = _require_paid(session_id)
    prompt_doc = session.get("prompt_doc")
    if not prompt_doc:
        raise HTTPException(status_code=409, detail="Prompt para IA indisponível.")
    return Response(
        content=prompt_doc,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=planroot-prompt-ia.md"},
    )


@app.get("/api/download/{session_id}.md")
def download_md(session_id: str) -> Response:
    session = _require_paid(session_id)
    return Response(
        content=session["md"],
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=planroot-blueprint.md"},
    )


@app.get("/api/download/{session_id}.json")
def download_json(session_id: str) -> Response:
    session = _require_paid(session_id)
    return Response(
        content=json.dumps(session["json_doc"], ensure_ascii=False, indent=2),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=planroot-blueprint.json"},
    )


# --------------------------------------------------------------------------- #
# Static frontend (mounted last so /api routes win)
# --------------------------------------------------------------------------- #
if SITE_DIR.exists():
    app.mount("/", StaticFiles(directory=str(SITE_DIR), html=True), name="site")
