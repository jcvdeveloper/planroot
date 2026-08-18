#!/usr/bin/env python
"""Carimba cada asset do site/index.html com o hash do proprio conteudo.

    python tools/bump_assets_version.py            # reescreve o index.html
    python tools/bump_assets_version.py --check    # so verifica, sai 1 se desatualizado

Por que existe
--------------
O host serve os estaticos sem `Cache-Control` -- so com `ETag` e
`Last-Modified`. Sem `Cache-Control` o navegador aplica a heuristica de
frescor do HTTP e decide sozinho por quanto tempo guarda CADA arquivo, e o
visitante acaba com uma mistura de versoes: HTML novo com JS velho, por
exemplo. Foi o que derrubou o site em producao (a pagina abria so com o
fundo, porque os textos entram todos por copy.js).

Versionar pela URL resolve: `app.js?v=a1b2c3d4` e, para o navegador, um
recurso diferente de `app.js?v=0e9f8a7b` -- ele nao tem como servir a copia
velha.

Por que o hash do conteudo, e nao a data
----------------------------------------
Timestamp invalidaria tudo a cada deploy, jogando fora cache que ainda era
bom. Com o hash do arquivo, um asset que nao mudou mantem a mesma URL e
segue em cache; so o que realmente mudou e rebuscado. Cada asset tem o seu,
entao mexer no CSS nao invalida o JS.

Nao toca no backend: le e escreve apenas dentro de site/.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
INDEX = SITE / "index.html"

# Casa src/href de qualquer asset sob /assets/, com ou sem ?v= previo.
ASSET_RE = re.compile(r'((?:src|href)=")(/assets/[^"?]+)(\?v=[^"]*)?(")')

HASH_LEN = 8


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_LEN]


def stamp(html: str) -> tuple[str, list[str], list[str]]:
    """Devolve (html novo, mudancas, ausentes)."""
    changes: list[str] = []
    missing: list[str] = []

    def repl(m: re.Match[str]) -> str:
        prefix, url, old, suffix = m.group(1), m.group(2), m.group(3), m.group(4)
        asset = SITE / url.lstrip("/")
        if not asset.is_file():
            # Um asset citado no HTML que nao existe no disco e um 404 em
            # producao: reportar em vez de carimbar um hash inventado.
            missing.append(url)
            return m.group(0)
        new = f"?v={_hash(asset)}"
        if old != new:
            changes.append(f"{url}  {old or '(sem versao)'} -> {new}")
        return f"{prefix}{url}{new}{suffix}"

    return ASSET_RE.sub(repl, html), changes, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="nao escreve; sai 1 se o index.html estiver desatualizado",
    )
    args = parser.parse_args()

    if not INDEX.is_file():
        print(f"ERRO: {INDEX} nao encontrado", file=sys.stderr)
        return 1

    original = INDEX.read_text(encoding="utf-8")
    updated, changes, missing = stamp(original)

    for url in missing:
        print(f"AUSENTE  {url} (citado no index.html, nao existe em site/)", file=sys.stderr)

    if not changes:
        print("Assets ja versionados com o hash atual.")
        return 1 if missing else 0

    if args.check:
        print("index.html DESATUALIZADO:")
        for c in changes:
            print(f"  {c}")
        print("\nRode: python tools/bump_assets_version.py")
        return 1

    INDEX.write_text(updated, encoding="utf-8")
    print(f"index.html atualizado ({len(changes)} asset(s)):")
    for c in changes:
        print(f"  {c}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
