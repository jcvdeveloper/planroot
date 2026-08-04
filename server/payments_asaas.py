"""Asaas Pix integration.

Configuration via environment variables:
  ASAAS_API_KEY        Asaas access token (server-side only; never sent to the browser).
  ASAAS_BASE_URL       https://sandbox.asaas.com/api/v3 (default) or https://api.asaas.com/v3
  ASAAS_WEBHOOK_TOKEN  Shared secret expected on the asaas-access-token webhook header.
  ASAAS_DEFAULT_CPF    Fallback CPF used to create the payer customer (sandbox testing).
  ASAAS_MODE           "live" (default) or "mock" — mock returns a fake QR so the full
                       flow (gating, polling, download) can be exercised without keys.

Public API:
  create_pix_charge(session_id, payer) -> {charge_id, qr_base64, copia_cola, value}
  get_payment_status(charge_id)        -> {"paid": bool, "status": str}
  verify_webhook_token(token)          -> bool
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

PRICE = float(os.getenv("PLANROOT_PRICE", "20.00"))
_DEFAULT_BASE = "https://sandbox.asaas.com/api/v3"

_PAID_STATUSES = {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}


def _cfg() -> dict[str, str]:
    return {
        "api_key": os.getenv("ASAAS_API_KEY", ""),
        "base_url": os.getenv("ASAAS_BASE_URL", _DEFAULT_BASE).rstrip("/"),
        "webhook_token": os.getenv("ASAAS_WEBHOOK_TOKEN", ""),
        "default_cpf": os.getenv("ASAAS_DEFAULT_CPF", "24971563792"),  # Asaas sandbox test CPF
        "mode": os.getenv("ASAAS_MODE", "live").lower(),
    }


def is_mock() -> bool:
    cfg = _cfg()
    return cfg["mode"] == "mock" or not cfg["api_key"]


def _client(cfg: dict[str, str]) -> httpx.Client:
    return httpx.Client(
        base_url=cfg["base_url"],
        headers={"access_token": cfg["api_key"], "Content-Type": "application/json"},
        timeout=20.0,
    )


def _ensure_customer(client: httpx.Client, payer: dict[str, Any], cfg: dict[str, str]) -> str:
    body = {
        "name": payer.get("name") or "Cliente Planroot",
        "cpfCnpj": (payer.get("cpf") or cfg["default_cpf"]).replace(".", "").replace("-", ""),
    }
    if payer.get("email"):
        body["email"] = payer["email"]
    resp = client.post("/customers", json=body)
    resp.raise_for_status()
    return resp.json()["id"]


def create_pix_charge(session_id: str, payer: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Create a dynamic Pix charge of PRICE tied to `session_id` via externalReference."""
    payer = payer or {}

    if is_mock():
        # 1x1 transparent PNG stand-in so the UI can render an <img>.
        fake_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return {
            "charge_id": f"mock_{session_id[:12]}",
            "qr_base64": fake_png,
            "copia_cola": f"00020126MOCK-PIX-{session_id[:8]}5204000053039865406{PRICE:.2f}6304ABCD",
            "value": PRICE,
            "mock": True,
        }

    cfg = _cfg()
    with _client(cfg) as client:
        customer_id = _ensure_customer(client, payer, cfg)
        charge_resp = client.post(
            "/payments",
            json={
                "customer": customer_id,
                "billingType": "PIX",
                "value": PRICE,
                "dueDate": _today(),
                "description": "Planroot — Blueprint do Iniciador de Projeto (PIF)",
                "externalReference": session_id,
            },
        )
        charge_resp.raise_for_status()
        charge = charge_resp.json()
        charge_id = charge["id"]

        qr_resp = client.get(f"/payments/{charge_id}/pixQrCode")
        qr_resp.raise_for_status()
        qr = qr_resp.json()

    return {
        "charge_id": charge_id,
        "qr_base64": qr.get("encodedImage"),
        "copia_cola": qr.get("payload"),
        "value": PRICE,
        "mock": False,
    }


def get_payment_status(charge_id: str) -> dict[str, Any]:
    if is_mock() or charge_id.startswith("mock_"):
        # Mock charges are only flipped to paid via the simulate endpoint / webhook.
        return {"paid": False, "status": "PENDING", "mock": True}

    cfg = _cfg()
    with _client(cfg) as client:
        resp = client.get(f"/payments/{charge_id}")
        resp.raise_for_status()
        status = resp.json().get("status", "UNKNOWN")
    return {"paid": status in _PAID_STATUSES, "status": status}


def verify_webhook_token(token: Optional[str]) -> bool:
    cfg = _cfg()
    expected = cfg["webhook_token"]
    if not expected:
        # No token configured -> accept (useful in sandbox); log-worthy in production.
        return True
    return token == expected


def event_is_paid(event: dict[str, Any]) -> bool:
    return event.get("event") in {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"}


def _today() -> str:
    from datetime import date

    return date.today().isoformat()
