#!/usr/bin/env python
"""Build a parsimonious Planroot/PIF blueprint from interview answers.

The script consumes the same JSON shape accepted by `pif_router.py` (`answers` or `classifiers`),
runs the deterministic router, and renders a Markdown blueprint.

Parsimony rules:
- `core_always` blocks always appear; missing answers become `[PENDENTE]`.
- `preset_block` appears only when the matrix chose a `primary_preset`.
- `overlay_block` sections appear only when the overlay is active.
- No block is inflated with template content.
- When `scope_target` is beyond MVP, an annex is added listing unanswered questions.
- `--strict` errors out if any required router field is missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = "answers.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pif_blueprint import render_blueprint, render_minimal_blueprint
from tools.pif_router import _extract_input, load_json, resolve_routing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a parsimonious blueprint from answers or classifiers.")
    parser.add_argument("--input", required=True, help="Path to a JSON file with answers or classifiers.")
    parser.add_argument("--matrix", default=str(ROOT / "PIF_Decision_Matrix.json"), help="Path to PIF_Decision_Matrix.json.")
    parser.add_argument("--output", help="Where to write the blueprint markdown. Defaults to stdout.")
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Use the strict-minimum renderer (only sections with answered questions).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with a non-zero exit code if the router reports any error.",
    )
    parser.add_argument(
        "--pending-as-block",
        action="store_true",
        help="Always include the 'Pendências da entrevista' section in the blueprint body.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    matrix = load_json(Path(args.matrix))
    payload = load_json(Path(args.input))
    input_mode, input_data = _extract_input(payload)
    routing = resolve_routing(input_data, matrix, input_mode=input_mode)

    if args.strict and not routing.get("ok"):
        print(json.dumps(routing, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    answers = routing.get("answers", {})
    pending = routing.get("pending_questions", []) if args.pending_as_block else []
    answers_for_render = answers if input_mode == "answers" else {}

    renderer = render_minimal_blueprint if args.minimal else render_blueprint
    markdown = renderer(answers_for_render, routing, pending_questions=pending)

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
