#!/usr/bin/env python
"""Simula o fluxo cortado e prova que ele nao muda o roteamento (Fase 3).

O risco central da reducao: se uma pergunta deixa de ser feita, os sinais dela
somem e preset, overlays ou profundidade podem mudar sem ninguem perceber.

Aqui a entrevista e simulada de verdade. Partindo das respostas da fixture, o
plano e recalculado ate o ponto fixo -- a cada rodada so permanecem as respostas
das perguntas que o fluxo realmente exibiria. O roteamento resultante e
comparado com o do fluxo completo.

    python tools/pif_simulate_flow.py            # falha se alguma rota divergir
    python tools/pif_simulate_flow.py --report   # tabela de perguntas por rota

Divergencia aqui significa: o corte quebrou o roteamento. Nao ha excecao
aceitavel sem registro em PIF_Migration_Table.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "server")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pif_service  # noqa: E402
from app.pif_decisions import resolve_interview_plan, route_question_ids  # noqa: E402
from app.pif_question_bank import QUESTION_INDEX  # noqa: E402
from pif_flow_fixtures import FIXTURES, Fixture  # noqa: E402
from pif_snapshot_flow import DEPTH_TARGETS  # noqa: E402

MAX_ROUNDS = 12


def simulate(fixture: Fixture) -> dict[str, Any]:
    """Roda a entrevista cortada ate o ponto fixo.

    Devolve o roteamento completo, o roteamento cortado e as perguntas exibidas.
    """
    full_answers = fixture.answers()
    routing_full = pif_service.route(full_answers)

    shown: list[str] = []
    answers = dict(full_answers)
    routing = routing_full
    rounds = 0

    for rounds in range(1, MAX_ROUNDS + 1):
        plan = resolve_interview_plan(answers, routing)
        shown = plan.active_question_ids
        # O usuario so responde o que o fluxo exibe.
        restricted = {qid: full_answers[qid] for qid in shown if qid in full_answers}
        new_routing = pif_service.route(restricted)

        stable = (
            new_routing.get("primary_preset") == routing.get("primary_preset")
            and new_routing.get("depth_profile") == routing.get("depth_profile")
            and sorted(new_routing.get("active_overlays", []))
            == sorted(routing.get("active_overlays", []))
            and restricted.keys() == answers.keys()
        )
        answers, routing = restricted, new_routing
        if stable:
            break

    return {
        "id": fixture.id,
        "label": fixture.label,
        "rounds": rounds,
        "converged": rounds < MAX_ROUNDS,
        "shown": shown,
        "shown_count": len(shown),
        "routing_full": routing_full,
        "routing_cut": routing,
        # Caminho sem nenhuma condicao aplicada: a linha de base do "antes".
        "full_path_count": len(route_question_ids(routing_full)),
        # Piso estrutural: classificadores + preset + overlays ativos. Mesmo
        # zerando o nucleo, o fluxo nao desce abaixo disto.
        "floor": len(
            [
                qid
                for qid in route_question_ids(routing_full)
                if QUESTION_INDEX[qid]["block_type"] != "core_always"
            ]
        ),
    }


def _routing_diff(full: dict[str, Any], cut: dict[str, Any]) -> list[str]:
    diffs: list[str] = []
    for key in ("primary_preset", "depth_profile"):
        if full.get(key) != cut.get(key):
            diffs.append(f"{key}: {full.get(key)!r} -> {cut.get(key)!r}")
    lost = sorted(set(full.get("active_overlays", [])) - set(cut.get("active_overlays", [])))
    gained = sorted(set(cut.get("active_overlays", [])) - set(full.get("active_overlays", [])))
    if lost:
        diffs.append(f"overlays perdidos: {lost}")
    if gained:
        diffs.append(f"overlays surgidos: {gained}")
    return diffs


def check() -> int:
    failures = 0
    for fixture in FIXTURES:
        result = simulate(fixture)
        problems = _routing_diff(result["routing_full"], result["routing_cut"])
        if not result["converged"]:
            problems.append(f"nao convergiu em {MAX_ROUNDS} rodadas")

        if problems:
            failures += 1
            print(f"FAIL {fixture.id}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"PASS {fixture.id}  ({result['shown_count']} perguntas exibidas)")

    print()
    print(f"Rotas: {len(FIXTURES)} | Estaveis: {len(FIXTURES) - failures} | Quebradas: {failures}")
    if failures:
        print()
        print("O corte alterou o roteamento. Transfira os sinais da pergunta removida")
        print("ou reveja a condicao antes de prosseguir.")
    return 1 if failures else 0


def report() -> int:
    header = (
        f"{'rota':<22} {'depth':<9} {'antes':>6} {'depois':>7} {'piso':>5} "
        f"{'meta':>5} {'status':>16}"
    )
    print(header)
    print("-" * len(header))

    acima = 0
    piso_acima_da_meta = 0
    total_antes = total_depois = 0
    for fixture in FIXTURES:
        result = simulate(fixture)
        depth = result["routing_cut"].get("depth_profile") or "-"
        alvo = DEPTH_TARGETS.get(depth)
        dentro = alvo is not None and result["shown_count"] <= alvo
        piso_impede = alvo is not None and result["floor"] > alvo
        if alvo is not None and not dentro:
            acima += 1
        if piso_impede:
            piso_acima_da_meta += 1
        total_antes += result["full_path_count"]
        total_depois += result["shown_count"]

        status = "ok" if dentro else ("ACIMA (piso)" if piso_impede else "ACIMA")
        print(
            f"{fixture.id:<22} {depth:<9} {result['full_path_count']:>6} "
            f"{result['shown_count']:>7} {result['floor']:>5} {str(alvo or '-'):>5} {status:>16}"
        )

    print("-" * len(header))
    print(f"{'TOTAL':<22} {'':<9} {total_antes:>6} {total_depois:>7}")
    print()
    print(f"Rotas acima da meta: {acima}/{len(FIXTURES)}")
    if piso_acima_da_meta:
        print(
            f"Rotas cujo PISO ja excede a meta: {piso_acima_da_meta}/{len(FIXTURES)} "
            "-- nenhuma condicao adicional resolve; exige consolidar perguntas."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simula o fluxo cortado do PIF.")
    parser.add_argument("--report", action="store_true", help="Tabela de perguntas por rota.")
    args = parser.parse_args(argv)
    return report() if args.report else check()


if __name__ == "__main__":
    raise SystemExit(main())
