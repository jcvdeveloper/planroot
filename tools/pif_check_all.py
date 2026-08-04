#!/usr/bin/env python
"""Gate de regressao: roda todas as verificacoes do PIF em um comando.

    python tools/pif_check_all.py

Sai com 1 se qualquer verificacao falhar. E o que deve rodar antes de declarar
qualquer fase concluida.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

CHECKS: list[tuple[str, list[str]]] = [
    ("banco de perguntas", [sys.executable, str(TOOLS / "pif_validate_question_bank.py")]),
    ("respostas estruturadas", [sys.executable, str(TOOLS / "pif_test_answers.py")]),
    ("decisoes e resolver", [sys.executable, str(TOOLS / "pif_test_decisions.py")]),
    ("roteamento", [sys.executable, str(TOOLS / "pif_test_routing.py")]),
    ("blueprint", [sys.executable, str(TOOLS / "pif_test_blueprint.py")]),
    ("prompt para IA", [sys.executable, str(TOOLS / "pif_test_prompt.py")]),
    ("estabilidade do corte", [sys.executable, str(TOOLS / "pif_simulate_flow.py")]),
    ("snapshot do fluxo", [sys.executable, str(TOOLS / "pif_snapshot_flow.py")]),
]


def main() -> int:
    failures: list[str] = []

    for name, command in CHECKS:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"PASS  {name}")
            continue

        failures.append(name)
        print(f"FAIL  {name}")
        for line in (result.stdout + result.stderr).splitlines():
            print(f"      {line}")

    print()
    print(f"Verificacoes: {len(CHECKS)} | Passaram: {len(CHECKS) - len(failures)} | Falharam: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
