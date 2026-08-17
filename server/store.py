"""Session store backed by SQLite (stdlib only).

Holds one row per interview session: the free-form brief, the collected answers,
the resolved routing, the generated .md/.json artifacts, and the payment state.
The download endpoints read `paid` from here before releasing any file.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Configuravel para que o deploy possa apontar o banco para um disco
# persistente sem mudar codigo. Sem a variavel, cai no comportamento local.
DB_PATH = Path(os.getenv("PLANROOT_DB_PATH") or Path(__file__).resolve().parent / "planroot.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    brief       TEXT,
    answers     TEXT NOT NULL DEFAULT '{}',
    routing     TEXT,
    md          TEXT,
    json_doc    TEXT,
    prompt_doc  TEXT,
    charge_id   TEXT,
    paid        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    # PLANROOT_DB_PATH pode apontar para um volume cujo diretorio ainda nao
    # existe; sqlite3.connect nao cria o caminho sozinho.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        # Migracao defensiva: CREATE TABLE IF NOT EXISTS nao adiciona colunas novas
        # a um banco ja existente. Adiciona prompt_doc se faltar.
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN prompt_doc TEXT")
        except sqlite3.OperationalError:
            pass  # coluna ja existe


def create_session(brief: str = "") -> str:
    session_id = uuid.uuid4().hex
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, brief, answers, paid, created_at, updated_at) "
            "VALUES (?, ?, '{}', 0, ?, ?)",
            (session_id, brief, now, now),
        )
    return session_id


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "brief": row["brief"],
        "answers": json.loads(row["answers"] or "{}"),
        "routing": json.loads(row["routing"]) if row["routing"] else None,
        "md": row["md"],
        "json_doc": json.loads(row["json_doc"]) if row["json_doc"] else None,
        "prompt_doc": row["prompt_doc"],
        "charge_id": row["charge_id"],
        "paid": bool(row["paid"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_session(session_id: str, **fields: Any) -> None:
    """Update a subset of columns. JSON-serializable fields are encoded automatically."""
    if not fields:
        return
    json_columns = {"answers", "routing", "json_doc"}
    sets: list[str] = []
    values: list[Any] = []
    for key, value in fields.items():
        if key in json_columns and not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        if key == "paid":
            value = 1 if value else 0
        sets.append(f"{key} = ?")
        values.append(value)
    sets.append("updated_at = ?")
    values.append(_now())
    values.append(session_id)
    with _connect() as conn:
        conn.execute(f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", values)


def mark_paid_by_charge(charge_id: str) -> Optional[str]:
    """Flip `paid` for the session that owns this Asaas charge. Returns the session id."""
    with _connect() as conn:
        row = conn.execute("SELECT id FROM sessions WHERE charge_id = ?", (charge_id,)).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE sessions SET paid = 1, updated_at = ? WHERE charge_id = ?",
            (_now(), charge_id),
        )
        return row["id"]
