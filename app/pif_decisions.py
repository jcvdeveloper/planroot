"""Camada de decisoes do PIF: a unidade passa a ser a decisao, nao a pergunta.

O sistema operava como `blocos obrigatorios + perguntas adicionais`. Passa a
operar como `decisoes necessarias + perguntas substituiveis`.

Uma decisao (`decision_key`) pode ser resolvida por mais de uma pergunta. Quando
uma pergunta especializada da rota resolve a mesma decisao que uma generica, a
generica sai do fluxo -- e a relacao e declarada, nunca inferida de texto.

`resolve_interview_plan()` e a fonte unica: wizard, progresso, blueprint,
blueprint minimo, prompt para IA e pendencias devem consumir o mesmo plano.

Nota de projeto: os documentos sugeriam `decision_key` e `supersedes` como
argumentos de `q()`. Aqui eles vivem em tabelas centrais (`DECISION_BY_QUESTION`
e `SUPERSEDES`) porque sao relacionais -- lidas lado a lado, as substituicoes
sao audiveis de uma vez, em vez de espalhadas por 110 registros. O que e
propriedade da pergunta isolada (`ask_when`, `skip_when`, `priority`,
`answer_mode`) continua em `q()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.pif_answers import answer_source, is_answered, legacy_option_id
from app.pif_question_bank import QUESTION_INDEX, QUESTIONS


# --------------------------------------------------------------------------- #
# Catalogo de decisoes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Decision:
    key: str
    domain: str
    weight: int = 1


# Pesos vindos da secao "Progresso" do documento de melhorias: o progresso passa
# a ser medido por decisao resolvida, nao por pergunta respondida.
DECISIONS: tuple[Decision, ...] = (
    Decision("identity.project", "Identidade", 1),
    Decision("governance.ownership", "Governanca", 1),
    Decision("problem.current_state", "Problema", 2),
    Decision("value.target_outcome", "Resultado", 2),
    Decision("value.success_measure", "Medicao", 1),
    Decision("users.audience_and_scale", "Publico", 1),
    Decision("scope.mvp_priorities", "Escopo", 3),
    Decision("delivery.deadline", "Prazo", 1),
    Decision("delivery.constraints", "Restricoes", 1),
    Decision("runtime.environment", "Ambiente", 2),
    Decision("integration.landscape", "Integracoes", 1),
    Decision("data.classification", "Dados", 2),
    Decision("risk.impact", "Risco", 2),
    Decision("compliance.obligations", "Conformidade", 1),
    Decision("access.model", "Acesso", 1),
    Decision("continuity.strategy", "Continuidade", 1),
    Decision("quality.acceptance", "Qualidade", 1),
    Decision("audit.requirements", "Auditoria", 1),
    Decision("ai.usage", "Uso de IA", 1),
)

DECISION_INDEX: dict[str, Decision] = {decision.key: decision for decision in DECISIONS}


# Qual decisao cada pergunta ajuda a resolver.
# Perguntas de preset e overlay entram junto das genericas de proposito: e isso
# que permite a especializada substituir a generica quando a rota a ativa.
DECISION_BY_QUESTION: dict[str, str] = {
    # -- Identidade e governanca
    "project_name": "identity.project",
    "sponsor": "governance.ownership",
    "approvers": "governance.ownership",
    # -- Problema
    "problem": "problem.current_state",
    "current_process": "problem.current_state",
    "bottlenecks": "problem.current_state",
    # -- Resultado e medicao
    "expected_outcome": "value.target_outcome",
    "value_hypothesis": "value.target_outcome",
    "success_metric": "value.success_measure",
    # -- Publico e escala
    "primary_users": "users.audience_and_scale",
    "audience_model": "users.audience_and_scale",
    # -- Escopo
    "mvp_scope": "scope.mvp_priorities",
    "non_scope": "scope.mvp_priorities",
    "scope_target": "scope.mvp_priorities",
    "use_cases": "scope.mvp_priorities",
    "flow_criticality": "scope.mvp_priorities",
    "modules": "scope.mvp_priorities",
    # -- Prazo e restricoes
    "urgency": "delivery.deadline",
    "deadline": "delivery.deadline",
    "constraints": "delivery.constraints",
    "external_dependencies": "delivery.constraints",
    # -- Ambiente
    "delivery_type": "runtime.environment",
    "interaction_model": "runtime.environment",
    "runtime": "runtime.environment",
    "output_directory": "runtime.environment",
    # -- Integracoes
    "integration_intensity": "integration.landscape",
    "base_integrations": "integration.landscape",
    # -- Dados
    "handled_data": "data.classification",
    "data_risk": "data.classification",
    # -- Risco
    "data_loss_impact": "risk.impact",
    "main_risks": "risk.impact",
    # -- Conformidade
    "basic_compliance": "compliance.obligations",
    # -- Acesso
    "access_profile": "access.model",
    "permissions": "access.model",
    "authentication": "access.model",
    "authorization": "access.model",
    "secrets": "access.model",
    # -- Continuidade
    "backup_restore": "continuity.strategy",
    "update_strategy": "continuity.strategy",
    "continuity_owner": "continuity.strategy",
    "retention": "continuity.strategy",
    # -- Qualidade
    "business_rules": "quality.acceptance",
    "test_strategy": "quality.acceptance",
    "definition_of_done": "quality.acceptance",
    "acceptance_criteria": "quality.acceptance",
    # -- Auditoria
    "minimal_audit": "audit.requirements",
    # -- IA
    "ai_usage": "ai.usage",
    # -- Especializadas de preset/overlay que resolvem uma decisao ja existente.
    #    Sem isto elas apenas se somariam ao nucleo, que e a causa raiz apontada
    #    no diagnostico.
    "local_update": "continuity.strategy",
    "local_recovery": "continuity.strategy",
    "local_rollout": "continuity.strategy",
    "dr_runbooks": "continuity.strategy",
    "release_rollback": "continuity.strategy",
    "security_audit_scope": "audit.requirements",
    "agent_audit": "audit.requirements",
    "commerce_core_integrations": "integration.landscape",
    "iam_sso": "access.model",
    "technical_auth": "access.model",
    "privileged_actions": "access.model",
}


# Perguntas especializadas que resolvem a mesma decisao de uma generica.
# `especializada -> [genericas que saem do fluxo quando ela e respondida]`.
#
# A relacao e declarada, nunca inferida de texto. Cada par vem do diagnostico
# nos documentos e esta registrado em PIF_Migration_Table.md com o efeito
# medido por rota. Uma generica so sai depois que a especializada foi de fato
# respondida -- ate la nada e perdido.
SUPERSEDES: dict[str, list[str]] = {
    # Continuidade
    "local_update": ["update_strategy"],
    "local_rollout": ["update_strategy"],
    "release_rollback": ["update_strategy"],
    "local_recovery": ["backup_restore"],
    "dr_runbooks": ["backup_restore"],
    # Auditoria
    "security_audit_scope": ["minimal_audit"],
    "agent_audit": ["minimal_audit"],
    # Integracoes
    "commerce_core_integrations": ["base_integrations"],
    # Acesso
    "iam_sso": ["authentication"],
    "technical_auth": ["authentication"],
    "privileged_actions": ["authorization"],
}


# --------------------------------------------------------------------------- #
# Plano da entrevista
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class InterviewPlan:
    """Retrato completo de uma entrevista num dado momento."""

    active_question_ids: list[str]
    pending_question_ids: list[str]
    resolved_decisions: dict[str, Any]
    unresolved_decision_keys: list[str]
    skipped: dict[str, str]
    provenance: dict[str, str]
    progress: float = 0.0

    def is_active(self, question_id: str) -> bool:
        return question_id in self._active_set

    @property
    def _active_set(self) -> frozenset[str]:
        return frozenset(self.active_question_ids)


# --------------------------------------------------------------------------- #
# Rota
# --------------------------------------------------------------------------- #
def route_question_ids(routing: dict[str, Any]) -> list[str]:
    """Perguntas da rota escolhida, na ordem do banco.

    = core_always + classificadores + o preset eleito + os overlays ativos.
    Presets e overlays inativos nunca entram.
    """
    primary_preset = routing.get("primary_preset")
    preset_block = f"preset_{primary_preset}" if primary_preset else None
    overlay_blocks = {f"overlay_{overlay}" for overlay in routing.get("active_overlays", [])}

    ids: list[str] = []
    for question in QUESTIONS:
        block_type = question["block_type"]
        if block_type in ("core_always", "classifier"):
            ids.append(question["id"])
        elif block_type == "preset_block" and question["block"] == preset_block:
            ids.append(question["id"])
        elif block_type == "overlay_block" and question["block"] in overlay_blocks:
            ids.append(question["id"])
    return ids


def _condition_holds(condition: Any, context: dict[str, Any]) -> bool:
    """Avalia `ask_when` / `skip_when` de forma determinística.

    Formatos aceitos:

        {"campo": valor}            -- igualdade
        {"campo": [v1, v2]}         -- pertence ao conjunto
        {"campo": {"gte": 2}}       -- comparacao numerica (`gte` / `lte`)
        [cond_a, cond_b]            -- OU entre condicoes

    Num dicionario, TODOS os pares precisam bater (E). Numa lista, basta uma
    condicao bater (OU) -- e o que permite escrever "pergunte isto quando o
    risco for alto OU o projeto pedir rigor".

    `campo` pode ser um id de pergunta (compara a opcao escolhida), um
    classificador, um sinal, `depth_profile`, `primary_preset` ou
    `overlay:<nome>`.
    """
    if not condition:
        return False

    if isinstance(condition, (list, tuple)):
        return any(_condition_holds(item, context) for item in condition)

    for field_name, expected in condition.items():
        actual = context.get(field_name)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif isinstance(expected, dict):
            minimum = expected.get("gte")
            maximum = expected.get("lte")
            if minimum is not None and not (isinstance(actual, (int, float)) and actual >= minimum):
                return False
            if maximum is not None and not (isinstance(actual, (int, float)) and actual <= maximum):
                return False
        elif actual != expected:
            return False
    return True


def _build_context(answers: dict[str, Any], routing: dict[str, Any]) -> dict[str, Any]:
    """Contexto para as condicoes: respostas + classificadores + sinais + rota."""
    context: dict[str, Any] = {}
    context.update(routing.get("signals", {}))
    context.update(routing.get("classifiers", {}))
    # Saidas do roteador: permitem condicionar profundidade ("so pergunte isto
    # quando o projeto pedir rigor") sem duplicar as regras da matriz.
    context["depth_profile"] = routing.get("depth_profile")
    context["primary_preset"] = routing.get("primary_preset")
    for overlay in routing.get("active_overlays", []):
        context[f"overlay:{overlay}"] = True
    for question_id, raw_answer in (answers or {}).items():
        option_id = legacy_option_id(raw_answer)
        if option_id is not None:
            context[question_id] = option_id
    return context


def resolve_interview_plan(
    answers: dict[str, Any] | None,
    routing: dict[str, Any],
    *,
    include_optional: bool = False,
) -> InterviewPlan:
    """Fonte unica de verdade sobre o que perguntar, o que ja foi decidido e o que falta."""
    answers = answers or {}
    context = _build_context(answers, routing)

    candidates = route_question_ids(routing)
    skipped: dict[str, str] = {}

    # 1) Perguntas fora da rota escolhida.
    for question in QUESTIONS:
        if question["id"] not in candidates:
            skipped[question["id"]] = f"fora da rota ({question['block']})"

    # 2) Condicoes declaradas na propria pergunta.
    active: list[str] = []
    for question_id in candidates:
        question = QUESTION_INDEX[question_id]

        skip_when = question.get("skip_when")
        if skip_when and _condition_holds(skip_when, context):
            skipped[question_id] = "skip_when satisfeito"
            continue

        ask_when = question.get("ask_when")
        if ask_when and not _condition_holds(ask_when, context):
            skipped[question_id] = "ask_when nao satisfeito"
            continue

        active.append(question_id)

    # 3) Substituicao: a especializada respondida remove a generica equivalente.
    superseded: dict[str, str] = {}
    for specialized, generics in SUPERSEDES.items():
        if specialized not in active or not is_answered(answers.get(specialized)):
            continue
        for generic in generics:
            if generic in active and generic != specialized:
                superseded[generic] = f"substituida por {specialized}"

    if superseded:
        active = [question_id for question_id in active if question_id not in superseded]
        skipped.update(superseded)

    # 4) Decisoes resolvidas e pendentes.
    resolved: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    for question_id in active:
        if not is_answered(answers.get(question_id)):
            continue
        decision_key = DECISION_BY_QUESTION.get(question_id)
        if decision_key is None:
            continue
        # A primeira resposta da ordem do banco fixa a decisao; uma
        # especializada so vence porque a generica ja saiu do fluxo acima.
        resolved.setdefault(decision_key, {})[question_id] = legacy_option_id(answers[question_id])
        provenance.setdefault(decision_key, answer_source(answers[question_id]))

    # Uma decisao so e exigida quando a rota tem ao menos uma pergunta capaz de
    # resolve-la. Decisao que este projeto nao precisa tomar nao e pendencia --
    # conta-la travaria o progresso abaixo de 100% para sempre numa rota enxuta.
    required_keys = [
        decision.key
        for decision in DECISIONS
        if any(DECISION_BY_QUESTION.get(qid) == decision.key for qid in active)
    ]
    unresolved = [key for key in required_keys if key not in resolved]

    pending = [qid for qid in active if not is_answered(answers.get(qid))]

    total_weight = sum(DECISION_INDEX[key].weight for key in required_keys)
    done_weight = sum(DECISION_INDEX[key].weight for key in resolved)
    progress = round(done_weight / total_weight * 100, 1) if total_weight else 0.0

    return InterviewPlan(
        active_question_ids=active,
        pending_question_ids=pending,
        resolved_decisions=resolved,
        unresolved_decision_keys=unresolved,
        skipped=skipped,
        provenance=provenance,
        progress=progress,
    )
