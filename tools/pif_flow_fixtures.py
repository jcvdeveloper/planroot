#!/usr/bin/env python
"""Fixtures de regressao do fluxo PIF (Fase 0 da reducao de perguntas).

As 13 fixtures cobrem as rotas listadas no plano de refatoracao. Cada fixture
declara apenas os 7 classificadores e as respostas de nucleo que precisam
divergir da linha de base; o resto vem de `BASE_CORE`.

`BASE_CORE` responde todas as 40 perguntas `core_always` com a opcao de menor
carga de sinais. Isso e proposital: mantem os sinais perto de zero para que o
roteamento de cada fixture seja governado pelos classificadores, e nao por
ruido acumulado do nucleo. Quando uma pergunta for consolidada na Fase 3, a
entrada correspondente aqui deve ser atualizada de forma explicita e registrada
na tabela de migracao -- nunca recalculada automaticamente.

As perguntas de preset e de overlay ficam deliberadamente sem resposta: e assim
que uma entrevista real chega ao fim hoje, e e esse estado que os renderizadores
precisam continuar tratando.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------- #
# Linha de base: 40 respostas core_always, opcao de menor carga de sinais
# --------------------------------------------------------------------------- #
BASE_CORE: dict[str, str] = {
    # core_identity
    "project_name": "approved_name",
    "sponsor": "single_sponsor",
    "approvers": "single_chain",
    # core_problem_value
    "problem": "local_efficiency_pain",
    "expected_outcome": "localized_improvement",
    "urgency": "planned_window",
    "success_metric": "single_clear_metric",
    "value_hypothesis": "efficiency_gain",
    # core_users_process
    "primary_users": "single_profile",
    "current_process": "manual_process",
    "bottlenecks": "sporadic_friction",
    # core_scope_constraints
    "mvp_scope": "single_job_to_be_done",
    "non_scope": "explicit_non_scope",
    "deadline": "flexible_timeline",
    "constraints": "low_constraint",
    "external_dependencies": "independent",
    "scope_target": "mvp_first",
    # core_data_access
    "access_profile": "single_access_level",
    "handled_data": "reference_data",
    "data_loss_impact": "low_impact",
    "basic_compliance": "no_formal_compliance",
    "main_risks": "delivery_risk",
    # core_final_product
    "use_cases": "single_use_case",
    "flow_criticality": "single_critical_flow",
    "business_rules": "light_rules",
    "permissions": "simple_permissions",
    # core_final_architecture
    "modules": "few_modules",
    "minimal_audit": "light_history",
    "base_integrations": "no_base_integrations",
    "output_directory": "fixed_workspace_path",
    # core_final_security_min
    "authentication": "simple_auth",
    "authorization": "coarse_roles",
    "secrets": "few_local_secrets",
    "retention": "short_retention",
    # core_final_quality
    "test_strategy": "basic_manual_checks",
    "definition_of_done": "light_dod",
    "acceptance_criteria": "simple_acceptance",
    # core_final_continuity
    "backup_restore": "basic_backup",
    "update_strategy": "manual_light_updates",
    "continuity_owner": "single_team_owner",
}

# Classificadores neutros. Cada fixture sobrescreve o que a define.
BASE_CLASSIFIERS: dict[str, str] = {
    "delivery_type": "internal_tool",
    "interaction_model": "backoffice_simple",
    "runtime": "cloud",
    "audience_model": "small_team",
    "integration_intensity": "none",
    "data_risk": "low",
    "ai_usage": "none",
}


class Fixture:
    """Uma rota de entrevista congelada."""

    def __init__(
        self,
        fixture_id: str,
        label: str,
        classifiers: dict[str, str] | None = None,
        core: dict[str, str] | None = None,
    ) -> None:
        self.id = fixture_id
        self.label = label
        self.classifiers = classifiers or {}
        self.core = core or {}

    def answers(self) -> dict[str, Any]:
        """Respostas completas: base + classificadores da fixture + overrides."""
        merged: dict[str, Any] = dict(BASE_CORE)
        merged.update(BASE_CLASSIFIERS)
        merged.update(self.classifiers)
        merged.update(self.core)
        return merged


FIXTURES: list[Fixture] = [
    Fixture(
        "discovery",
        "Descoberta de ideia",
        classifiers={"delivery_type": "design_discovery", "interaction_model": "mixed"},
        core={"project_name": "unnamed_initiative", "mvp_scope": "scope_not_closed"},
    ),
    Fixture(
        "local_offline_tool",
        "Ferramenta local offline",
        classifiers={
            # `local` + `mostly_offline` viraram um unico valor de runtime.
            "runtime": "offline_first",
            "audience_model": "individual",
            "integration_intensity": "none",
        },
    ),
    Fixture(
        "local_team_app",
        "App local de equipe",
        classifiers={
            "runtime": "local",
            "audience_model": "small_team",
            "interaction_model": "ui_rich",
        },
    ),
    Fixture(
        "api_integration",
        "API de integracao",
        classifiers={
            "interaction_model": "api_service",
            "runtime": "cloud",
            "integration_intensity": "few",
        },
    ),
    Fixture(
        "onprem",
        "Sistema on-premise",
        classifiers={
            # `isolated_network` agora esta implicito em `on_prem`.
            "runtime": "on_prem",
            "audience_model": "multi_area",
            "delivery_type": "business_system",
        },
    ),
    Fixture(
        "cloud_app",
        "App cloud de negocio",
        classifiers={
            "runtime": "cloud",
            "delivery_type": "business_system",
            "interaction_model": "ui_rich",
            "integration_intensity": "few",
        },
    ),
    Fixture(
        "cloud_corporate",
        "Cloud corporativo integrado",
        classifiers={
            "runtime": "cloud",
            "delivery_type": "business_system",
            "audience_model": "corporate",
            "integration_intensity": "many",
            "interaction_model": "mixed",
        },
    ),
    Fixture(
        "commerce",
        "Experiencia de comercio",
        classifiers={
            "delivery_type": "commerce_experience",
            "interaction_model": "ui_rich",
            "runtime": "cloud",
        },
        core={"handled_data": "customer_or_financial_data"},
    ),
    Fixture(
        "multi_tenant",
        "Multi-tenant",
        classifiers={
            "runtime": "cloud",
            # Escala e isolamento agora sao um valor so.
            "audience_model": "multi_tenant",
            "delivery_type": "business_system",
        },
    ),
    Fixture(
        "ai_hitl",
        "IA com aprovacao humana",
        classifiers={"ai_usage": "automated_with_hitl", "runtime": "cloud"},
    ),
    Fixture(
        "low_code",
        "Low-code / workflow",
        classifiers={
            # `platform_style` foi absorvido: a automacao em sequencia e o que
            # ativa o overlay low-code.
            "interaction_model": "workflow_automation",
            "runtime": "cloud",
        },
    ),
    Fixture(
        "high_security",
        "Alta seguranca",
        classifiers={"data_risk": "high", "runtime": "cloud"},
        core={
            "handled_data": "sensitive_regulated_data",
            "basic_compliance": "regulated_requirement",
        },
    ),
    Fixture(
        "full_version_annex",
        "Versao completa (exercita o anexo)",
        classifiers={
            "runtime": "offline_first",
            "audience_model": "individual",
            "integration_intensity": "none",
        },
        # A unica fixture com `scope_target` diferente de `mvp_first`: sem ela, a
        # secao "Para versao completa" nunca e renderizada em nenhum snapshot.
        core={"scope_target": "full_version"},
    ),
    Fixture(
        "critical_ops",
        "Operacao critica",
        classifiers={
            # `operational_criticality: high` era redundante com este
            # `delivery_type`, que agora governa a criticidade sozinho.
            "delivery_type": "critical_system",
            "runtime": "cloud",
        },
        core={"data_loss_impact": "high_impact", "main_risks": "operational_risk"},
    ),
]

FIXTURES_BY_ID: dict[str, Fixture] = {fixture.id: fixture for fixture in FIXTURES}
