#!/usr/bin/env python
"""Testes da camada de decisoes e do resolver central (`app/pif_decisions.py`).

Cobre o que a Fase 2 promete: fonte unica de verdade, substituicao declarada,
condicoes deterministicas, pendencias so da rota ativa e progresso medido por
decisao resolvida.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_blueprint import plan_sections, render_blueprint  # noqa: E402
from app.pif_decisions import (  # noqa: E402
    DECISION_BY_QUESTION,
    DECISION_INDEX,
    DECISIONS,
    SUPERSEDES,
    resolve_interview_plan,
    route_question_ids,
)
from app.pif_question_bank import QUESTION_INDEX, QUESTIONS  # noqa: E402
from tools.pif_flow_fixtures import FIXTURES, FIXTURES_BY_ID  # noqa: E402
from tools.pif_router import resolve_routing  # noqa: E402


class CheckFailed(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


def check_equal(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise CheckFailed(f"{message}: esperado {expected!r}, obtido {actual!r}")


def _section_lines(markdown: str, heading: str) -> list[str]:
    """Linhas de uma secao, sem invadir a proxima."""
    marcador = f"## {heading}"
    if marcador not in markdown:
        return []
    resto = markdown[markdown.index(marcador) + len(marcador):]
    linhas: list[str] = []
    for linha in resto.splitlines():
        if linha.startswith("## "):
            break
        linhas.append(linha)
    return linhas


def _plan(fixture_id: str, overrides: dict[str, Any] | None = None):
    answers = dict(FIXTURES_BY_ID[fixture_id].answers())
    answers.update(overrides or {})
    routing = resolve_routing(
        {k: (v if isinstance(v, str) else v.get("option")) for k, v in answers.items() if v},
        input_mode="answers",
    )
    return answers, routing, resolve_interview_plan(answers, routing)


# --------------------------------------------------------------------------- #
# Catalogo
# --------------------------------------------------------------------------- #
def test_every_question_maps_to_a_decision() -> None:
    """Uma pergunta sem decisao nao pode ser avaliada nem substituida."""
    sem_decisao = [q["id"] for q in QUESTIONS if q["id"] not in DECISION_BY_QUESTION]
    # Perguntas de preset/overlay entram na Fase 3; por ora exige-se o nucleo.
    nucleo_sem_decisao = [
        qid for qid in sem_decisao
        if QUESTION_INDEX[qid]["block_type"] in ("core_always", "classifier")
    ]
    check_equal(nucleo_sem_decisao, [], "toda pergunta de nucleo tem decisao")


def test_decision_keys_are_known() -> None:
    desconhecidas = sorted({k for k in DECISION_BY_QUESTION.values() if k not in DECISION_INDEX})
    check_equal(desconhecidas, [], "toda decision_key referenciada existe no catalogo")


def test_supersedes_points_to_real_questions() -> None:
    for especializada, genericas in SUPERSEDES.items():
        check(especializada in QUESTION_INDEX, f"especializada inexistente: {especializada}")
        for generica in genericas:
            check(generica in QUESTION_INDEX, f"generica inexistente: {generica}")
            check(
                generica != especializada,
                f"{especializada} nao pode substituir a si mesma",
            )
            check(
                DECISION_BY_QUESTION.get(especializada) == DECISION_BY_QUESTION.get(generica),
                f"{especializada} substitui {generica} mas resolvem decisoes diferentes",
            )


# --------------------------------------------------------------------------- #
# Fonte unica
# --------------------------------------------------------------------------- #
def test_plan_matches_route_when_unconditioned() -> None:
    """Sem condicoes nem substituicoes aplicaveis, o plano e a rota."""
    for fixture in FIXTURES:
        answers, routing, plan = _plan(fixture.id)
        esperado = [
            qid for qid in route_question_ids(routing)
            if qid not in plan.skipped
        ]
        check_equal(plan.active_question_ids, esperado, f"{fixture.id}: plano == rota ativa")


def test_inactive_routes_never_appear() -> None:
    for fixture in FIXTURES:
        _, routing, plan = _plan(fixture.id)
        preset_ativo = f"preset_{routing.get('primary_preset')}"
        overlays_ativos = {f"overlay_{o}" for o in routing.get("active_overlays", [])}

        for qid in plan.active_question_ids:
            bloco = QUESTION_INDEX[qid]["block"]
            tipo = QUESTION_INDEX[qid]["block_type"]
            if tipo == "preset_block":
                check_equal(bloco, preset_ativo, f"{fixture.id}: preset inativo em {qid}")
            elif tipo == "overlay_block":
                check(bloco in overlays_ativos, f"{fixture.id}: overlay inativo em {qid} ({bloco})")


def test_sections_come_from_the_plan() -> None:
    """O blueprint nao pode renderizar pergunta que saiu do fluxo."""
    for fixture in FIXTURES:
        answers, routing, plan = _plan(fixture.id)
        ativos = set(plan.active_question_ids)
        for section in plan_sections(routing, answers):
            for qid in section.question_ids:
                check(qid in ativos, f"{fixture.id}: {qid} renderizado fora do plano")


# --------------------------------------------------------------------------- #
# Pendencias (defeito 3.3 dos documentos)
# --------------------------------------------------------------------------- #
def test_full_version_annex_lists_only_active_route() -> None:
    answers, routing, plan = _plan("full_version_annex")
    md = render_blueprint(answers, routing)
    check("## Para versão completa" in md, "anexo deve existir com scope_target=full_version")

    listados = [
        linha[2:].split(":")[0]
        for linha in _section_lines(md, "Para versão completa")
        if linha.startswith("- ")
    ]
    check(len(listados) > 0, "anexo nao pode estar vazio quando ha pendencias")

    preset_ativo = f"preset_{routing.get('primary_preset')}"
    overlays_ativos = {f"overlay_{o}" for o in routing.get("active_overlays", [])}
    for qid in listados:
        bloco_q = QUESTION_INDEX[qid]["block"]
        tipo = QUESTION_INDEX[qid]["block_type"]
        if tipo == "preset_block":
            check_equal(bloco_q, preset_ativo, f"anexo lista preset inativo: {qid}")
        elif tipo == "overlay_block":
            check(bloco_q in overlays_ativos, f"anexo lista overlay inativo: {qid} ({bloco_q})")

    check_equal(
        sorted(listados),
        sorted(q for q in plan.pending_question_ids if q != "scope_target"),
        "anexo == pendencias do plano",
    )


def test_interview_pendings_section_ignores_inactive_routes() -> None:
    """`routing["pending_questions"]` varre o banco inteiro; o render nao pode.

    Defeito encontrado ao rodar o fluxo real: com tudo respondido, a secao
    "Pendencias da entrevista" listava 44 perguntas de presets e overlays que
    aquele projeto nunca teria.
    """
    answers, routing, plan = _plan("local_offline_tool")
    # completa preset e overlays ativos -> nao deve sobrar pendencia alguma
    preset_ativo = f"preset_{routing['primary_preset']}"
    overlays_ativos = {f"overlay_{o}" for o in routing["active_overlays"]}
    for question in QUESTIONS:
        if question["block"] == preset_ativo or question["block"] in overlays_ativos:
            answers.setdefault(question["id"], question["options"][0]["id"])

    global_pendings = routing.get("pending_questions", [])
    check(len(global_pendings) > 20, "o roteador deve mesmo reportar pendencia global grande")

    md = render_blueprint(answers, routing, pending_questions=global_pendings)
    check(
        "## Pendências da entrevista" not in md,
        "sem pendencia na rota ativa, a secao nao deve existir",
    )

    # E quando ha pendencia real, ela aparece -- e so ela.
    # `sponsor` nao participa de nenhuma substituicao, entao sai do fluxo apenas
    # por nao ter resposta, que e exatamente o caso a testar.
    answers.pop("sponsor", None)
    md2 = render_blueprint(answers, routing)  # caminho de producao: pendencia vem do plano
    listadas = [
        linha for linha in _section_lines(md2, "Pendências da entrevista")
        if linha.startswith("- ")
    ]
    check_equal(len(listadas), 1, "apenas a pendencia real da rota ativa")
    check("sponsor" in listadas[0], "a pendencia listada e a que existe de fato")


def test_pending_excludes_answered() -> None:
    for fixture in FIXTURES:
        answers, _, plan = _plan(fixture.id)
        respondidas = {qid for qid, value in answers.items() if value}
        vazamento = [qid for qid in plan.pending_question_ids if qid in respondidas]
        check_equal(vazamento, [], f"{fixture.id}: pendencia inclui pergunta respondida")


# --------------------------------------------------------------------------- #
# Condicoes e substituicao
# --------------------------------------------------------------------------- #
def test_skip_when_removes_question() -> None:
    """Condicao declarada tira a pergunta do fluxo, com motivo registrado."""
    original = QUESTION_INDEX["approvers"].get("skip_when")
    try:
        QUESTION_INDEX["approvers"]["skip_when"] = {"sponsor": "single_sponsor"}
        _, _, plan = _plan("local_offline_tool")
        check("approvers" not in plan.active_question_ids, "skip_when deve remover a pergunta")
        check_equal(plan.skipped.get("approvers"), "skip_when satisfeito", "motivo registrado")
    finally:
        QUESTION_INDEX["approvers"]["skip_when"] = original


def test_ask_when_keeps_question_out_until_condition_holds() -> None:
    original = QUESTION_INDEX["deadline"].get("ask_when")
    try:
        QUESTION_INDEX["deadline"]["ask_when"] = {"urgency": "fixed_deadline"}
        _, _, plan = _plan("local_offline_tool")  # urgency = planned_window
        check("deadline" not in plan.active_question_ids, "ask_when nao satisfeito remove a pergunta")

        _, _, plan2 = _plan("local_offline_tool", {"urgency": "fixed_deadline"})
        check("deadline" in plan2.active_question_ids, "ask_when satisfeito traz a pergunta de volta")
    finally:
        QUESTION_INDEX["deadline"]["ask_when"] = original


def test_supersedes_removes_generic_only_when_specialized_answered() -> None:
    SUPERSEDES["local_update"] = ["update_strategy"]
    # `update_strategy` so entra no fluxo quando a operacao e critica (Fase 3);
    # sem isso nao ha generica para substituir e o teste nao testaria nada.
    #
    # Desde a consolidacao dos classificadores, criticidade nao e mais um campo
    # auto-declarado: vem de `delivery_type = critical_system` ou de `ops_need`.
    # Usa-se aqui o risco operacional (ops_need 2) porque ele satisfaz o gate
    # sem trocar o preset da fixture, que e o que o teste isola.
    critica = {"main_risks": "operational_risk"}
    try:
        # especializada NAO respondida -> generica permanece
        _, _, plan = _plan("local_offline_tool", critica)
        check(
            "update_strategy" in plan.active_question_ids,
            "generica permanece enquanto a especializada nao foi respondida",
        )

        # especializada respondida -> generica sai, com motivo
        _, _, plan2 = _plan("local_offline_tool", {**critica, "local_update": "manual_replace"})
        check(
            "update_strategy" not in plan2.active_question_ids,
            "generica sai quando a especializada e respondida",
        )
        check_equal(
            plan2.skipped.get("update_strategy"),
            "substituida por local_update",
            "motivo da substituicao registrado",
        )
    finally:
        SUPERSEDES.pop("local_update", None)


# --------------------------------------------------------------------------- #
# Progresso
# --------------------------------------------------------------------------- #
def test_progress_is_weighted_by_decision() -> None:
    vazio = resolve_interview_plan({}, {"primary_preset": None, "active_overlays": []})
    check_equal(vazio.progress, 0.0, "sem resposta, progresso zero")
    check_equal(vazio.resolved_decisions, {}, "sem resposta, nada resolvido")

    # Só é exigida a decisão que a rota ativa consegue resolver. Uma decisão sem
    # pergunta ativa não é pendência -- contá-la travaria o progresso abaixo de
    # 100% para sempre numa rota enxuta.
    alcancaveis = {
        DECISION_BY_QUESTION[qid]
        for qid in vazio.active_question_ids
        if qid in DECISION_BY_QUESTION
    }
    check_equal(
        sorted(vazio.unresolved_decision_keys),
        sorted(alcancaveis),
        "pendencia == decisoes alcancaveis pela rota ativa",
    )
    check(
        set(vazio.unresolved_decision_keys) <= {d.key for d in DECISIONS},
        "toda pendencia pertence ao catalogo",
    )

    _, _, cheio = _plan("local_offline_tool")
    check(cheio.progress > 90, f"fixture completa deve ter progresso alto, obtido {cheio.progress}")


def test_progress_uses_weights_not_question_count() -> None:
    """Escopo (peso 3) precisa mover mais o progresso que Auditoria (peso 1)."""
    base = {"delivery_type": "internal_tool", "runtime": "cloud"}
    routing = resolve_routing(base, input_mode="answers")

    com_escopo = resolve_interview_plan({**base, "mvp_scope": "tight_scope"}, routing)
    com_auditoria = resolve_interview_plan({**base, "minimal_audit": "light_history"}, routing)

    check(
        com_escopo.progress > com_auditoria.progress,
        f"escopo (peso 3) deve pesar mais que auditoria (peso 1): "
        f"{com_escopo.progress} vs {com_auditoria.progress}",
    )


TESTS: list[Callable[[], None]] = [
    test_every_question_maps_to_a_decision,
    test_decision_keys_are_known,
    test_supersedes_points_to_real_questions,
    test_plan_matches_route_when_unconditioned,
    test_inactive_routes_never_appear,
    test_sections_come_from_the_plan,
    test_full_version_annex_lists_only_active_route,
    test_interview_pendings_section_ignores_inactive_routes,
    test_pending_excludes_answered,
    test_skip_when_removes_question,
    test_ask_when_keeps_question_out_until_condition_holds,
    test_supersedes_removes_generic_only_when_specialized_answered,
    test_progress_is_weighted_by_decision,
    test_progress_uses_weights_not_question_count,
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
