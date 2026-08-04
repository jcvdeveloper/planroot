#!/usr/bin/env python
"""Congela o comportamento do fluxo PIF e detecta regressao (Fase 0).

Para cada fixture de `pif_flow_fixtures`, percorre o caminho real do produto --
`answers` -> `resolve_routing` -> caminho ativo -> `plan_sections` -> renderizadores
-- e grava um retrato determinístico em `PIF_Flow_Snapshot.json`.

Uso:
    python tools/pif_snapshot_flow.py --update    # grava o snapshot
    python tools/pif_snapshot_flow.py             # compara e falha se divergir
    python tools/pif_snapshot_flow.py --report    # imprime a tabela de contagem

O snapshot guarda a lista completa de ids do caminho ativo (diff legivel) e o
hash dos renderizadores (detecta drift de texto sem inchar o arquivo). Toda
divergencia precisa ser justificada na tabela de migracao antes de o snapshot
ser regravado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "server")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pif_service  # noqa: E402  (server/pif_service.py)
from app.pif_blueprint import (  # noqa: E402
    plan_sections,
    render_ai_prompt,
    render_blueprint,
    render_minimal_blueprint,
)
from pif_flow_fixtures import FIXTURES, Fixture  # noqa: E402

SNAPSHOT_PATH = ROOT / "PIF_Flow_Snapshot.json"

# Metas de perguntas visiveis por perfil de profundidade (criterio de aceite).
DEPTH_TARGETS = {"lite": 16, "standard": 24, "strict": 32}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def snapshot_fixture(fixture: Fixture) -> dict[str, Any]:
    """Retrato determinístico de uma rota, ponta a ponta."""
    answers = fixture.answers()
    routing = pif_service.route(answers)

    active_path = pif_service.active_path_question_ids(routing)
    phase1 = pif_service.phase1_question_ids()
    ambiguity = pif_service.compute_ambiguity(answers, routing)

    # Quantas perguntas do caminho ativo o cliente precisa responder para o gate.
    gate_fraction = pif_service.AMBIGUITY_GATE / 100.0
    answers_for_gate = -(-int(len(active_path) * gate_fraction * 100) // 100)

    sections = [
        {
            "block_id": section.block_id,
            "block_type": section.block_type,
            "question_count": len(section.question_ids),
        }
        for section in plan_sections(routing)
    ]

    blueprint = render_blueprint(
        answers, routing, pending_questions=routing.get("pending_questions", [])
    )
    minimal = render_minimal_blueprint(answers, routing)
    ai_prompt = render_ai_prompt(answers, routing, brief=f"Fixture {fixture.id}")

    return {
        "id": fixture.id,
        "label": fixture.label,
        "routing": {
            "ok": routing.get("ok"),
            "primary_preset": routing.get("primary_preset"),
            "depth_profile": routing.get("depth_profile"),
            "active_overlays": sorted(routing.get("active_overlays", [])),
            "blueprint_profile": routing.get("blueprint_profile", {}),
            "fallbacks": sorted(routing.get("fallbacks", [])),
        },
        "classifiers": routing.get("classifiers", {}),
        "signals": routing.get("signals", {}),
        "flow": {
            "phase1_count": len(phase1),
            "active_path_count": len(active_path),
            "answers_needed_for_gate": answers_for_gate,
            "ambiguity_with_fixture_answers": ambiguity,
            "active_path_ids": active_path,
        },
        "sections": sections,
        "renders": {
            "blueprint_sha": _sha(blueprint),
            "blueprint_lines": blueprint.count("\n"),
            "minimal_sha": _sha(minimal),
            "minimal_lines": minimal.count("\n"),
            "ai_prompt_sha": _sha(ai_prompt),
            "ai_prompt_lines": ai_prompt.count("\n"),
        },
    }


def build_snapshot() -> dict[str, Any]:
    fixtures = [snapshot_fixture(fixture) for fixture in FIXTURES]
    return {
        "schema": "planroot.flow_snapshot/v1",
        "ambiguity_gate": pif_service.AMBIGUITY_GATE,
        "depth_targets": DEPTH_TARGETS,
        "fixtures": fixtures,
    }


# --------------------------------------------------------------------------- #
# Comparacao
# --------------------------------------------------------------------------- #
def _diff(expected: Any, actual: Any, path: str = "") -> list[str]:
    """Diferencas legiveis entre dois documentos JSON."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        out: list[str] = []
        for key in sorted(set(expected) | set(actual)):
            child = f"{path}.{key}" if path else key
            if key not in expected:
                out.append(f"{child}: campo novo ({actual[key]!r})")
            elif key not in actual:
                out.append(f"{child}: campo removido (era {expected[key]!r})")
            else:
                out.extend(_diff(expected[key], actual[key], child))
        return out

    if isinstance(expected, list) and isinstance(actual, list):
        if all(isinstance(item, str) for item in expected + actual):
            removed = [item for item in expected if item not in actual]
            added = [item for item in actual if item not in expected]
            out = []
            if removed:
                out.append(f"{path}: removidos {removed}")
            if added:
                out.append(f"{path}: adicionados {added}")
            if not out and expected != actual:
                out.append(f"{path}: ordem mudou")
            return out
        if len(expected) != len(actual):
            return [f"{path}: tamanho {len(expected)} -> {len(actual)}"]
        out = []
        for index, (exp_item, act_item) in enumerate(zip(expected, actual)):
            out.extend(_diff(exp_item, act_item, f"{path}[{index}]"))
        return out

    if expected != actual:
        return [f"{path}: {expected!r} -> {actual!r}"]
    return []


