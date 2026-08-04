"""Camada de respostas estruturadas do PIF.

Hoje uma resposta e apenas o id da opcao escolhida (`dict[str, str]`). Isso
guarda a decisao mas perde tudo que a torna concreta: o nome real do projeto, a
data do prazo, o sistema que precisa ser integrado, quem responde pela operacao.

Este modulo introduz a forma canonica sem quebrar nada:

    {"option": "fixed_business_date",
     "details": {"date": "2026-10-15", "reason": "lancamento comercial"},
     "source": "explicit"}

O formato antigo continua valido na entrada. `to_legacy_answers()` devolve o
`dict[str, str]` que `resolve_routing` ja consome, de modo que a camada de
roteamento permanece intocada -- e o snapshot de fluxo, verde.

Uma resposta com `option = None` e `source = "deferred"` representa um
"ainda nao sei": ela existe, nao bloqueia o progresso, e continua pendente para
o roteador. Nada e inventado.
"""

from __future__ import annotations

from typing import Any

from app.pif_question_bank import OPTION_INDEX, QUESTION_INDEX

# Procedencia de uma resposta. Ordem = precedencia (a primeira vence).
SOURCE_EXPLICIT = "explicit"
SOURCE_DERIVED = "derived"
SOURCE_PRESET_DEFAULT = "preset_default"
SOURCE_LEGACY = "legacy"
SOURCE_MIGRATION = "migration"
SOURCE_INFERRED_FROM_BRIEF = "inferred_from_brief"
SOURCE_DEFERRED = "deferred"

VALID_SOURCES = frozenset(
    {
        SOURCE_EXPLICIT,
        SOURCE_DERIVED,
        SOURCE_PRESET_DEFAULT,
        SOURCE_LEGACY,
        SOURCE_MIGRATION,
        SOURCE_INFERRED_FROM_BRIEF,
        SOURCE_DEFERRED,
    }
)

# Fontes que o usuario ainda nao confirmou explicitamente.
UNCONFIRMED_SOURCES = frozenset({SOURCE_INFERRED_FROM_BRIEF, SOURCE_DEFERRED})

_SCALAR_TYPES = (str, int, float, bool)


def _clean_details(raw: Any) -> dict[str, Any]:
    """Mantem apenas pares utilizaveis. Nunca inventa conteudo."""
    if not isinstance(raw, dict):
        return {}

    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            continue
        key = key.strip()

        if isinstance(value, str):
            value = value.strip()
            if value:
                cleaned[key] = value
        elif isinstance(value, bool) or isinstance(value, (int, float)):
            cleaned[key] = value
        elif isinstance(value, list):
            items = [item.strip() if isinstance(item, str) else item for item in value]
            items = [item for item in items if isinstance(item, _SCALAR_TYPES) and item != ""]
            if items:
                cleaned[key] = items

    return cleaned


def _resolve_option_id(question_id: str, raw_option: Any) -> str | None:
    """Aceita id da opcao ou o rotulo visivel, como o roteador ja faz.

    Um valor desconhecido e devolvido intacto: quem reporta erro de opcao
    invalida e o roteador, e ele deve continuar reportando.
    """
    if raw_option in (None, ""):
        return None

    option_id = str(raw_option).strip()
    if not option_id:
        return None

    if question_id in OPTION_INDEX and option_id in OPTION_INDEX[question_id]:
        return option_id

    question = QUESTION_INDEX.get(question_id)
    if question:
        for option in question["options"]:
            if option["label"] == option_id:
                return option["id"]

    return option_id


def normalize_answer(question_id: str, raw_answer: Any) -> dict[str, Any] | None:
    """Converte qualquer formato aceito na forma canonica.

    Devolve None quando nao ha resposta alguma -- diferente de uma resposta
    adiada, que existe e carrega `source = "deferred"`.
    """
    if raw_answer in (None, ""):
        return None

    if isinstance(raw_answer, dict):
        option_id = _resolve_option_id(question_id, raw_answer.get("option"))
        details = _clean_details(raw_answer.get("details"))
        raw_source = raw_answer.get("source")
        source = raw_source if raw_source in VALID_SOURCES else None

        # Sem opcao e sem detalhe, so e resposta se o adiamento foi declarado.
        # Um payload vazio e ausencia de resposta, nao um "ainda nao sei".
        if option_id is None and not details and source != SOURCE_DEFERRED:
            return None

        if source is None:
            source = SOURCE_DEFERRED if option_id is None else SOURCE_EXPLICIT
        return {"option": option_id, "details": details, "source": source}

    option_id = _resolve_option_id(question_id, raw_answer)
    if option_id is None:
        return None
    return {"option": option_id, "details": {}, "source": SOURCE_LEGACY}


def normalize_answers(raw_answers: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Normaliza um conjunto inteiro, descartando entradas vazias."""
    if not raw_answers:
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for question_id, raw_answer in raw_answers.items():
        answer = normalize_answer(question_id, raw_answer)
        if answer is not None:
            normalized[question_id] = answer
    return normalized


def legacy_option_id(normalized_answer: Any) -> str | None:
    """Id da opcao, no formato que o roteador consome."""
    if isinstance(normalized_answer, dict):
        return normalized_answer.get("option")
    if normalized_answer in (None, ""):
        return None
    return str(normalized_answer)


def answer_details(normalized_answer: Any) -> dict[str, Any]:
    if isinstance(normalized_answer, dict):
        return normalized_answer.get("details") or {}
    return {}


def answer_source(normalized_answer: Any) -> str:
    if isinstance(normalized_answer, dict):
        return normalized_answer.get("source") or SOURCE_EXPLICIT
    if normalized_answer in (None, ""):
        return SOURCE_DEFERRED
    return SOURCE_LEGACY


def is_answered(normalized_answer: Any) -> bool:
    """Uma decisao so esta resolvida quando ha opcao escolhida."""
    return legacy_option_id(normalized_answer) is not None


def to_legacy_answers(answers: dict[str, Any] | None) -> dict[str, str]:
    """Reduz para `dict[str, str]` -- a entrada de `resolve_routing`.

    Respostas adiadas somem daqui de proposito: para o roteador elas continuam
    sendo pendencias, exatamente como uma pergunta nunca exibida.
    """
    legacy: dict[str, str] = {}
    for question_id, raw_answer in (answers or {}).items():
        option_id = legacy_option_id(
            raw_answer if isinstance(raw_answer, dict) else normalize_answer(question_id, raw_answer)
        )
        if option_id is not None:
            legacy[question_id] = option_id
    return legacy


def detail_text(answers: dict[str, Any] | None, question_id: str, *keys: str) -> str | None:
    """Primeiro detalhe textual nao vazio entre `keys`.

    Usado pelos renderizadores para preferir o dado concreto do cliente ao
    rotulo generico da opcao.
    """
    details = answer_details((answers or {}).get(question_id))
    for key in keys:
        value = details.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
