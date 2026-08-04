#!/usr/bin/env python
"""Testes da camada de respostas estruturadas (`app/pif_answers.py`).

A garantia central esta em `test_routing_is_unaffected`: normalizar respostas
nao pode mudar o que o roteador ve. Enquanto isso valer, a Fase 1 nao consegue
alterar preset, overlays nem profundidade.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_answers import (  # noqa: E402
    SOURCE_DEFERRED,
    SOURCE_EXPLICIT,
    SOURCE_LEGACY,
    answer_details,
    answer_source,
    detail_text,
    is_answered,
    legacy_option_id,
    normalize_answer,
    normalize_answers,
    to_legacy_answers,
)
from tools.pif_flow_fixtures import FIXTURES  # noqa: E402
from tools.pif_router import resolve_routing  # noqa: E402


class CheckFailed(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


def check_equal(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise CheckFailed(f"{message}: esperado {expected!r}, obtido {actual!r}")


# --------------------------------------------------------------------------- #
# Formatos de entrada
# --------------------------------------------------------------------------- #
def test_legacy_string() -> None:
    answer = normalize_answer("deadline", "fixed_business_date")
    check_equal(answer["option"], "fixed_business_date", "opcao legada")
    check_equal(answer["details"], {}, "legado nao tem detalhes")
    check_equal(answer["source"], SOURCE_LEGACY, "origem legada")


def test_structured() -> None:
    answer = normalize_answer(
        "deadline",
        {
            "option": "fixed_business_date",
            "details": {"date": "2026-10-15", "reason": "lancamento comercial"},
            "source": "explicit",
        },
    )
    check_equal(answer["option"], "fixed_business_date", "opcao estruturada")
    check_equal(answer["details"]["date"], "2026-10-15", "detalhe de data")
    check_equal(answer["source"], SOURCE_EXPLICIT, "origem explicita")


def test_label_is_accepted() -> None:
    """O roteador ja aceita rotulo no lugar do id; a normalizacao tambem deve."""
    answer = normalize_answer("deadline", "Tenho uma data fixa de negocio")
    from app.pif_question_bank import QUESTION_INDEX

    label = QUESTION_INDEX["deadline"]["options"][2]["label"]
    resolved = normalize_answer("deadline", label)
    check(resolved is not None, "rotulo real deve resolver")
    check_equal(
        resolved["option"],
        QUESTION_INDEX["deadline"]["options"][2]["id"],
        "rotulo -> id",
    )
    # Um rotulo inventado nao vira id valido: fica intacto para o roteador acusar.
    check(answer is None or answer["option"] == "Tenho uma data fixa de negocio", "rotulo invalido preservado")


def test_invalid_option_is_preserved() -> None:
    """Opcao invalida nao pode ser engolida -- o roteador precisa acusar."""
    answer = normalize_answer("deadline", "opcao_que_nao_existe")
    check_equal(answer["option"], "opcao_que_nao_existe", "opcao invalida preservada")

    routing = resolve_routing({"deadline": answer["option"]}, input_mode="answers")
    check(not routing.get("ok"), "roteador deve rejeitar opcao invalida")


def test_empty_answers_vanish() -> None:
    for empty in (None, "", {}):
        check_equal(normalize_answer("deadline", empty), None, f"vazio {empty!r} -> None")

    normalized = normalize_answers({"deadline": "", "sponsor": "single_sponsor"})
    check_equal(sorted(normalized), ["sponsor"], "entradas vazias descartadas")


def test_deferred() -> None:
    """'Ainda nao sei' existe, nao resolve a decisao e nao vira pendencia falsa."""
    answer = normalize_answer("deadline", {"option": None, "source": "deferred"})
    check_equal(answer["option"], None, "adiada nao tem opcao")
    check_equal(answer["source"], SOURCE_DEFERRED, "origem adiada")
    check(not is_answered(answer), "adiada nao conta como respondida")
    check_equal(to_legacy_answers({"deadline": answer}), {}, "adiada nao chega ao roteador")


def test_details_are_cleaned() -> None:
    answer = normalize_answer(
        "project_name",
        {
            "option": "approved_name",
            "details": {
                "name": "  Planroot  ",
                "vazio": "   ",
                "": "sem chave",
                "contagem": 3,
                "alternativas": ["Raiz", "  ", "Plan"],
                "objeto": {"nao": "suportado"},
            },
        },
    )
    details = answer["details"]
    check_equal(details["name"], "Planroot", "texto e aparado")
    check("vazio" not in details, "valor em branco descartado")
    check("" not in details, "chave vazia descartada")
    check_equal(details["contagem"], 3, "numero preservado")
    check_equal(details["alternativas"], ["Raiz", "Plan"], "lista filtrada")
    check("objeto" not in details, "valor aninhado descartado")


def test_accessors() -> None:
    answer = normalize_answer(
        "project_name",
        {"option": "approved_name", "details": {"name": "Planroot"}, "source": "explicit"},
    )
    check_equal(legacy_option_id(answer), "approved_name", "legacy_option_id")
    check_equal(answer_details(answer)["name"], "Planroot", "answer_details")
    check_equal(answer_source(answer), SOURCE_EXPLICIT, "answer_source")
    check_equal(answer_source("approved_name"), SOURCE_LEGACY, "string crua e legada")
    check_equal(
        detail_text({"project_name": answer}, "project_name", "name"),
        "Planroot",
        "detail_text encontra a chave",
    )
    check_equal(
        detail_text({"project_name": answer}, "project_name", "ausente"),
        None,
        "detail_text sem a chave",
    )


def test_mixed_format() -> None:
    """Legado e estruturado convivendo no mesmo conjunto."""
    normalized = normalize_answers(
        {
            "deadline": "fixed_business_date",
            "project_name": {"option": "approved_name", "details": {"name": "Planroot"}},
        }
    )
    check_equal(normalized["deadline"]["source"], SOURCE_LEGACY, "misto: parte legada")
    check_equal(normalized["project_name"]["source"], SOURCE_EXPLICIT, "misto: parte estruturada")
    check_equal(
        to_legacy_answers(normalized),
        {"deadline": "fixed_business_date", "project_name": "approved_name"},
        "misto reduz ao formato do roteador",
    )


# --------------------------------------------------------------------------- #
# Garantia central
# --------------------------------------------------------------------------- #
def test_routing_is_unaffected() -> None:
    """Para as 13 fixtures, normalizar nao pode mexer no roteamento."""
    for fixture in FIXTURES:
        legacy_answers = fixture.answers()
        normalized = normalize_answers(legacy_answers)
        rebuilt = to_legacy_answers(normalized)

        check_equal(rebuilt, legacy_answers, f"{fixture.id}: ida e volta preserva as respostas")

        before = resolve_routing(legacy_answers, input_mode="answers")
        after = resolve_routing(rebuilt, input_mode="answers")

        for key in ("primary_preset", "depth_profile", "signals", "classifiers"):
            check_equal(after.get(key), before.get(key), f"{fixture.id}: {key} preservado")
        check_equal(
            sorted(after.get("active_overlays", [])),
            sorted(before.get("active_overlays", [])),
            f"{fixture.id}: overlays preservados",
        )


def test_structured_details_do_not_change_routing() -> None:
    """Acrescentar detalhes concretos nao pode mover uma unica decisao."""
    fixture = FIXTURES[1]  # ferramenta local offline
    plain = fixture.answers()

    enriched: dict[str, Any] = dict(plain)
    enriched["project_name"] = {
        "option": plain["project_name"],
        "details": {"name": "Conciliador de Planilhas"},
        "source": "explicit",
    }
    enriched["deadline"] = {
        "option": plain["deadline"],
        "details": {"date": "2026-10-15", "reason": "fim do trimestre"},
        "source": "explicit",
    }

    before = resolve_routing(plain, input_mode="answers")
    after = resolve_routing(to_legacy_answers(normalize_answers(enriched)), input_mode="answers")

    check_equal(after.get("primary_preset"), before.get("primary_preset"), "preset preservado")
    check_equal(after.get("signals"), before.get("signals"), "sinais preservados")
    check_equal(
        sorted(after.get("active_overlays", [])),
        sorted(before.get("active_overlays", [])),
        "overlays preservados",
    )


# --------------------------------------------------------------------------- #
# Efeito nos renderizadores
# --------------------------------------------------------------------------- #
def _render(answers: dict[str, Any]) -> tuple[str, str, str]:
    from app.pif_blueprint import render_ai_prompt, render_blueprint, render_minimal_blueprint

    routing = resolve_routing(to_legacy_answers(answers), input_mode="answers")
    return (
        render_blueprint(answers, routing),
        render_minimal_blueprint(answers, routing),
        render_ai_prompt(answers, routing),
    )


def test_real_project_name_is_rendered() -> None:
    answers: dict[str, Any] = dict(FIXTURES[1].answers())
    answers["project_name"] = {
        "option": "approved_name",
        "details": {"name": "Conciliador de Planilhas"},
        "source": "explicit",
    }
    full, minimal, ai_prompt = _render(answers)

    check("- Projeto: Conciliador de Planilhas" in full, "blueprint traz o nome real")
    check("- Projeto: Conciliador de Planilhas" in minimal, "blueprint minimo traz o nome real")
    check("Nome do projeto: Conciliador de Planilhas." in ai_prompt, "prompt traz o nome real")


def test_option_label_is_never_used_as_the_name() -> None:
    """O defeito original: o rotulo da opcao virava o nome do projeto."""
    answers = dict(FIXTURES[1].answers())  # legado, sem detalhes
    full, minimal, ai_prompt = _render(answers)

    label = "Já tenho o nome final, decidido"
    check(f"- Projeto: {label}" not in full, "blueprint nao usa o rotulo como nome")
    check(f"- Projeto: {label}" not in minimal, "minimo nao usa o rotulo como nome")
    check(f"Nome do projeto: {label}" not in ai_prompt, "prompt nao usa o rotulo como nome")

    # A situacao do nome continua registrada, no campo certo.
    check(f"- Situação do nome: {label}" in full, "a situacao do nome e preservada")
    check(f"Sobre o nome do projeto: {label}." in ai_prompt, "prompt descreve a situacao do nome")


def test_details_reach_the_blueprint() -> None:
    answers: dict[str, Any] = dict(FIXTURES[1].answers())
    # Condicoes da Fase 3: `deadline` exige prazo real, `base_integrations` exige
    # que exista alguma integracao. Sem abrir as duas, nada seria renderizado.
    answers["urgency"] = "fixed_deadline"
    answers["integration_intensity"] = "few"
    answers["deadline"] = {
        "option": "fixed_business_date",
        "details": {"date": "2026-10-15", "reason": "fim do trimestre"},
        "source": "explicit",
    }
    answers["base_integrations"] = {
        "option": "few_base_integrations",
        "details": {"sistemas": ["Bling", "Conta Azul"]},
        "source": "explicit",
    }
    full, _, ai_prompt = _render(answers)

    check("date: 2026-10-15" in full, "data concreta no blueprint")
    check("reason: fim do trimestre" in full, "motivo concreto no blueprint")
    check("sistemas: Bling, Conta Azul" in full, "lista concreta no blueprint")
    check("date: 2026-10-15" in ai_prompt, "detalhe concreto chega ao prompt")


def test_deferred_answer_stays_pending_in_render() -> None:
    answers: dict[str, Any] = dict(FIXTURES[1].answers())
    answers["scope_target"] = "full_version"  # habilita o anexo "Para versao completa"
    answers["urgency"] = "fixed_deadline"     # abre a condicao de `deadline`
    answers["deadline"] = {"option": None, "source": "deferred"}

    full, _, _ = _render(answers)

    check("- **Prazo**: [PENDENTE]" in full, "adiada aparece como pendente")
    check("- deadline: Prazo" in full, "adiada continua listada como decisao a tomar")


TESTS: list[Callable[[], None]] = [
    test_legacy_string,
    test_structured,
    test_label_is_accepted,
    test_invalid_option_is_preserved,
    test_empty_answers_vanish,
    test_deferred,
    test_details_are_cleaned,
    test_accessors,
    test_mixed_format,
    test_routing_is_unaffected,
    test_structured_details_do_not_change_routing,
    test_real_project_name_is_rendered,
    test_option_label_is_never_used_as_the_name,
    test_details_reach_the_blueprint,
    test_deferred_answer_stays_pending_in_render,
]


def main() -> int:
    failures: list[tuple[str, str]] = []

    for test in TESTS:
        name = test.__name__
        try:
            test()
        except CheckFailed as error:
            failures.append((name, str(error)))
            print(f"FAIL {name}")
            print(f"  - {error}")
        else:
            print(f"PASS {name}")

    print()
    print(f"Testes: {len(TESTS)} | Passaram: {len(TESTS) - len(failures)} | Falharam: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
