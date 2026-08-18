#!/usr/bin/env python
"""Instala os git hooks do projeto.

    python3 tools/install_hooks.py

O diretorio .git/hooks nao e versionado, entao os hooks vivem em
tools/hooks/ e sao copiados por aqui. Precisa rodar uma vez por clone.
"""

from __future__ import annotations

import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "hooks"
TARGET = ROOT / ".git" / "hooks"


def main() -> int:
    if not TARGET.is_dir():
        print(f"ERRO: {TARGET} nao existe -- este e um repositorio git?", file=sys.stderr)
        return 1

    installed = []
    for hook in sorted(SOURCE.iterdir()):
        if not hook.is_file():
            continue
        dest = TARGET / hook.name
        if dest.exists() and dest.read_bytes() != hook.read_bytes():
            backup = dest.with_suffix(".backup")
            shutil.copy2(dest, backup)
            print(f"  hook existente salvo em {backup.name}")
        shutil.copy2(hook, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(hook.name)

    if not installed:
        print("Nenhum hook encontrado em tools/hooks/.")
        return 0

    print("Hooks instalados: " + ", ".join(installed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
