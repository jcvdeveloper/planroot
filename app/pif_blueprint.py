"""Parsimonious blueprint renderer for the deterministic Planroot/PIF interview.

The renderer follows one rule: only emit what was actually answered.
- `core_always` blocks are emitted; missing answers become `[PENDENTE]`.
- `preset_block` is emitted only when the matrix chose a primary_preset.
- `overlay_block` sections are emitted only when the overlay is active.
- No block is ever inflated with template content.
- When `scope_target = full_version`, the renderer appends a "Para versão completa" annex
  listing questions that should be asked next. It never fills them in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from app.pif_answers import answer_details, detail_text, is_answered, legacy_option_id
from app.pif_decisions import resolve_interview_plan
from app.pif_question_bank import OPTION_INDEX, QUESTION_INDEX, QUESTIONS


PENDENTE = "[PENDENTE]"

# Chaves aceitas para o nome real do projeto, em ordem de preferencia.
_PROJECT_NAME_KEYS = ("name", "nome")

# Frases legiveis para o vocabulario interno do roteador.
# Usadas tanto no blueprint tecnico (scope) quanto no "Prompt para IA".
_SCOPE_HUMAN = {
    "full_version": "versão completa",
    "mvp_plus_near_roadmap": "MVP + roadmap próximo",
    "mvp_then_iterate": "MVP + iteração posterior",
    "mvp_first": "MVP (parcimonioso)",
}

_DEPTH_HUMAN = {
    "strict": "é um projeto que pede rigor alto (as decisões precisam ser bem pensadas)",
    "standard": "é um projeto de complexidade média",
    "lite": "é um projeto enxuto, em que as decisões podem ser mais leves",
}

_PRESET_HUMAN = {
    "design_discovery_service": "uma fase de descoberta e validação da ideia, antes de construir de verdade",
    "local_offline_tool": "uma ferramenta que roda no próprio computador, sem depender da internet",
    "local_small_team_app": "um aplicativo usado localmente por uma equipe pequena",
    "api_integration_service": "um serviço que conecta sistemas automaticamente, sem telas",
    "onprem_business_system": "um sistema que roda nos servidores da própria empresa",
    "cloud_business_app": "um aplicativo de negócio que roda na internet (nuvem)",
    "cloud_corporate_integrated": "um aplicativo corporativo na nuvem, integrado a outros sistemas da empresa",
    "commerce_frontend_app": "uma experiência de venda ou loja voltada ao cliente final",
}

_OVERLAY_HUMAN = {
    "frontend_light": "ter uma interface de telas simples e leve",
    "offline_sync": "funcionar sem internet e sincronizar os dados depois",
    "integrations_heavy": "conectar com muitos outros sistemas",
    "security_strong": "ter segurança reforçada",
    "ops_advanced": "ter monitoramento e operação mais avançados",
    "multi_tenant": "atender vários clientes no mesmo sistema, com os dados de cada um separados",
    "ai_hitl": "usar inteligência artificial com revisão de uma pessoa antes de valer",
    "low_code_workflow": "ser montado com ferramentas visuais, com pouca programação",
}

# Titulos de secao amigaveis para o "Prompt para IA" (nao reutiliza _title_for_block,
# que serve o blueprint tecnico e seus testes).
_AI_BLOCK_TITLE = {
    "core_identity": "Identidade do projeto",
    "core_problem_value": "Problema e valor",
    "core_users_process": "Quem usa e como funciona hoje",
    "core_scope_constraints": "Escopo e limites",
    "core_data_access": "Dados, acesso e riscos",
    "core_final_product": "O produto",
    "core_final_architecture": "Como vai ser organizado",
    "core_final_security_min": "Segurança",
    "core_final_quality": "Qualidade e aprovação",
    "core_final_continuity": "Manutenção e continuidade",
    "preset_design_discovery_service": "Detalhes da descoberta da ideia",
    "preset_local_offline_tool": "Detalhes da ferramenta local",
    "preset_local_small_team_app": "Detalhes do app de equipe",
    "preset_api_integration_service": "Detalhes da integração entre sistemas",
    "preset_onprem_business_system": "Detalhes do sistema na empresa",
    "preset_cloud_business_app": "Detalhes do app na nuvem",
    "preset_cloud_corporate_integrated": "Detalhes do app corporativo integrado",
    "preset_commerce_frontend_app": "Detalhes da experiência de venda",
    "overlay_frontend_light": "Sobre as telas",
    "overlay_offline_sync": "Sobre funcionar offline",
    "overlay_integrations_heavy": "Sobre as integrações",
    "overlay_security_strong": "Sobre segurança",
    "overlay_ops_advanced": "Sobre operação e monitoramento",
    "overlay_multi_tenant": "Sobre atender vários clientes",
    "overlay_ai_hitl": "Sobre o uso de IA",
    "overlay_low_code_workflow": "Sobre a ferramenta visual",
}


@dataclass(frozen=True)
class SectionPlan:
    block_id: str
    block_type: str
    title: str
    question_ids: list[str]


def plan_sections(routing: dict[str, Any], answers: dict[str, Any] | None = None) -> list[SectionPlan]:
    """Order sections deterministically: core_always, classifier, preset, overlays.

    As perguntas vem do `InterviewPlan`: uma pergunta removida do fluxo (fora da
    rota, condicionada ou substituida) tambem some do blueprint.
    """
    plan = resolve_interview_plan(answers or {}, routing)
    active = set(plan.active_question_ids)

    by_block: dict[str, list[str]] = {}
    block_meta: dict[str, tuple[str, str, str]] = {}

    for question in QUESTIONS:
        if question["phase"] == "Classificadores":
            continue
        block = question["block"]
        if question["id"] == "scope_target":
            continue
        if question["id"] not in active:
            continue
        by_block.setdefault(block, []).append(question["id"])
        block_meta[block] = (
            question["phase"],
            question["block_type"],
            _title_for_block(block),
        )

    core_block_order = [
        "core_identity",
        "core_problem_value",
        "core_users_process",
        "core_scope_constraints",
        "core_data_access",
        "core_final_product",
        "core_final_architecture",
        "core_final_security_min",
        "core_final_quality",
        "core_final_continuity",
    ]

    sections: list[SectionPlan] = []
    for block in core_block_order:
        if block not in by_block:
            continue
        phase, block_type, title = block_meta[block]
        sections.append(SectionPlan(block, block_type, title, by_block[block]))

    primary_preset = routing.get("primary_preset")
    if primary_preset:
        preset_block = f"preset_{primary_preset}"
        if preset_block in by_block:
            phase, block_type, _ = block_meta[preset_block]
            sections.append(
                SectionPlan(
                    preset_block,
                    block_type,
                    _title_for_block(preset_block),
                    by_block[preset_block],
                )
            )

    for overlay in routing.get("active_overlays", []):
        overlay_block = f"overlay_{overlay}"
        if overlay_block in by_block:
            phase, block_type, _ = block_meta[overlay_block]
            sections.append(
                SectionPlan(
                    overlay_block,
                    block_type,
                    _title_for_block(overlay_block),
                    by_block[overlay_block],
                )
            )

    return sections


def _title_for_block(block: str) -> str:
    titles = {
        "core_identity": "Identidade",
        "core_problem_value": "Problema, resultado e valor",
        "core_users_process": "Usuários, fluxos e processo",
        "core_scope_constraints": "Escopo e restrições",
        "core_data_access": "Dados, acesso e riscos",
        "core_final_product": "Produto final",
        "core_final_architecture": "Arquitetura final",
        "core_final_security_min": "Segurança mínima",
        "core_final_quality": "Qualidade e aceite",
        "core_final_continuity": "Continuidade operacional",
        "preset_design_discovery_service": "Preset: design & discovery",
        "preset_local_offline_tool": "Preset: ferramenta local offline",
        "preset_local_small_team_app": "Preset: app local de equipe",
        "preset_api_integration_service": "Preset: API / integração",
        "preset_onprem_business_system": "Preset: sistema on-prem",
        "preset_commerce_frontend_app": "Preset: experiência comercial",
        "preset_cloud_business_app": "Preset: app cloud de negócio",
        "preset_cloud_corporate_integrated": "Preset: cloud corporativo integrado",
        "overlay_frontend_light": "Overlay: frontend leve",
        "overlay_offline_sync": "Overlay: sincronização offline",
        "overlay_integrations_heavy": "Overlay: integrações pesadas",
        "overlay_security_strong": "Overlay: segurança forte",
        "overlay_ops_advanced": "Overlay: operação avançada",
        "overlay_multi_tenant": "Overlay: multi-tenant",
        "overlay_ai_hitl": "Overlay: IA com HITL",
        "overlay_low_code_workflow": "Overlay: low-code / workflow",
    }
    if block in titles:
        return titles[block]
    return block


def _classifiers_block(routing: dict[str, Any]) -> list[tuple[str, str]]:
    classifiers = routing.get("classifiers", {})
    return [(field, value) for field, value in sorted(classifiers.items())]


def _format_signal_value(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{int(value)}"
    return str(value)


def _selected_label(question_id: str, option_id: str) -> str:
    option = OPTION_INDEX[question_id].get(option_id)
    if option is None:
        return option_id
    return option["label"]


def _option_of(answers: dict[str, Any], question_id: str) -> str | None:
    """Id da opcao escolhida, aceitando formato legado e estruturado."""
    return legacy_option_id(answers.get(question_id))


def _format_details(answers: dict[str, Any], question_id: str) -> str:
    """Detalhes concretos do cliente, prontos para anexar a uma linha."""
    details = answer_details(answers.get(question_id))
    if not details:
        return ""

    parts: list[str] = []
    for key, value in details.items():
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        parts.append(f"{key}: {value}")
    return " — " + "; ".join(parts)


def _project_identity(answers: dict[str, Any]) -> tuple[str | None, str | None]:
    """(nome real informado, rotulo da situacao do nome).

    A pergunta `project_name` classifica o *estado* do nome ("ja decidido",
    "provisorio"). O nome em si vive nos detalhes. Renderizar o rotulo da opcao
    como se fosse o nome produz linhas como "Projeto: Ja tenho o nome final".
    """
    name = detail_text(answers, "project_name", *_PROJECT_NAME_KEYS)
    option_id = _option_of(answers, "project_name")
    status = _selected_label("project_name", option_id) if option_id else None
    return name, status


def render_blueprint(
    answers: dict[str, str],
    routing: dict[str, Any],
    *,
    pending_questions: Iterable[str] | None = None,
) -> str:
    lines: list[str] = []
    # `routing["pending_questions"]` varre as 110 perguntas do banco e lista
    # pendencias de presets e overlays que este projeto nunca tera. O padrao e
    # a pendencia da rota ativa; a lista explicita continua aceita, mas e
    # filtrada pelo plano para nao reintroduzir rota inativa.
    plan = resolve_interview_plan(answers, routing)
    if pending_questions is None:
        pending = list(plan.pending_question_ids)
    else:
        # Cruzar com a pendencia real do plano: a lista do chamador pode estar
        # defasada e conter perguntas ja respondidas ou fora da rota.
        realmente_pendentes = set(plan.pending_question_ids)
        pending = [qid for qid in pending_questions if qid in realmente_pendentes]

    project_name, project_status = _project_identity(answers)
    lines.append("# Blueprint")
    lines.append("")
    lines.append(f"- Projeto: {project_name or PENDENTE}")
    if project_status:
        lines.append(f"- Situação do nome: {project_status}")
    lines.append(f"- Profundidade: {routing.get('depth_profile') or PENDENTE}")
    lines.append(f"- Preset principal: {routing.get('primary_preset') or PENDENTE}")
    lines.append(f"- Overlays ativos: {', '.join(routing.get('active_overlays', [])) or PENDENTE}")

    scope_target = _option_of(answers, "scope_target")
    scope_label = _SCOPE_HUMAN.get(scope_target, PENDENTE)
    lines.append(f"- Alvo do blueprint: {scope_label}")

    blueprint_profile = routing.get("blueprint_profile") or {}
    if blueprint_profile:
        lines.append("- Perfis iniciais:")
        for field, value in sorted(blueprint_profile.items()):
            lines.append(f"  - {field}: {value}")
    lines.append("")

    classifier_pairs = _classifiers_block(routing)
    if classifier_pairs:
        lines.append("## Classificadores derivados")
        lines.append("")
        for field, value in classifier_pairs:
            lines.append(f"- `{field}`: {value}")
        lines.append("")

    for section in plan_sections(routing, answers):
        lines.append(f"## {section.title}")
        lines.append("")
        for question_id in section.question_ids:
            question = QUESTION_INDEX[question_id]
            option_id = _option_of(answers, question_id)
            if option_id:
                label = _selected_label(question_id, option_id)
                details = _format_details(answers, question_id)
                option = OPTION_INDEX[question_id].get(option_id)
                signals = option.get("signals", {}) if option else {}
                if signals:
                    signal_str = ", ".join(
                        f"{key}={_format_signal_value(value)}"
                        for key, value in sorted(signals.items())
                    )
                    lines.append(f"- **{question['title']}**: {label}{details} (sinais: {signal_str})")
                else:
                    lines.append(f"- **{question['title']}**: {label}{details}")
            else:
                lines.append(f"- **{question['title']}**: {PENDENTE}")
        lines.append("")

    if scope_target in {"mvp_then_iterate", "mvp_plus_near_roadmap", "full_version"}:
        lines.append("## Para versão completa")
        lines.append("")
        lines.append(
            "A matriz continua parcimoniosa. As perguntas abaixo ainda não foram respondidas e "
            "precisam ser feitas antes de tratar este blueprint como plano além do MVP. "
            "Nada é preenchido automaticamente."
        )
        lines.append("")
        # Somente pendencias da rota ativa. Varrer `QUESTIONS` listava perguntas
        # de presets e overlays que nunca serao feitas neste projeto.
        for question_id in plan.pending_question_ids:
            if question_id == "scope_target":
                continue
            lines.append(f"- {question_id}: {QUESTION_INDEX[question_id]['title']}")
        lines.append("")

    if pending:
        lines.append("## Pendências da entrevista")
        lines.append("")
        for question_id in pending:
            question = QUESTION_INDEX.get(question_id)
            if question is None:
                lines.append(f"- {question_id}")
            else:
                lines.append(f"- {question['title']} (`{question_id}`)")
        lines.append("")

    cleaned = [line for line in lines if line is not None]
    return "\n".join(cleaned).rstrip() + "\n"


def _ai_block_title(block: str) -> str:
    return _AI_BLOCK_TITLE.get(block, _title_for_block(block))


def _answered_label(answers: dict[str, str], question_id: str) -> str | None:
    option_id = _option_of(answers, question_id)
    if not option_id:
        return None
    return _selected_label(question_id, option_id)


def render_ai_prompt(
    answers: dict[str, str],
    routing: dict[str, Any],
    *,
    brief: str | None = None,
) -> str:
    """Render a self-contained, copy-paste-ready prompt for an AI assistant.

    Beginner-facing: plain language, no raw signals, no `[PENDENTE]` markers.
    Unanswered questions of the active path are surfaced gently as open decisions.
    """
    lines: list[str] = []

    # (1) Preambulo: instrucao para a IA.
    lines.append("# Prompt para sua IA construir este projeto")
    lines.append("")
    lines.append(
        "Você é um(a) desenvolvedor(a) sênior e mentor(a). Vou te dar o contexto de um "
        "projeto que quero construir. Com base nele:"
    )
    lines.append("")
    lines.append("1. Proponha um plano técnico claro, do passo mais simples ao mais completo.")
    lines.append("2. Aponte as decisões que ainda faltam e me faça as perguntas necessárias.")
    lines.append("3. Sugira ferramentas e tecnologias adequadas para quem está começando.")
    lines.append("4. Me dê um primeiro passo concreto para começar hoje.")
    lines.append("")
    lines.append("Use linguagem acessível e explique o porquê de cada escolha.")
    lines.append("")

    # (2) Contexto do projeto em prosa simples.
    lines.append("## O projeto em poucas palavras")
    lines.append("")
    project_name, project_status = _project_identity(answers)
    if project_name:
        lines.append(f"Nome do projeto: {project_name}.")
    elif project_status:
        # Sem o nome real, o que temos e a situacao dele. Dizer isso e honesto;
        # imprimir o rotulo como se fosse o nome, nao.
        lines.append(f"Sobre o nome do projeto: {project_status}.")
    if brief:
        lines.append(f"Na minha descrição: {brief.strip()}")
    problem_label = _answered_label(answers, "problem")
    if problem_label:
        lines.append(f"O problema que eu quero resolver: {problem_label}.")
    outcome_label = _answered_label(answers, "expected_outcome")
    if outcome_label:
        lines.append(f"O que vai significar dar certo: {outcome_label}.")
    preset = routing.get("primary_preset")
    depth = routing.get("depth_profile")
    shape_bits = []
    if preset and preset in _PRESET_HUMAN:
        shape_bits.append(f"isto se parece com {_PRESET_HUMAN[preset]}")
    if depth and depth in _DEPTH_HUMAN:
        shape_bits.append(_DEPTH_HUMAN[depth])
    if shape_bits:
        lines.append("Pelo que respondi, " + "; ".join(shape_bits) + ".")
    lines.append("")

    # (3) Requisitos e decisoes ja tomadas, em linguagem leiga, SEM sinais.
    lines.append("## O que já foi decidido")
    lines.append("")
    for section in plan_sections(routing, answers):
        answered = [
            (qid, _answered_label(answers, qid))
            for qid in section.question_ids
            # A identidade ja foi dita em prosa acima. Repetir aqui reimprime o
            # rotulo da opcao ("Ja tenho o nome final") como se fosse o nome.
            if qid != "project_name" and _answered_label(answers, qid)
        ]
        if not answered:
            continue
        lines.append(f"### {_ai_block_title(section.block_id)}")
        for qid, label in answered:
            lines.append(f"- {QUESTION_INDEX[qid]['title']}: {label}{_format_details(answers, qid)}")
        lines.append("")

    overlays = [o for o in routing.get("active_overlays", []) if o in _OVERLAY_HUMAN]
    if overlays:
        lines.append("**Características especiais que o projeto precisa:** " + "; ".join(
            _OVERLAY_HUMAN[o] for o in overlays
        ) + ".")
        lines.append("")

    # (4) O que ainda esta em aberto (gentil, sem [PENDENTE]).
    pending_prompts: list[str] = []
    for section in plan_sections(routing, answers):
        for qid in section.question_ids:
            if not answers.get(qid):
                pending_prompts.append(QUESTION_INDEX[qid]["prompt"])
    lines.append("## O que ainda precisamos decidir")
    lines.append("")
    if pending_prompts:
        lines.append(
            "Estes pontos ainda não foram definidos. Tudo bem — me ajude a decidir cada um, "
            "respondendo com o que eu já souber:"
        )
        lines.append("")
        for prompt in pending_prompts:
            lines.append(f"- {prompt}")
    else:
        lines.append("Já respondi o essencial do caminho atual. Mesmo assim, me diga se faltou algo importante.")
    lines.append("")

    # (5) Pedido final.
    lines.append("## O que eu preciso de você")
    lines.append("")
    lines.append("1. Um plano técnico em passos, do mais simples ao mais completo.")
    lines.append("2. As perguntas que você ainda precisa que eu responda.")
    lines.append("3. Uma sugestão de tecnologias e ferramentas adequada para um iniciante.")
    lines.append("4. Um primeiro passo concreto para eu começar hoje.")

    cleaned = [line for line in lines if line is not None]
    return "\n".join(cleaned).rstrip() + "\n"


def render_minimal_blueprint(
    answers: dict[str, str],
    routing: dict[str, Any],
) -> str:
    """Strictly minimal variant.

    Includes core and preset sections only when at least one of their questions
    was answered. Includes overlay sections whenever the overlay is active,
    because the matrix decided it should be present even if no overlay question
    was answered yet.
    """
    lines: list[str] = []
    project_name, _ = _project_identity(answers)
    lines.append("# Blueprint mínimo")
    lines.append("")
    lines.append(f"- Projeto: {project_name or PENDENTE}")
    lines.append(f"- Profundidade: {routing.get('depth_profile') or PENDENTE}")
    lines.append(f"- Preset principal: {routing.get('primary_preset') or PENDENTE}")
    lines.append(f"- Overlays ativos: {', '.join(routing.get('active_overlays', [])) or PENDENTE}")
    lines.append("")

    for section in plan_sections(routing, answers):
        answered = [qid for qid in section.question_ids if is_answered(answers.get(qid))]
        if not answered and not section.block_id.startswith("overlay_"):
            continue
        lines.append(f"## {section.title}")
        lines.append("")
        if answered:
            for question_id in answered:
                label = _selected_label(question_id, _option_of(answers, question_id))
                question = QUESTION_INDEX[question_id]
                lines.append(f"- **{question['title']}**: {label}{_format_details(answers, question_id)}")
        else:
            lines.append(f"- {PENDENTE}")
        lines.append("")

    cleaned = [line for line in lines if line is not None]
    return "\n".join(cleaned).rstrip() + "\n"