def compare(snapshot_path: Path) -> int:
    if not snapshot_path.exists():
        print(f"ERRO: snapshot ausente em {snapshot_path}.", file=sys.stderr)
        print("Rode com --update para grava-lo antes de refatorar.", file=sys.stderr)
        return 2

    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    actual = build_snapshot()

    expected_by_id = {item["id"]: item for item in expected.get("fixtures", [])}
    actual_by_id = {item["id"]: item for item in actual["fixtures"]}

    failures = 0
    for fixture_id in sorted(set(expected_by_id) | set(actual_by_id)):
        if fixture_id not in expected_by_id:
            print(f"NOVA {fixture_id} (ausente no snapshot)")
            failures += 1
            continue
        if fixture_id not in actual_by_id:
            print(f"SUMIU {fixture_id} (presente no snapshot)")
            failures += 1
            continue

        differences = _diff(expected_by_id[fixture_id], actual_by_id[fixture_id], fixture_id)
        if differences:
            failures += 1
            print(f"DIVERGE {fixture_id}")
            for difference in differences:
                print(f"  - {difference}")
        else:
            print(f"OK      {fixture_id}")

    for key in ("ambiguity_gate", "depth_targets"):
        if expected.get(key) != actual.get(key):
            failures += 1
            print(f"DIVERGE {key}: {expected.get(key)!r} -> {actual.get(key)!r}")

    total = len(actual["fixtures"])
    print()
    print(f"Fixtures: {total} | Iguais: {total - failures} | Divergentes: {failures}")
    if failures:
        print()
        print("Toda divergencia precisa constar da tabela de migracao antes de")
        print("regravar o snapshot com --update.")
    return 1 if failures else 0


def report() -> int:
    """Tabela de contagem por rota -- o antes/depois do criterio de aceite."""
    snapshot = build_snapshot()
    header = f"{'fixture':<20} {'preset':<28} {'depth':<9} {'ovl':>4} {'caminho':>8} {'gate':>6} {'meta':>6} {'status':>8}"
    print(header)
    print("-" * len(header))

    over_target = 0
    for item in snapshot["fixtures"]:
        routing = item["routing"]
        flow = item["flow"]
        depth = routing["depth_profile"] or "-"
        target = DEPTH_TARGETS.get(depth)
        within = target is not None and flow["active_path_count"] <= target
        if target is not None and not within:
            over_target += 1
        print(
            f"{item['id']:<20} {str(routing['primary_preset']):<28} {depth:<9} "
            f"{len(routing['active_overlays']):>4} {flow['active_path_count']:>8} "
            f"{flow['answers_needed_for_gate']:>6} {str(target or '-'):>6} "
            f"{('ok' if within else 'ACIMA'):>8}"
        )

    print()
    print(f"Rotas acima da meta: {over_target}/{len(snapshot['fixtures'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot de regressao do fluxo PIF.")
    parser.add_argument("--update", action="store_true", help="Grava o snapshot atual.")
    parser.add_argument("--report", action="store_true", help="Imprime a tabela de contagem por rota.")
    parser.add_argument("--snapshot", default=str(SNAPSHOT_PATH), help="Caminho do snapshot.")
    args = parser.parse_args(argv)

    if args.report:
        return report()

    snapshot_path = Path(args.snapshot)
    if args.update:
        snapshot = build_snapshot()
        snapshot_path.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Snapshot gravado: {snapshot_path} ({len(snapshot['fixtures'])} fixtures)")
        return 0

    return compare(snapshot_path)


if __name__ == "__main__":
    raise SystemExit(main())
