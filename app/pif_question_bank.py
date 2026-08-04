"""Deterministic interview bank for Planroot/PIF.

Every question exposes 3-5 substantive answer options.
Concrete names, examples, and notes live outside this catalog as free-form details.
The selected option contributes deterministic signals to routing and blueprint planning.

Os textos (prompt/label/detail_hint) usam linguagem de iniciante, sem jargao de
desenvolvedor. Os campos estruturais (id, signals, classifier_value, block, phase)
controlam o roteamento e nao devem mudar ao reescrever os textos.
"""

from __future__ import annotations

from typing import Any


def opt(
    option_id: str,
    label: str,
    signals: dict[str, int] | None = None,
    classifier_value: str | None = None,
) -> dict[str, Any]:
    return {
        "id": option_id,
        "label": label,
        "signals": signals or {},
        "classifier_value": classifier_value,
    }


# Campo de detalhe usado quando a pergunta nao declara `detail_schema`.
# Uma anotacao livre, sem tipo -- serve para qualquer pergunta.
DEFAULT_DETAIL_FIELD = {"key": "nota", "type": "text", "label": None}


def q(
    question_id: str,
    phase: str,
    block: str,
    title: str,
    prompt: str,
    options: list[dict[str, Any]],
    classifier_field: str | None = None,
    block_type: str = "core_always",
    detail_hint: str | None = None,
    *,
    detail_schema: dict[str, Any] | None = None,
    ask_when: dict[str, Any] | None = None,
    skip_when: dict[str, Any] | None = None,
    priority: int = 100,
    answer_mode: str = "single_choice",
) -> dict[str, Any]:
    """Registro de pergunta.

    `detail_schema` descreve os detalhes concretos que a pergunta coleta ao lado
    da opcao escolhida (nome, data, sistema, responsavel). Formato:

        {"fields": [{"key": "date", "type": "date", "label": "Qual data?"}]}

    E opcional e kw-only de proposito: os 110 registros existentes continuam
    validos sem alteracao, e quem nao declara nada ganha um campo de anotacao
    livre. Os detalhes nunca influenciam o roteamento.

    `ask_when` / `skip_when` sao condicoes deterministicas de exibicao, avaliadas
    por `app.pif_decisions`. Formato: {"campo": valor} ou {"campo": [v1, v2]},
    onde `campo` e um id de pergunta, um classificador ou um sinal. Todos os
    pares precisam bater. A qual decisao a pergunta pertence e quais genericas
    ela substitui vivem em `app/pif_decisions.py`, em tabelas centrais.
    """
    return {
        "id": question_id,
        "phase": phase,
        "block": block,
        "block_type": block_type,
        "title": title,
        "prompt": prompt,
        "options": options,
        "classifier_field": classifier_field,
        "detail_hint": detail_hint or "Se ajudar, escreva aqui detalhes, exemplos ou observacoes nas suas palavras.",
        "detail_schema": detail_schema or {"fields": [dict(DEFAULT_DETAIL_FIELD)]},
        "ask_when": ask_when,
        "skip_when": skip_when,
        "priority": priority,
        "answer_mode": answer_mode,
    }


QUESTIONS: list[dict[str, Any]] = [
    q(
        "project_name",
        "Motor Inicial",
        "core_identity",
        "Nome do projeto",
        "Qual é o nome do seu projeto?",
        [
            opt("approved_name", "Já tenho o nome final, decidido", {"clarity_risk": 0}),
            opt("working_name", "Tenho um nome provisório que já uso", {"clarity_risk": 1}),
            opt("commercial_name_pending", "O nome ainda depende da marca/identidade visual", {"clarity_risk": 2}),
            opt("unnamed_initiative", "Ainda não tenho um nome", {"clarity_risk": 2}),
        ],
        detail_hint="Anote o nome atual e outras ideias de nome que você tenha.",
        detail_schema={
            "fields": [
                {"key": "name", "type": "text", "label": "Como o projeto se chama (ou vai se chamar)?"},
            ]
        },
    ),
    q(
        "sponsor",
        "Motor Inicial",
        "core_identity",
        "Sponsor",
        "Quem é o dono da decisão final sobre este projeto?",
        [
            opt("single_sponsor", "Uma pessoa só decide", {"governance_load": 0}),
            opt("sponsor_with_delegate", "Uma pessoa decide, mas alguém cuida do dia a dia", {"governance_load": 1}),
            opt("shared_sponsorship", "Duas áreas ou pessoas decidem juntas", {"governance_load": 2}),
            opt("sponsor_open", "Ainda não está claro quem decide", {"governance_load": 2, "clarity_risk": 1}),
        ],
    ),
    q(
        "approvers",
        "Motor Inicial",
        "core_identity",
        "Aprovadores",
        "Quem precisa dar o 'ok' para o projeto andar (dinheiro, segurança, lançamento)?",
        [
            opt("single_chain", "Uma pessoa só libera tudo", {"governance_load": 0}),
            opt("split_chain", "Quem cuida do produto e quem cuida do dinheiro aprovam separados", {"governance_load": 1}),
            opt("formal_committee", "Tem um comitê ou várias pessoas para aprovar", {"governance_load": 2}),
            opt("regulated_gate", "Tem aprovação jurídica ou de regras obrigatórias", {"governance_load": 2, "security_need": 1}),
        ],
    ),
    q(
        "problem",
        "Motor Inicial",
        "core_problem_value",
        "Problema central",
        "Qual problema de verdade você quer resolver?",
        [
            opt("local_efficiency_pain", "Um incômodo pequeno no dia a dia", {"problem_pressure": 0}),
            opt("recurring_loss", "Perco tempo ou dinheiro de novo e de novo", {"problem_pressure": 1}),
            opt("strategic_blocker", "Isso trava o crescimento do negócio", {"problem_pressure": 2}),
            opt("critical_operation_risk", "Isso põe em risco algo que não pode parar", {"problem_pressure": 2, "ops_need": 1}),
        ],
    ),
    q(
        "expected_outcome",
        "Motor Inicial",
        "core_problem_value",
        "Resultado esperado",
        "O que precisa mudar para você considerar que deu certo?",
        [
            opt("localized_improvement", "Uma melhoria pequena e bem clara", {"clarity_risk": 0}),
            opt("new_operating_flow", "Uma nova forma de trabalhar para uma equipe", {"scope_load": 1}),
            opt("cross_area_change", "Uma mudança que afeta várias áreas", {"scope_load": 2, "governance_load": 1}),
            opt("market_or_revenue_shift", "Algo ligado a vender mais ou alcançar mais gente", {"scope_load": 2, "frontend_need": 1}),
        ],
    ),
    q(
        "urgency",
        "Motor Inicial",
        "core_problem_value",
        "Urgência",
        "Por que isso precisa acontecer agora?",
        [
            opt("planned_window", "Tem um bom momento, mas sem pressa", {"delivery_pressure": 0}),
            opt("managerial_priority", "Virou prioridade deste período", {"delivery_pressure": 1}),
            opt("fixed_deadline", "Tem uma data marcada ou compromisso com alguém", {"delivery_pressure": 2}),
            opt("active_incident", "Já está doendo agora ou é um risco imediato", {"delivery_pressure": 2, "ops_need": 1}),
        ],
    ),
    q(
        "success_metric",
        "Motor Inicial",
        "core_problem_value",
        "Métrica de sucesso",
        "Como você vai saber, na prática, que deu certo?",
        [
            opt("single_clear_metric", "Tem um número ou sinal principal para acompanhar", {"quality_need": 0}),
            opt("small_metric_set", "Tem poucos números para acompanhar", {"quality_need": 1}),
            opt("cross_area_kpis", "Tem números de mais de uma área", {"quality_need": 1, "governance_load": 1}),
            opt("metric_not_closed", "Ainda preciso definir como medir", {"clarity_risk": 2}),
        ],
    ),
    q(
        "value_hypothesis",
        "Motor Inicial",
        "core_problem_value",
        "Hipótese de valor",
        "Qual é o maior ganho que você espera com isso?",
        [
            opt("efficiency_gain", "Ganhar tempo e fazer as coisas mais rápido", {"problem_pressure": 0}),
            opt("risk_reduction", "Diminuir um risco ou evitar um problema", {"security_need": 1, "ops_need": 1}),
            opt("revenue_growth", "Vender mais ou conquistar mais clientes", {"frontend_need": 1}),
            opt("mixed_value_case", "Um pouco de cada: tempo, risco e crescimento", {"scope_load": 1, "governance_load": 1}),
        ],
    ),
    # Consolida `business_context`: "quem usa" e "onde isso se encaixa"
    # descreviam o mesmo publico por dois angulos, e ambas resolviam
    # `users.audience_and_scale`. As opcoes cruzam perfil de acesso com alcance
    # organizacional, preservando `scope_load` e `governance_load`, que eram
    # exclusivos de `business_context`.
    q(
        "primary_users",
        "Motor Inicial",
        "core_users_process",
        "Usuários e alcance",
        "Quem vai usar isso, e em que parte do negócio se encaixa?",
        [
            opt("single_profile", "Um tipo de pessoa, numa equipe pequena", {"access_load": 0, "scope_load": 0}),
            opt("two_key_profiles", "Dois tipos principais de pessoas, num setor ou área", {"access_load": 1, "scope_load": 1}),
            # Sem `governance_load`: a carga de governanca do alcance
            # organizacional ja vem de `audience_model` (`multi_area`,
            # `corporate`, `multi_tenant`). Mante-la aqui puniria quem tem
            # muitos perfis dentro de uma unica area -- combinacao que a fusao
            # com `business_context` deixou de distinguir.
            opt("multi_role_operation", "Vários perfis: quem usa, quem aprova, quem só consulta", {"access_load": 2, "scope_load": 2}),
            opt("public_plus_internal", "Clientes de fora, além da equipe interna", {"access_load": 2, "scope_load": 2, "frontend_need": 1}),
        ],
    ),
    # `critical_flows` foi consolidado em `mvp_scope`: perguntava "quais as
    # tarefas mais importantes" e media exatamente o mesmo eixo (`scope_load`
    # 0-2) que `product_objective` e `mvp_scope`. Eram tres formulacoes da
    # pergunta "quao grande e isto", feitas em todas as rotas.
    q(
        "current_process",
        "Motor Inicial",
        "core_users_process",
        "Processo atual",
        "Como você faz isso hoje, sem o app?",
        [
            opt("manual_process", "Tudo na mão, no improviso", {"problem_pressure": 1}),
            opt("spreadsheet_plus_tools", "Com planilhas e ferramentas soltas", {"problem_pressure": 1, "integration_need": 1}),
            opt("legacy_system_flow", "Com um sistema antigo que já existe", {"integration_need": 1, "continuity_need": 1}),
            opt("already_platformized", "Já tem um sistema, mas ele atrapalha", {"low_code_need": 1, "scope_load": 1}),
        ],
    ),
    q(
        "bottlenecks",
        "Motor Inicial",
        "core_users_process",
        "Gargalos e exceções",
        "Onde isso costuma travar, atrasar ou dar retrabalho hoje?",
        [
            opt("sporadic_friction", "Trava de vez em quando, nada grave", {"problem_pressure": 0}),
            opt("frequent_rework", "Tenho que refazer coisas com frequência", {"problem_pressure": 1}),
            opt("exception_heavy", "Vive cheio de exceções e casos especiais", {"scope_load": 1, "quality_need": 1}),
            opt("failure_causes_business_loss", "Quando falha, já causa prejuízo de verdade", {"problem_pressure": 2, "ops_need": 1}),
        ],
    ),
    # Consolida `product_objective`, `critical_flows` e o `mvp_scope` original.
    # As tres perguntavam a mesma coisa por angulos diferentes -- objetivo,
    # tarefas e recorte -- e todas graduavam `scope_load` de 0 a 2. Os sinais
    # secundarios exclusivos de cada uma (`integration_need` dos fluxos que
    # cruzam sistemas, `frontend_need` da jornada de cliente, `clarity_risk` do
    # escopo em aberto) estao preservados nas opcoes abaixo.
    q(
        "mvp_scope",
        "Motor Inicial",
        "core_scope_constraints",
        "Escopo da primeira versão",
        "O que a primeira versão precisa entregar para já valer a pena?",
        [
            opt("single_job_to_be_done", "Uma tarefa principal, bem definida", {"scope_load": 0}),
            opt("few_related_flows", "Poucas tarefas ligadas entre si, num caminho enxuto", {"scope_load": 1}),
            opt("cross_module_flows", "Tarefas que atravessam várias partes do sistema ou outros sistemas", {"scope_load": 2, "integration_need": 1}),
            opt("transactional_journey", "Uma jornada completa para o cliente final, como uma compra ou um pedido", {"scope_load": 2, "frontend_need": 1}),
            opt("scope_not_closed", "Bastante coisa de uma vez, e ainda estou decidindo o que entra", {"scope_load": 2, "clarity_risk": 1}),
        ],
    ),
    q(
        "non_scope",
        "Motor Inicial",
        "core_scope_constraints",
        "Não escopo",
        "O que você já decidiu deixar de fora por enquanto?",
        [
            opt("explicit_non_scope", "Já está claro o que fica de fora", {"clarity_risk": 0}),
            opt("partially_defined_non_scope", "Sei mais ou menos o que fica de fora", {"clarity_risk": 1}),
            opt("non_scope_contested", "Ainda discutimos o que fica de fora", {"clarity_risk": 2, "scope_load": 1}),
            opt("everything_feels_in_scope", "Parece que tudo precisa entrar", {"clarity_risk": 2, "scope_load": 2}),
        ],
    ),
    q(
        "deadline",
        "Motor Inicial",
        "core_scope_constraints",
        "Prazo",
        "Existe uma data ou prazo importante para entregar?",
        [
            opt("flexible_timeline", "Sem prazo apertado", {"delivery_pressure": 0}),
            opt("target_window", "Tem um prazo desejado, mas dá para negociar", {"delivery_pressure": 1}),
            opt("fixed_business_date", "Tem uma data fixa do negócio", {"delivery_pressure": 2}),
            opt("external_or_regulatory_date", "Tem uma data de fora ou exigida por lei", {"delivery_pressure": 2, "governance_load": 1}),
        ],
        detail_schema={
            "fields": [
                {"key": "date", "type": "date", "label": "Qual é a data?"},
                {"key": "reason", "type": "text", "label": "Por que essa data?"},
            ]
        },
    ),
    q(
        "constraints",
        "Motor Inicial",
        "core_scope_constraints",
        "Capacidade e restrições",
        "Quais limites você já tem (equipe, dinheiro, ferramentas que é obrigado a usar)?",
        [
            opt("low_constraint", "Poucos limites, e bem conhecidos", {"dependency_load": 0}),
            opt("team_or_budget_cap", "Tenho um limite claro de equipe ou dinheiro", {"dependency_load": 1}),
            opt("stack_or_vendor_lock", "Sou obrigado a usar uma certa ferramenta ou fornecedor", {"dependency_load": 2}),
            opt("multi_constraint_scenario", "Vários limites ao mesmo tempo, brigando entre si", {"dependency_load": 2, "governance_load": 1}),
        ],
    ),
    q(
        "external_dependencies",
        "Motor Inicial",
        "core_scope_constraints",
        "Dependências externas",
        "O projeto depende de outras empresas, sistemas ou aprovações de fora?",
        [
            opt("independent", "Quase não dependo de ninguém de fora", {"dependency_load": 0}),
            opt("few_dependencies", "Dependo de poucos terceiros ou aprovações", {"dependency_load": 1}),
            opt("many_dependencies", "Dependo de vários sistemas ou parceiros de fora", {"dependency_load": 2, "integration_need": 1}),
            opt("hard_external_gate", "Tem algo de fora que pode travar a entrega", {"dependency_load": 2, "delivery_pressure": 1}),
        ],
    ),
    q(
        "scope_target",
        "Motor Inicial",
        "core_scope_constraints",
        "Alvo do blueprint",
        "Este plano deve cobrir só a primeira versão útil do produto ou já a versão completa?",
        [
            opt("mvp_first", "Só a primeira versão, bem enxuta", {"scope_load": 0}),
            opt("mvp_then_iterate", "Primeira versão agora, melhorias em etapas depois", {"scope_load": 0, "delivery_pressure": 1}),
            opt("mvp_plus_near_roadmap", "Primeira versão e os próximos passos já no plano", {"scope_load": 1, "delivery_pressure": 1}),
            opt("full_version", "Já quero o plano da versão completa", {"scope_load": 2, "delivery_pressure": 2}),
        ],
        detail_hint="Isso não acrescenta mais perguntas. Só decide se o plano final abre uma seção extra de 'versão completa' quando você quer ir além da primeira versão.",
    ),
    q(
        "access_profile",
        "Motor Inicial",
        "core_data_access",
        "Perfil de acesso",
        "As pessoas vão ter níveis diferentes de acesso (ex: quem manda, quem aprova, quem só vê)?",
        [
            opt("single_access_level", "Não, todo mundo tem o mesmo acesso", {"access_load": 0}),
            opt("basic_roles", "Tem poucos níveis, bem definidos", {"access_load": 1}),
            opt("segregated_roles", "Tem uma separação clara de quem faz o quê", {"access_load": 2, "security_need": 1}),
            opt("privileged_or_audit_roles", "Tem acessos especiais ou alguém que fiscaliza", {"access_load": 2, "security_need": 2}),
        ],
    ),
    q(
        "handled_data",
        "Motor Inicial",
        "core_data_access",
        "Dados manipulados",
        "Que tipo de informação o app vai guardar ou usar?",
        [
            opt("reference_data", "Informações simples de cadastro", {"security_need": 0}),
            opt("operational_data", "Dados do dia a dia do negócio", {"security_need": 1}),
            opt("customer_or_financial_data", "Dados de clientes, vendas ou dinheiro", {"security_need": 2, "frontend_need": 1}),
            opt("sensitive_regulated_data", "Dados sensíveis ou pessoais, protegidos por lei", {"security_need": 2, "quality_need": 1}),
        ],
    ),
    # `data_sensitivity` foi removida: era subconjunto exato de `handled_data`.
    # Perguntava "esses dados sao delicados?" logo depois de a pessoa ja ter
    # escolhido entre "cadastro simples" e "dados protegidos por lei", e
    # graduava o mesmo `security_need` 0-2 sem nenhum sinal exclusivo.
    q(
        "data_loss_impact",
        "Motor Inicial",
        "core_data_access",
        "Impacto de perda",
        "O que acontece se essas informações se perderem ou ficarem fora do ar?",
        [
            opt("low_impact", "Pouco impacto, dá para recuperar fácil", {"continuity_need": 0}),
            opt("moderate_impact", "Atrapalha, mas tem como contornar", {"continuity_need": 1, "ops_need": 1}),
            opt("high_impact", "Para a operação ou o faturamento", {"continuity_need": 2, "ops_need": 2}),
            opt("legal_or_trust_impact", "Vira problema legal ou quebra a confiança", {"continuity_need": 2, "security_need": 1}),
        ],
    ),
    q(
        "basic_compliance",
        "Motor Inicial",
        "core_data_access",
        "Compliance básico",
        "Existe alguma regra de lei ou contrato que você precisa cumprir?",
        [
            opt("no_formal_compliance", "Não, nada formal", {"security_need": 0}),
            opt("client_or_contract_requirement", "Sim, uma exigência de contrato ou de cliente", {"security_need": 1, "governance_load": 1}),
            opt("regulated_requirement", "Sim, uma exigência de lei ou órgão regulador", {"security_need": 2, "governance_load": 1}),
            opt("audited_requirement", "Sim, e ainda passa por fiscalização ou auditoria", {"security_need": 2, "quality_need": 1}),
        ],
    ),
    q(
        "main_risks",
        "Motor Inicial",
        "core_data_access",
        "Riscos principais",
        "O que mais te preocupa que possa dar errado?",
        [
            opt("delivery_risk", "Não conseguir entregar no prazo", {"delivery_pressure": 1}),
            opt("operational_risk", "O sistema falhar no dia a dia", {"ops_need": 2}),
            opt("security_risk", "Vazar dados ou ter uma falha de segurança", {"security_need": 2}),
            opt("multi_risk_surface", "Tenho várias preocupações ao mesmo tempo", {"ops_need": 1, "security_need": 1, "delivery_pressure": 1}),
        ],
    ),
    q(
        "delivery_type",
        "Classificadores",
        "classifier_block",
        "Tipo de entrega",
        "Qual frase descreve melhor o que você quer criar?",
        [
            opt("design_discovery", "Ainda estou testando a ideia (protótipo ou validação)", {"clarity_risk": 1}, "design_discovery"),
            opt("internal_tool", "Uma ferramenta para uso interno da equipe", {"frontend_need": 0}, "internal_tool"),
            opt("business_system", "Um sistema para fazer o negócio funcionar", {"scope_load": 1}, "business_system"),
            opt("commerce_experience", "Algo para vender, mostrar catálogo ou ter uma loja", {"frontend_need": 2, "integration_need": 1}, "commerce_experience"),
            opt("critical_system", "Algo que não pode parar de jeito nenhum", {"ops_need": 2, "security_need": 1}, "critical_system"),
        ],
        classifier_field="delivery_type",
        block_type="classifier",
    ),
    q(
        "interaction_model",
        "Classificadores",
        "classifier_block",
        "Modelo principal de interação",
        "Como as pessoas (ou outros sistemas) vão usar isso no dia a dia?",
        [
            opt("ui_rich", "Por telas bonitas e completas, bem visuais", {"frontend_need": 2}, "ui_rich"),
            opt("backoffice_simple", "Por telas internas simples, para a equipe", {"frontend_need": 1}, "backoffice_simple"),
            opt("api_service", "Sem telas: outro programa conversa com o seu automaticamente", {"integration_need": 2}, "api_service"),
            # Absorve o antigo `platform_style`: automacao em sequencia e a rota
            # que de fato leva a montagem visual/low-code, e passa a ser a fonte
            # forte de `low_code_need` que sustenta o overlay.
            opt("workflow_automation", "Por automações que rodam sozinhas, em sequência (montadas em ferramenta visual ou programadas)", {"integration_need": 1, "low_code_need": 2}, "workflow_automation"),
            opt("mixed", "Um pouco de cada", {"frontend_need": 1, "integration_need": 1}, "mixed"),
        ],
        classifier_field="interaction_model",
        block_type="classifier",
    ),
    q(
        "runtime",
        "Classificadores",
        "classifier_block",
        "Onde roda e com qual conexão",
        "Onde isso vai funcionar, e como vai ser a conexão com a internet?",
        [
            # Absorve o antigo `connectivity_profile`: conectividade nunca foi
            # independente do lugar onde o sistema roda -- cada valor abaixo ja
            # implica um regime de conexao, e carrega os sinais dos dois campos.
            opt("local", "No próprio computador da pessoa, com internet disponível", {"continuity_need": 0}, "local"),
            opt("offline_first", "No computador ou celular da pessoa, funcionando mesmo sem internet e sincronizando depois", {"continuity_need": 1}, "offline_first"),
            opt("on_prem", "Nos servidores da própria empresa, em rede interna fechada", {"ops_need": 3, "security_need": 2}, "on_prem"),
            opt("cloud", "Na internet (nuvem), acessível de qualquer lugar", {"ops_need": 1}, "cloud"),
            opt("hybrid", "Uma parte na empresa e outra na internet", {"ops_need": 2, "integration_need": 1}, "hybrid"),
        ],
        classifier_field="runtime",
        block_type="classifier",
    ),
    q(
        "audience_model",
        "Classificadores",
        "classifier_block",
        "Público e isolamento",
        "Quem vai usar, e os dados precisam ficar separados por cliente ou unidade?",
        [
            # Absorve o antigo `tenant_model`: escala e isolamento sempre
            # resolveram a mesma decisao (`users.audience_and_scale`), e eram
            # perguntados em sequencia como se fossem independentes.
            opt("individual", "Só eu, ou uma pessoa", {"scope_load": 0}, "individual"),
            opt("small_team", "Uma equipe pequena, tudo junto", {"scope_load": 0}, "small_team"),
            opt("multi_area", "Várias áreas da empresa, cada uma com seus dados", {"scope_load": 1, "governance_load": 1, "tenant_need": 1}, "multi_area"),
            opt("corporate", "A empresa inteira, muita gente", {"scope_load": 2, "governance_load": 2, "tenant_need": 1}, "corporate"),
            opt("multi_tenant", "Vários clientes diferentes, cada um vendo só os seus dados", {"scope_load": 2, "governance_load": 2, "tenant_need": 2, "security_need": 1}, "multi_tenant"),
        ],
        classifier_field="audience_model",
        block_type="classifier",
    ),
    q(
        "integration_intensity",
        "Classificadores",
        "classifier_block",
        "Intensidade de integrações",
        "Vai precisar conectar com outros sistemas (ex: pagamento, planilha, e-mail)?",
        [
            opt("none", "Não, funciona sozinho", {"integration_need": 0}, "none"),
            opt("few", "Sim, poucas conexões", {"integration_need": 1}, "few"),
            opt("many", "Sim, muitas conexões", {"integration_need": 2}, "many"),
        ],
        classifier_field="integration_intensity",
        block_type="classifier",
    ),
    q(
        "data_risk",
        "Classificadores",
        "classifier_block",
        "Risco dos dados",
        "Se um dado vazar ou se perder, o estrago seria...?",
        [
            opt("low", "Pequeno", {"security_need": 0}, "low"),
            opt("medium", "Médio", {"security_need": 1}, "medium"),
            opt("high", "Grande", {"security_need": 2}, "high"),
        ],
        classifier_field="data_risk",
        block_type="classifier",
    ),
    # `operational_criticality` foi removido como classificador: era uma
    # auto-avaliacao abstrata ("pequeno/medio/grande") que duplicava o que a
    # rota ja sabe. A criticidade agora vem declarada por `delivery_type =
    # critical_system` e medida por `ops_need`, que o nucleo alimenta a partir
    # de fatos concretos (`data_loss_impact`, `flow_criticality`, `main_risks`,
    # `continuity_owner`, `backup_restore`) ate 13 pontos -- muito acima do
    # gatilho 4 das regras que ele governava.
    q(
        "ai_usage",
        "Classificadores",
        "classifier_block",
        "Uso de IA",
        "Você quer usar inteligência artificial neste projeto?",
        [
            opt("none", "Não, sem IA", {"ai_need": 0}, "none"),
            opt("assistive", "Sim, só para ajudar e sugerir", {"ai_need": 1}, "assistive"),
            opt("automated_with_hitl", "Sim, fazendo tarefas, mas com uma pessoa revisando antes de valer", {"ai_need": 2, "ops_need": 1}, "automated_with_hitl"),
        ],
        classifier_field="ai_usage",
        block_type="classifier",
    ),
    # `tenant_model` foi absorvido por `audience_model` (acima): as duas
    # perguntas resolviam a mesma decisao `users.audience_and_scale`.
    #
    # `platform_style` foi absorvido por `interaction_model`: "como vai ser
    # construido" e uma escolha de implementacao que o entrevistado raramente
    # sabe responder no inicio, e cujo unico efeito era o overlay
    # `low_code_workflow` -- agora governado por `interaction_model =
    # workflow_automation` ou por `low_code_need >= 2`.
    q(
        "use_cases",
        "Motor Final",
        "core_final_product",
        "Casos de uso",
        "Quais funções precisam existir para a primeira versão já funcionar de verdade?",
        [
            opt("single_use_case", "Uma função principal bem definida", {"scope_load": 0}),
            opt("few_use_cases", "Poucas funções que se completam", {"scope_load": 1}),
            opt("many_use_cases", "Várias funções já na primeira versão", {"scope_load": 2}),
            opt("use_cases_still_open", "Ainda não fechei quais funções entram", {"clarity_risk": 2}),
        ],
    ),
    q(
        "flow_criticality",
        "Motor Final",
        "core_final_product",
        "Criticidade por fluxo",
        "Entre as tarefas do app, quais são realmente essenciais e quais são só 'bom ter'?",
        [
            opt("single_critical_flow", "Uma tarefa é essencial, o resto é extra", {"ops_need": 0}),
            opt("few_critical_flows", "Poucas tarefas claramente essenciais", {"ops_need": 1}),
            opt("many_critical_flows", "Várias tarefas essenciais ao mesmo tempo", {"ops_need": 2}),
            opt("criticality_not_ranked", "Ainda não ordenei o que é essencial", {"clarity_risk": 1, "ops_need": 1}),
        ],
    ),
    q(
        "business_rules",
        "Motor Final",
        "core_final_product",
        "Regras de negócio",
        "Quais regras o app nunca pode quebrar (ex: não vender sem ter em estoque)?",
        [
            opt("light_rules", "Poucas regras e simples", {"quality_need": 0}),
            opt("moderate_rules", "Algumas regras importantes, mas tranquilas", {"quality_need": 1}),
            opt("strict_rules", "Muitas regras e bem rígidas", {"quality_need": 2}),
            opt("regulated_rules", "Tem regra de lei, contrato ou imposto envolvida", {"quality_need": 2, "security_need": 1}),
        ],
    ),
    q(
        "permissions",
        "Motor Final",
        "core_final_product",
        "Permissões",
        "Cada tipo de pessoa vai poder fazer coisas diferentes (ver, criar, editar, aprovar)?",
        [
            opt("simple_permissions", "Permissões simples por tipo de pessoa", {"access_load": 0}),
            opt("role_matrix", "Uma tabela de quem pode fazer o quê", {"access_load": 1}),
            opt("granular_permissions", "Permissões detalhadas para cada ação", {"access_load": 2, "security_need": 1}),
            opt("approval_and_export_controls", "Tem aprovação e exportação de dados sensíveis", {"access_load": 2, "security_need": 2}),
        ],
    ),
    # Consolida `data_model` em `modules`: as duas mediam o tamanho estrutural
    # do sistema -- blocos de funcionalidade e tipos de informacao crescem
    # juntos -- e eram as duas unicas fontes de `tenant_need` no nucleo. A opcao
    # mais pesada carrega `tenant_need: 2` (a soma das duas originais) para que
    # o overlay `multi_tenant` continue alcancavel pelo nucleo, sem depender de
    # `audience_model = multi_tenant`.
    q(
        "modules",
        "Motor Final",
        "core_final_architecture",
        "Módulos e informações",
        "Em quais grandes partes o app se divide, e quantos tipos de informação ele organiza?",
        [
            opt("few_modules", "Poucos blocos e poucos tipos de informação", {"scope_load": 0, "quality_need": 0}),
            opt("moderate_modules", "Alguns blocos bem definidos, com informações ligadas entre si", {"scope_load": 1, "quality_need": 1}),
            opt("many_modules", "Muitos blocos, com informações cheias de ligações e histórico", {"scope_load": 2, "quality_need": 2}),
            opt("platform_like_shape", "Tantas partes que parece uma plataforma, com dados separados por cliente ou área", {"scope_load": 2, "quality_need": 2, "tenant_need": 2}),
        ],
    ),
    q(
        "minimal_audit",
        "Motor Final",
        "core_final_architecture",
        "Auditoria mínima",
        "Quais ações precisam ficar registradas (quem fez, o quê e quando)?",
        [
            opt("light_history", "Só um histórico básico", {"quality_need": 0}),
            opt("selected_audit", "Algumas ações precisam de registro", {"quality_need": 1, "security_need": 1}),
            opt("strong_audit", "Muitas ações precisam de registro completo", {"quality_need": 2, "security_need": 1}),
            opt("formal_audit_evidence", "O registro precisa servir como prova oficial", {"quality_need": 2, "security_need": 2}),
        ],
    ),
    q(
        "base_integrations",
        "Motor Final",
        "core_final_architecture",
        "Integrações base",
        "Quais conexões com outros sistemas já estão certas que vão existir?",
        [
            opt("no_base_integrations", "Quase nenhuma confirmada", {"integration_need": 0}),
            opt("few_base_integrations", "Poucas confirmadas", {"integration_need": 1}),
            opt("many_base_integrations", "Muitas já na primeira versão", {"integration_need": 2}),
            opt("platform_critical_integrations", "As conexões são o que tornam o app possível", {"integration_need": 2, "dependency_load": 1}),
        ],
    ),
    q(
        "output_directory",
        "Motor Final",
        "core_final_architecture",
        "Diretório de saída",
        "Onde os arquivos finais gerados devem ser salvos no computador?",
        [
            opt("fixed_workspace_path", "Numa pasta fixa, sempre a mesma", {"clarity_risk": 0}),
            opt("project_subfolder", "Numa subpasta dedicada do projeto", {"clarity_risk": 0}),
            opt("chosen_per_run", "Escolho o lugar a cada vez", {"clarity_risk": 1}),
            opt("client_managed_path", "Depende da pasta do cliente ou do ambiente", {"clarity_risk": 1, "dependency_load": 1}),
        ],
    ),
    q(
        "authentication",
        "Motor Final",
        "core_final_security_min",
        "Autenticação",
        "Como as pessoas vão entrar (fazer login) no app?",
        [
            opt("simple_auth", "Login simples, com usuário e senha", {"security_need": 0}),
            opt("managed_auth", "Login por um serviço pronto (ex: entrar com o Google)", {"security_need": 1}),
            opt("enterprise_auth", "Com o mesmo login que já usam na empresa", {"security_need": 2}),
            opt("multi_actor_auth", "Pessoas e outros sistemas entram de formas diferentes", {"security_need": 2, "access_load": 1}),
        ],
    ),
    q(
        "authorization",
        "Motor Final",
        "core_final_security_min",
        "Autorização",
        "Como você vai controlar o que cada pessoa pode fazer depois de entrar?",
        [
            opt("coarse_roles", "Poucos perfis amplos já bastam", {"security_need": 0}),
            opt("role_based_control", "Permissões por perfil e por área", {"security_need": 1}),
            opt("fine_grained_control", "Controle detalhado por ação ou por item", {"security_need": 2}),
            opt("policy_and_approval_control", "Depende de regras e de aprovação", {"security_need": 2, "governance_load": 1}),
        ],
    ),
    q(
        "secrets",
        "Motor Final",
        "core_final_security_min",
        "Segredos",
        "Como você vai guardar com segurança as senhas e chaves de acesso do sistema?",
        [
            opt("few_local_secrets", "Poucas, guardadas de forma simples", {"security_need": 0}),
            opt("managed_secret_store", "Num cofre ou serviço próprio para isso", {"security_need": 1}),
            opt("rotated_and_scoped_secrets", "Trocadas de tempos em tempos e separadas por ambiente", {"security_need": 2}),
            opt("high_assurance_secret_model", "Com controle rígido e regras fortes", {"security_need": 2, "governance_load": 1}),
        ],
    ),
    q(
        "retention",
        "Motor Final",
        "core_final_security_min",
        "Retenção mínima",
        "Por quanto tempo as informações e os registros precisam ser guardados?",
        [
            opt("short_retention", "Pouco tempo, só o necessário", {"continuity_need": 0}),
            opt("standard_retention", "Um tempo padrão do negócio", {"continuity_need": 1}),
            opt("long_retention", "Bastante tempo, por necessidade interna", {"continuity_need": 2}),
            opt("regulated_retention", "Bastante tempo, por exigência de fora", {"continuity_need": 2, "security_need": 1}),
        ],
    ),
    q(
        "test_strategy",
        "Motor Final",
        "core_final_quality",
        "Estratégia mínima de testes",
        "Antes de lançar uma nova versão, quanto de teste você quer fazer?",
        [
            opt("basic_manual_checks", "Só conferir na mão se está funcionando", {"quality_need": 0}),
            opt("core_automated_tests", "Alguns testes automáticos das partes principais", {"quality_need": 1}),
            opt("broad_test_stack", "Vários níveis de teste antes de lançar", {"quality_need": 2}),
            opt("regulated_validation", "Testes que geram prova formal de qualidade", {"quality_need": 2, "security_need": 1}),
        ],
    ),
    q(
        "definition_of_done",
        "Motor Final",
        "core_final_quality",
        "Definition of Done",
        "Quando você considera que uma função está 'pronta'?",
        [
            opt("light_dod", "Quando funciona, está pronta", {"quality_need": 0}),
            opt("team_dod", "Quando passou por revisão, teste e o ok da equipe", {"quality_need": 1}),
            opt("formal_release_dod", "Quando passou por aprovações formais de lançamento", {"quality_need": 2, "governance_load": 1}),
            opt("compliance_dod", "Quando tem prova e cumpre as regras exigidas", {"quality_need": 2, "security_need": 1}),
        ],
    ),
    q(
        "acceptance_criteria",
        "Motor Final",
        "core_final_quality",
        "Critérios de aceite",
        "Como você vai confirmar que cada tarefa importante faz o que deveria?",
        [
            opt("simple_acceptance", "Mostrando funcionando, numa demonstração", {"quality_need": 0}),
            opt("scenario_acceptance", "Testando situações combinadas antes", {"quality_need": 1}),
            opt("cross_area_acceptance", "Com o ok de mais de uma área", {"quality_need": 2, "governance_load": 1}),
            opt("external_acceptance", "Com o ok de cliente, auditoria ou regulador", {"quality_need": 2, "dependency_load": 1}),
        ],
    ),
    q(
        "backup_restore",
        "Motor Final",
        "core_final_continuity",
        "Backup e restauração",
        "O que precisa ter cópia de segurança (backup), e como testar se ela funciona?",
        [
            opt("basic_backup", "Backup simples, de vez em quando", {"continuity_need": 0}),
            opt("defined_backup", "Backup definido, com restauração só quando precisar", {"continuity_need": 1}),
            opt("validated_restore", "A restauração é testada de tempos em tempos", {"continuity_need": 2}),
            opt("strict_recovery_objectives", "Backup segue metas rígidas de recuperação", {"continuity_need": 2, "ops_need": 1}),
        ],
    ),
    q(
        "update_strategy",
        "Motor Final",
        "core_final_continuity",
        "Estratégia de atualização",
        "Como as novas versões vão chegar até quem usa?",
        [
            opt("manual_light_updates", "Atualização simples e manual", {"continuity_need": 0}),
            opt("planned_release_cycle", "Num ciclo planejado de lançamentos", {"continuity_need": 1}),
            opt("controlled_rollout", "Liberada aos poucos, com conferência", {"continuity_need": 2}),
            opt("change_managed_release", "Com gestão formal de mudança", {"continuity_need": 2, "governance_load": 1}),
        ],
    ),
    q(
        "continuity_owner",
        "Motor Final",
        "core_final_continuity",
        "Owner de continuidade",
        "Depois que estiver no ar, quem vai cuidar, corrigir e manter o app funcionando?",
        [
            opt("single_team_owner", "Uma equipe pequena cuida de tudo", {"ops_need": 0}),
            opt("team_plus_support", "A equipe do produto, com um suporte definido", {"ops_need": 1}),
            opt("formal_operations", "Tem uma equipe de operação ou suporte formal", {"ops_need": 2}),
            opt("multi_party_support", "Vários atores dividem essa responsabilidade", {"ops_need": 2, "dependency_load": 1}),
        ],
    ),
    q(
        "artifacts_expected",
        "Motor Final",
        "preset_design_discovery_service",
        "Artefatos esperados",
        "Qual é o resultado principal que você espera desta fase de testar a ideia?",
        [
            opt("single_artifact", "Um entregável principal já basta", {"clarity_risk": 0}),
            opt("artifact_pack", "Um pacotinho de entregáveis que se completam", {"clarity_risk": 1}),
            opt("prototype_plus_decision_pack", "Um protótipo junto com uma recomendação organizada", {"clarity_risk": 1, "frontend_need": 1}),
            opt("multi_workstream_artifacts", "Entregáveis de várias frentes de investigação", {"clarity_risk": 2, "scope_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "discovery_method",
        "Motor Final",
        "preset_design_discovery_service",
        "Método de discovery",
        "Como você vai investigar a ideia com as pessoas?",
        [
            opt("single_method", "Um jeito principal, como conversar com pessoas", {"clarity_risk": 0}),
            opt("few_methods", "Poucos jeitos combinados", {"clarity_risk": 1}),
            opt("multi_method_research", "Vários jeitos de pesquisa juntos", {"clarity_risk": 2, "quality_need": 1}),
            opt("field_and_user_testing", "Observando na prática e testando com usuários", {"clarity_risk": 2, "frontend_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "transition_criteria",
        "Motor Final",
        "preset_design_discovery_service",
        "Critério de transição",
        "O que precisa estar decidido para parar de testar a ideia e começar a construir?",
        [
            opt("light_transition", "Um sinal simples de que pode ir", {"clarity_risk": 0}),
            opt("defined_checklist", "Uma listinha de decisões a bater", {"clarity_risk": 1, "governance_load": 1}),
            opt("formal_go_no_go", "Uma aprovação formal de vai/não vai", {"clarity_risk": 1, "governance_load": 2}),
            opt("budget_and_scope_gate", "Depende de orçamento e escopo aprovados", {"clarity_risk": 2, "governance_load": 2}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_installation",
        "Motor Final",
        "preset_local_offline_tool",
        "Instalação local",
        "Como o programa vai ser instalado no computador?",
        [
            opt("single_machine_install", "Instalação simples, numa máquina", {"continuity_need": 0}),
            opt("guided_local_install", "Instalação guiada, com poucos passos", {"continuity_need": 1}),
            opt("managed_rollout", "A TI local é quem instala", {"continuity_need": 1, "governance_load": 1}),
            opt("locked_down_environment", "Num computador bem travado e controlado", {"continuity_need": 2, "security_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_storage",
        "Motor Final",
        "preset_local_offline_tool",
        "Armazenamento local",
        "Onde os dados vão ficar guardados no próprio computador?",
        [
            opt("simple_files", "Em arquivos simples", {"continuity_need": 0}),
            opt("embedded_database", "Num banco de dados embutido no programa", {"continuity_need": 1}),
            opt("shared_local_store", "Num armazenamento local compartilhado", {"continuity_need": 1, "access_load": 1}),
            opt("sensitive_local_store", "Localmente, mas com proteção forte", {"continuity_need": 2, "security_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_update",
        "Motor Final",
        "preset_local_offline_tool",
        "Atualização",
        "Como as novas versões do programa vão chegar a quem usa?",
        [
            opt("manual_replace", "Trocando o arquivo na mão", {"continuity_need": 0}),
            opt("guided_update", "Com uma atualização guiada pelo próprio usuário", {"continuity_need": 1}),
            opt("centralized_distribution", "Distribuída a partir de um ponto central", {"continuity_need": 1, "governance_load": 1}),
            opt("controlled_patch_process", "Com controle formal de atualização", {"continuity_need": 2, "security_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_recovery",
        "Motor Final",
        "preset_local_offline_tool",
        "Recuperação",
        "Se o computador quebrar, como voltar a funcionar em outro?",
        [
            opt("simple_reinstall", "Basta reinstalar", {"continuity_need": 0}),
            opt("backup_and_restore", "Com backup local e restauração guiada", {"continuity_need": 1}),
            opt("transfer_between_devices", "Migrando de uma máquina para outra", {"continuity_need": 2}),
            opt("zero_loss_expectation", "Sem poder perder quase nada na troca", {"continuity_need": 2, "ops_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_topology",
        "Motor Final",
        "preset_local_small_team_app",
        "Topologia local",
        "O app vai rodar em uma máquina, numa rede local ou num servidor da unidade?",
        [
            opt("single_machine", "Numa máquina só", {"continuity_need": 0}),
            opt("small_lan", "Numa rede local pequena", {"continuity_need": 1}),
            opt("unit_server", "Num servidor simples do local", {"continuity_need": 1, "ops_need": 1}),
            opt("distributed_local_stack", "Em vários pontos locais coordenados", {"continuity_need": 2, "ops_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_concurrency",
        "Motor Final",
        "preset_local_small_team_app",
        "Concorrência",
        "Quantas pessoas vão mexer ao mesmo tempo, e o que fazer se duas editarem a mesma coisa?",
        [
            opt("low_concurrency", "Poucas ao mesmo tempo, sem conflito", {"quality_need": 0}),
            opt("moderate_concurrency", "Um número médio, previsível", {"quality_need": 1}),
            opt("high_local_concurrency", "Muitas ao mesmo tempo", {"quality_need": 2, "ops_need": 1}),
            opt("conflict_resolution_needed", "Já espero conflitos de edição para resolver", {"quality_need": 2, "continuity_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_rollout",
        "Motor Final",
        "preset_local_small_team_app",
        "Atualização local",
        "Como atualizar o app sem bagunçar o trabalho da equipe?",
        [
            opt("manual_quiet_update", "Atualização manual, em hora calma", {"continuity_need": 0}),
            opt("scheduled_update", "Atualização agendada com a equipe", {"continuity_need": 1}),
            opt("staged_rollout", "Liberada em etapas", {"continuity_need": 2}),
            opt("rollback_required", "Preciso poder voltar para a versão anterior se der errado", {"continuity_need": 2, "ops_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "api_contracts",
        "Motor Final",
        "preset_api_integration_service",
        "Contratos",
        "Como os sistemas vão combinar o formato dos dados que trocam entre si?",
        [
            opt("single_contract", "Um combinado principal e estável", {"integration_need": 1}),
            opt("few_contracts", "Poucos combinados coordenados", {"integration_need": 1, "quality_need": 1}),
            opt("many_contracts", "Muitos formatos e combinados", {"integration_need": 2, "quality_need": 1}),
            opt("evolving_contracts", "Esses combinados ainda vão mudar durante o projeto", {"integration_need": 2, "clarity_risk": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "technical_auth",
        "Motor Final",
        "preset_api_integration_service",
        "Autenticação técnica",
        "Como os outros sistemas vão provar que têm permissão para se conectar ao seu?",
        [
            opt("simple_service_secret", "Com uma senha simples por sistema", {"security_need": 0}),
            opt("managed_api_auth", "Com um controle de acesso pronto e gerenciado", {"security_need": 1}),
            opt("scoped_machine_identities", "Cada conexão com a sua própria identidade e limites", {"security_need": 2}),
            opt("regulated_machine_auth", "Com registro e aprovação obrigatórios", {"security_need": 2, "quality_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "failure_handling",
        "Motor Final",
        "preset_api_integration_service",
        "Falhas e retries",
        "O que o sistema deve fazer quando uma conexão falha ou demora demais?",
        [
            opt("basic_retries", "Tentar de novo algumas vezes já resolve", {"ops_need": 0}),
            opt("retry_and_timeout_policy", "Ter uma regra clara de tentar de novo e de tempo limite", {"ops_need": 1, "quality_need": 1}),
            opt("idempotent_and_partial_failure", "Garantir que repetir não duplique e tratar falha pela metade", {"ops_need": 2, "quality_need": 1}),
            opt("mission_critical_recovery", "Falhar aqui afeta algo que não pode parar", {"ops_need": 2, "continuity_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "contract_versioning",
        "Motor Final",
        "preset_api_integration_service",
        "Versionamento",
        "Quando o formato dos dados mudar, como controlar versões sem quebrar quem já usa?",
        [
            opt("informal_versioning", "Controle simples de versão", {"quality_need": 0}),
            opt("documented_versions", "Versões anotadas para cada combinado", {"quality_need": 1}),
            opt("compatibility_policy", "Uma regra de compatibilidade entre versões", {"quality_need": 2}),
            opt("governed_deprecation", "Aposentar versões exige aviso e governança", {"quality_need": 2, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "onprem_infra_owner",
        "Motor Final",
        "preset_onprem_business_system",
        "Infra local",
        "Quem cuida dos servidores, da rede, dos acessos e do backup dentro da empresa?",
        [
            opt("single_local_owner", "Tem um responsável local claro", {"ops_need": 1}),
            opt("infra_team_owner", "Tem uma equipe de infraestrutura dedicada", {"ops_need": 2}),
            opt("shared_ops_model", "A responsabilidade é dividida entre equipes", {"ops_need": 2, "governance_load": 1}),
            opt("client_or_third_party_ops", "Depende de um terceiro ou do cliente", {"ops_need": 2, "dependency_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_corporate_integration",
        "Motor Final",
        "preset_onprem_business_system",
        "Integração corporativa local",
        "A empresa tem regras de TI obrigatórias (login corporativo, pastas de rede, bloqueios de internet, firewall)?",
        [
            opt("minimal_local_policies", "Quase nenhuma regra obrigatória", {"integration_need": 1}),
            opt("some_corporate_controls", "Algumas regras corporativas", {"integration_need": 1, "security_need": 1}),
            opt("heavy_corporate_stack", "Login corporativo, bloqueios e firewall com regras fortes", {"integration_need": 2, "security_need": 2}),
            opt("strict_enterprise_controls", "Um ambiente corporativo muito restritivo", {"integration_need": 2, "security_need": 2, "ops_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "hardening_patching",
        "Motor Final",
        "preset_onprem_business_system",
        "Hardening e patching",
        "Como as atualizações de segurança dos servidores vão ser controladas?",
        [
            opt("basic_patch_cycle", "Atualizações de segurança básicas", {"security_need": 1}),
            opt("planned_hardening", "Reforço de segurança e atualizações planejados", {"security_need": 2}),
            opt("formal_change_cycle", "Toda mudança técnica passa por controle formal", {"security_need": 2, "governance_load": 1}),
            opt("strict_security_baseline", "Regras de segurança muito rígidas", {"security_need": 2, "ops_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "local_logs",
        "Motor Final",
        "preset_onprem_business_system",
        "Logs locais",
        "Onde ficam os registros de funcionamento (logs) e quem pode consultá-los?",
        [
            opt("basic_local_logs", "Registros locais simples", {"ops_need": 1}),
            opt("centralized_local_logs", "Registros centralizados no ambiente", {"ops_need": 2}),
            opt("restricted_access_logs", "O acesso aos registros é controlado", {"ops_need": 2, "security_need": 1}),
            opt("auditable_log_chain", "Os registros fazem parte da trilha de auditoria", {"ops_need": 2, "security_need": 2}),
        ],
        block_type="preset_block",
    ),
    q(
        "cloud_account_hosting",
        "Motor Final",
        "preset_cloud_business_app",
        "Conta e hospedagem",
        "Em qual conta ou ambiente na nuvem o app vai rodar?",
        [
            opt("single_cloud_space", "Uma conta simples", {"ops_need": 0}),
            opt("managed_cloud_space", "Uma conta com organização básica de ambientes", {"ops_need": 1}),
            opt("shared_cloud_governance", "Uma conta compartilhada, com regras de governança", {"ops_need": 1, "governance_load": 1}),
            opt("enterprise_cloud_landing_zone", "Um ambiente corporativo organizado da empresa", {"ops_need": 2, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "cloud_environments",
        "Motor Final",
        "preset_cloud_business_app",
        "Ambientes",
        "Além da sua máquina de desenvolvimento, quais ambientes vão existir (ex: testes, produção)?",
        [
            opt("single_runtime_env", "Só mais um ambiente além do seu", {"ops_need": 0}),
            opt("basic_dev_test_prod", "Poucos ambientes, bem definidos", {"ops_need": 1}),
            opt("multi_env_with_staging", "Tem um ambiente de homologação ou testes estruturado", {"ops_need": 2, "quality_need": 1}),
            opt("many_governed_envs", "Vários ambientes, cada um com regras diferentes", {"ops_need": 2, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "basic_observability",
        "Motor Final",
        "preset_cloud_business_app",
        "Observabilidade básica",
        "Para acompanhar a saúde do app, o mínimo que precisa existir é o quê (registros, números, avisos)?",
        [
            opt("logs_only", "Só registros básicos bastam", {"ops_need": 0}),
            opt("logs_and_alerts", "Registros e avisos principais", {"ops_need": 1}),
            opt("logs_metrics_alerts", "Registros, números e avisos por parte do sistema", {"ops_need": 2}),
            opt("observability_with_business_signal", "Inclui também sinais do negócio, como vendas", {"ops_need": 2, "quality_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "iam_sso",
        "Motor Final",
        "preset_cloud_corporate_integrated",
        "IAM e SSO",
        "Quais regras de acesso corporativo precisam ser atendidas (login único da empresa, separação de acessos)?",
        [
            opt("managed_identity", "Controle de acesso padrão e administrável", {"security_need": 1}),
            opt("corporate_sso", "Login único da empresa é obrigatório", {"security_need": 2}),
            opt("segregated_admin_and_user_access", "Separação forte entre quem administra e quem usa", {"security_need": 2, "access_load": 1}),
            opt("formal_iam_governance", "O controle de acesso segue governança formal", {"security_need": 2, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "environment_promotion",
        "Motor Final",
        "preset_cloud_corporate_integrated",
        "Ambientes e promoção",
        "Como uma versão vai passar de um ambiente para o outro (ex: de testes para produção)?",
        [
            opt("simple_promotion", "De forma simples", {"ops_need": 1}),
            opt("documented_promotion", "De forma documentada", {"ops_need": 1, "quality_need": 1}),
            opt("approval_based_promotion", "Só com aprovação", {"ops_need": 2, "governance_load": 1}),
            opt("segregated_release_train", "Por um caminho formal de lançamento", {"ops_need": 2, "governance_load": 2}),
        ],
        block_type="preset_block",
    ),
    q(
        "iac_approvals",
        "Motor Final",
        "preset_cloud_corporate_integrated",
        "IaC e approvals",
        "A montagem dos servidores precisa ser automatizada, e o lançamento precisa de aprovações formais?",
        [
            opt("light_iac", "Pouca automação da infraestrutura", {"ops_need": 1}),
            opt("core_iac", "As partes centrais montadas de forma automatizada", {"ops_need": 2}),
            opt("iac_plus_release_gate", "Automação mais uma aprovação formal para lançar", {"ops_need": 2, "governance_load": 1}),
            opt("full_controlled_change", "Toda mudança precisa de aprovação e registro forte", {"ops_need": 2, "governance_load": 2}),
        ],
        block_type="preset_block",
    ),
    q(
        "dr_runbooks",
        "Motor Final",
        "preset_cloud_corporate_integrated",
        "DR e runbooks",
        "Precisa de um plano para desastres (recuperação) e de guias do que fazer quando algo dá errado?",
        [
            opt("basic_runbooks", "Guias básicos já bastam", {"continuity_need": 1}),
            opt("defined_incident_runbooks", "Guias mais uma resposta a incidente", {"continuity_need": 2, "ops_need": 1}),
            opt("dr_expectation", "Tem expectativa de plano de desastre e recuperação", {"continuity_need": 2, "ops_need": 2}),
            opt("formal_resilience_governance", "A recuperação segue governança formal", {"continuity_need": 2, "ops_need": 2, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "commerce_channels",
        "Motor Final",
        "preset_commerce_frontend_app",
        "Canais comerciais",
        "Como você vai vender?",
        [
            opt("single_storefront", "Num site ou loja única", {"frontend_need": 1}),
            opt("catalog_and_checkout", "Num catálogo com finalização de compra no mesmo lugar", {"frontend_need": 2, "integration_need": 1}),
            opt("multi_channel_commerce", "Em mais de um canal de venda", {"frontend_need": 2, "integration_need": 2}),
            opt("partner_or_marketplace_motion", "Com parceiros ou num marketplace", {"frontend_need": 2, "integration_need": 2, "tenant_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "commerce_conversion_flow",
        "Motor Final",
        "preset_commerce_frontend_app",
        "Fluxo de conversão",
        "Como é o caminho até fechar a venda?",
        [
            opt("simple_conversion", "Uma compra simples e direta", {"frontend_need": 1}),
            opt("configurable_checkout", "Uma compra ou proposta com algumas opções para escolher", {"frontend_need": 2}),
            opt("approval_or_quote_flow", "A venda depende de aprovação, proposta ou orçamento", {"frontend_need": 2, "governance_load": 1}),
            opt("multi_step_conversion", "A venda passa por vários passos e etapas", {"frontend_need": 2, "quality_need": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "commerce_core_integrations",
        "Motor Final",
        "preset_commerce_frontend_app",
        "Catálogo, pagamento e logística",
        "A venda depende de conectar com o quê? (pagamento, estoque, frete, sistema da empresa)",
        [
            opt("light_commerce_stack", "Poucas conexões para vender", {"integration_need": 1}),
            opt("payment_and_fulfillment", "Pagamento e entrega fazem parte do centro", {"integration_need": 2}),
            opt("erp_stock_and_checkout", "Sistema da empresa, estoque, pagamento e frete tudo junto", {"integration_need": 2, "ops_need": 1}),
            opt("regulated_payment_surface", "Pagamento e risco exigem controle reforçado", {"integration_need": 2, "security_need": 2}),
        ],
        block_type="preset_block",
    ),
    q(
        "commerce_backoffice",
        "Motor Final",
        "preset_commerce_frontend_app",
        "Backoffice comercial",
        "Para administrar a venda nos bastidores, do que você precisa?",
        [
            opt("light_backoffice", "De um painel de administração leve", {"frontend_need": 1}),
            opt("catalog_and_order_ops", "De gestão de produtos e pedidos", {"frontend_need": 1, "scope_load": 1}),
            opt("customer_service_and_ops", "De atendimento ao cliente junto com a operação", {"frontend_need": 1, "ops_need": 1}),
            opt("governed_commercial_backoffice", "De um painel com perfis, aprovação e registros", {"frontend_need": 1, "security_need": 1, "governance_load": 1}),
        ],
        block_type="preset_block",
    ),
    q(
        "frontend_surfaces",
        "Motor Final",
        "overlay_frontend_light",
        "Pontos de interação",
        "Quais telas o app vai ter (formulários, painéis, etapas de navegação)?",
        [
            opt("few_simple_screens", "Poucas telas simples", {"frontend_need": 0}),
            opt("structured_ui", "Um conjunto organizado de telas", {"frontend_need": 1}),
            opt("journey_with_forms_and_dashboards", "Formulários, painéis e um caminho claro", {"frontend_need": 2}),
            opt("high_touch_experience", "As telas são o coração do produto", {"frontend_need": 2, "quality_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "frontend_accessibility",
        "Motor Final",
        "overlay_frontend_light",
        "Responsividade e acessibilidade",
        "O app precisa funcionar bem no celular, no computador e para pessoas com deficiência?",
        [
            opt("desktop_first_basic", "Foco no computador, com um cuidado básico", {"frontend_need": 0}),
            opt("responsive_required", "Precisa se adaptar a telas de tamanhos diferentes", {"frontend_need": 1}),
            opt("mobile_and_desktop", "Precisa funcionar bem no celular e no computador", {"frontend_need": 2}),
            opt("accessibility_commitment", "A acessibilidade é um requisito claro", {"frontend_need": 2, "quality_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "mvp_launcher",
        "Motor Final",
        "overlay_frontend_light",
        "Atalho de execução do MVP",
        "Durante o desenvolvimento, você quer um atalho de um clique para abrir o app no navegador?",
        [
            opt("no_launcher", "Não preciso de atalho", {"continuity_need": 0}),
            opt("single_os_launcher", "Um atalho num sistema (Windows ou Mac) já basta", {"continuity_need": 0}),
            opt("cross_os_launcher", "Atalhos para Windows e Mac ajudam a equipe", {"continuity_need": 1}),
            opt("launcher_is_operational_requirement", "Abrir o app com um clique é um requisito importante", {"continuity_need": 1, "frontend_need": 1}),
        ],
        block_type="overlay_block",
        detail_hint="Na prática, é criar um arquivo de atalho (run-mvp.cmd no Windows, run-mvp.command no Mac) que abre o app no navegador.",
    ),
    q(
        "sync_source_of_truth",
        "Motor Final",
        "overlay_offline_sync",
        "Fonte de verdade",
        "Quando o app funciona offline e depois sincroniza, qual cópia dos dados vale como a oficial?",
        [
            opt("single_master_source", "Uma fonte oficial única e clara", {"continuity_need": 1}),
            opt("local_then_cloud", "Depende: às vezes a do aparelho, às vezes a da nuvem", {"continuity_need": 2}),
            opt("multi_source_coordination", "Mais de uma fonte que precisam combinar", {"continuity_need": 2, "integration_need": 1}),
            opt("regulated_master_record", "A fonte oficial precisa de controle formal", {"continuity_need": 2, "security_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "sync_conflict_policy",
        "Motor Final",
        "overlay_offline_sync",
        "Conflito",
        "Se a mesma informação mudar no aparelho e na nuvem ao mesmo tempo, como decidir qual vale?",
        [
            opt("rare_manual_resolution", "É raro; quando rolar, resolvo na mão", {"quality_need": 0}),
            opt("rule_based_resolution", "Por uma regra automática clara", {"quality_need": 1}),
            opt("user_visible_conflict_flow", "O usuário escolhe qual vale", {"quality_need": 2, "frontend_need": 1}),
            opt("high_assurance_conflict_policy", "Precisa registrar tudo com rastreabilidade forte", {"quality_need": 2, "security_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "sync_window",
        "Motor Final",
        "overlay_offline_sync",
        "Janela de sincronização",
        "Quando os dados devem sincronizar com a nuvem?",
        [
            opt("opportunistic_sync", "Quando der, sem pressa", {"continuity_need": 0}),
            opt("scheduled_sync", "Em horários combinados", {"continuity_need": 1}),
            opt("near_real_time_sync", "Quase na hora, o tempo todo", {"continuity_need": 2}),
            opt("regulated_sync_window", "O horário do sync afeta a operação ou regras", {"continuity_need": 2, "ops_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "integration_system_owners",
        "Motor Final",
        "overlay_integrations_heavy",
        "Sistemas e owners",
        "Quais sistemas de fora vão se conectar, e quem cuida de cada um?",
        [
            opt("few_known_owners", "Poucos sistemas, com responsáveis claros", {"integration_need": 1}),
            opt("several_known_owners", "Vários sistemas, com responsáveis conhecidos", {"integration_need": 2}),
            opt("mixed_internal_external_owners", "Responsáveis internos e externos misturados", {"integration_need": 2, "dependency_load": 1}),
            opt("unclear_ownership", "Ainda não está claro quem cuida de cada um", {"integration_need": 2, "clarity_risk": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "integration_contract_limits",
        "Motor Final",
        "overlay_integrations_heavy",
        "Contratos e limites",
        "Esses sistemas de fora têm limites (de horário, de quantidade por minuto, de formato)?",
        [
            opt("light_constraints", "Limites leves e previsíveis", {"integration_need": 1}),
            opt("moderate_constraints", "Existem alguns combinados e limites", {"integration_need": 2}),
            opt("strict_limits", "Limites de quantidade ou horário pesam no projeto", {"integration_need": 2, "ops_need": 1}),
            opt("critical_dependency_limits", "Esses limites podem travar o negócio", {"integration_need": 2, "ops_need": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "integration_monitoring",
        "Motor Final",
        "overlay_integrations_heavy",
        "Monitoramento de integração",
        "Como você vai perceber e resolver quando uma conexão com outro sistema falhar?",
        [
            opt("basic_alerting", "Avisos básicos já bastam", {"ops_need": 1}),
            opt("owner_based_monitoring", "Cada falha tem um responsável e um caminho claro", {"ops_need": 2}),
            opt("observable_integration_chain", "As conexões precisam de acompanhamento detalhado", {"ops_need": 2, "quality_need": 1}),
            opt("business_impact_monitoring", "Uma falha aqui afeta a operação ou o faturamento", {"ops_need": 2, "continuity_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "security_encryption",
        "Motor Final",
        "overlay_security_strong",
        "Criptografia",
        "Quais dados precisam ficar protegidos (ao trafegar, ao serem guardados, ou escondidos na tela)?",
        [
            opt("selected_encryption", "Proteção em pontos específicos", {"security_need": 1}),
            opt("broad_encryption", "Proteção ampla, ao trafegar e ao guardar", {"security_need": 2}),
            opt("masking_and_key_controls", "Esconder dados e controlar as chaves importa", {"security_need": 2, "quality_need": 1}),
            opt("strict_sensitive_data_model", "A proteção forte é o centro do produto", {"security_need": 2, "ops_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "security_audit_scope",
        "Motor Final",
        "overlay_security_strong",
        "Auditoria forte",
        "Quais ações delicadas precisam ficar totalmente registradas?",
        [
            opt("few_sensitive_events", "Poucas ações delicadas", {"security_need": 1}),
            opt("admin_and_data_events", "Ações de administração e de dados", {"security_need": 2}),
            opt("privileged_and_business_events", "Ações especiais e de negócio", {"security_need": 2, "quality_need": 1}),
            opt("formal_evidence_chain", "O registro precisa virar prova oficial", {"security_need": 2, "quality_need": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "privileged_actions",
        "Motor Final",
        "overlay_security_strong",
        "Ações privilegiadas",
        "Quais ações são tão sérias que precisam de permissão extra ou da aprovação de duas pessoas?",
        [
            opt("few_privileged_actions", "Poucas ações desse tipo", {"security_need": 1}),
            opt("elevated_actions", "Algumas ações com permissão extra controlada", {"security_need": 2}),
            opt("dual_control_actions", "Algumas exigem aprovação de duas pessoas", {"security_need": 2, "governance_load": 1}),
            opt("strict_privilege_governance", "Esse controle é parte central do projeto", {"security_need": 2, "governance_load": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "service_targets",
        "Motor Final",
        "overlay_ops_advanced",
        "Nível de serviço",
        "Existe uma meta de quanto o app precisa ficar no ar e em quanto tempo se recuperar de uma falha?",
        [
            opt("informal_expectation", "Uma expectativa informal, sem meta fechada", {"ops_need": 1}),
            opt("defined_service_targets", "Metas básicas definidas", {"ops_need": 2}),
            opt("formal_sla_slo", "Metas formais de disponibilidade e de recuperação", {"ops_need": 2, "continuity_need": 1}),
            opt("strict_service_commitment", "Um compromisso de serviço muito rígido", {"ops_need": 2, "continuity_need": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "incident_flow",
        "Motor Final",
        "overlay_ops_advanced",
        "Alertas e incidente",
        "Quando algo dá errado, quais avisos disparam e qual é o passo a passo para resolver?",
        [
            opt("basic_notifications", "Avisos básicos", {"ops_need": 1}),
            opt("defined_incident_owner", "Tem um responsável e um caminho básico", {"ops_need": 2}),
            opt("escalation_and_response", "Tem escalonamento e resposta organizados", {"ops_need": 2, "continuity_need": 1}),
            opt("formal_incident_governance", "Segue um processo formal", {"ops_need": 2, "governance_load": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "release_rollback",
        "Motor Final",
        "overlay_ops_advanced",
        "Rollback",
        "Se uma nova versão der problema, como voltar rápido para a anterior?",
        [
            opt("simple_redeploy", "Basta publicar de novo a versão antiga", {"continuity_need": 1}),
            opt("planned_rollback", "Tem um plano de voltar atrás por ambiente", {"continuity_need": 2}),
            opt("data_sensitive_rollback", "Voltar atrás precisa cuidar dos dados também", {"continuity_need": 2, "quality_need": 1}),
            opt("strict_recovery_runbook", "Exige um guia rigoroso de recuperação", {"continuity_need": 2, "ops_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "tenant_isolation",
        "Motor Final",
        "overlay_multi_tenant",
        "Isolamento",
        "Como separar os dados e acessos de cada cliente para que um não veja o do outro?",
        [
            opt("logical_isolation", "Uma separação simples, por marcação", {"tenant_need": 1}),
            opt("segregated_data_and_access", "Dados e acessos separados por cliente", {"tenant_need": 2}),
            opt("config_plus_data_isolation", "Até as configurações mudam por cliente", {"tenant_need": 2, "security_need": 1}),
            opt("strict_tenant_boundary", "A separação entre clientes é crítica", {"tenant_need": 2, "security_need": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "tenant_onboarding",
        "Motor Final",
        "overlay_multi_tenant",
        "Onboarding e offboarding",
        "Como um novo cliente entra no sistema, e como sai dele?",
        [
            opt("manual_onboarding", "A entrada é feita na mão, controlada", {"tenant_need": 1}),
            opt("templated_onboarding", "A entrada é por um modelo ou roteiro pronto", {"tenant_need": 2}),
            opt("self_service_or_scaled_onboarding", "A entrada precisa escalar ou ser self-service", {"tenant_need": 2, "frontend_need": 1}),
            opt("compliant_offboarding", "A saída precisa preservar obrigações", {"tenant_need": 2, "security_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "tenant_variability",
        "Motor Final",
        "overlay_multi_tenant",
        "Configuração por tenant",
        "O que pode mudar de um cliente para outro sem quebrar o sistema?",
        [
            opt("light_branding_only", "Pouca coisa muda, como só a logo", {"tenant_need": 1}),
            opt("configurable_workflows", "Algumas configurações mudam por cliente", {"tenant_need": 2}),
            opt("rules_and_catalogs_vary", "Regras, catálogo ou fluxo mudam por cliente", {"tenant_need": 2, "quality_need": 1}),
            opt("deep_tenant_customization", "Muda muita coisa de um cliente para outro", {"tenant_need": 2, "scope_load": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "agent_scope",
        "Motor Final",
        "overlay_ai_hitl",
        "Escopo dos agentes",
        "O que a IA vai poder ajudar a fazer ou fazer sozinha?",
        [
            opt("assistive_only", "Só ajudar e sugerir", {"ai_need": 1}),
            opt("bounded_execution", "Fazer tarefas bem limitadas", {"ai_need": 2}),
            opt("workflow_step_execution", "Executar etapas que afetam a operação", {"ai_need": 2, "ops_need": 1}),
            opt("customer_or_sensitive_touchpoints", "Lidar com cliente, dado sensível ou decisão importante", {"ai_need": 2, "security_need": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "forbidden_agent_tasks",
        "Motor Final",
        "overlay_ai_hitl",
        "Tarefas proibidas",
        "O que a IA nunca pode fazer sozinha, sem uma pessoa?",
        [
            opt("few_restrictions", "Poucas proibições", {"ai_need": 1}),
            opt("clear_restricted_actions", "Algumas ações já são bloqueadas", {"ai_need": 2}),
            opt("security_sensitive_prohibitions", "Ações delicadas são proibidas de forma explícita", {"ai_need": 2, "security_need": 1}),
            opt("strict_human_only_zone", "Tem uma área reservada só a humanos", {"ai_need": 2, "governance_load": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "human_checkpoints",
        "Motor Final",
        "overlay_ai_hitl",
        "Checkpoints humanos",
        "Em quais momentos uma pessoa precisa aprovar antes de seguir?",
        [
            opt("exception_only_checkpoints", "Só em casos de exceção", {"ai_need": 1}),
            opt("key_step_checkpoints", "Em etapas-chave", {"ai_need": 2}),
            opt("approval_for_sensitive_steps", "Nas etapas delicadas", {"ai_need": 2, "security_need": 1}),
            opt("formal_human_gate", "Por uma aprovação formal obrigatória", {"ai_need": 2, "governance_load": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "agent_audit",
        "Motor Final",
        "overlay_ai_hitl",
        "Auditoria de agentes",
        "Como registrar o que a IA recebeu, o que respondeu, o que foi aprovado e o que falhou?",
        [
            opt("basic_logs", "Registros básicos do que rodou", {"ai_need": 1}),
            opt("traceable_prompts_and_outputs", "As perguntas e respostas da IA ficam rastreáveis", {"ai_need": 2, "quality_need": 1}),
            opt("approval_audit", "Aprovações e falhas entram no registro", {"ai_need": 2, "security_need": 1}),
            opt("formal_ai_evidence", "O registro da IA precisa virar prova oficial", {"ai_need": 2, "security_need": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "low_code_platform",
        "Motor Final",
        "overlay_low_code_workflow",
        "Plataforma",
        "Qual ferramenta visual (de arrastar-e-soltar) você vai usar para montar isso?",
        [
            opt("light_platform_use", "A ferramenta entra só em partes", {"low_code_need": 1}),
            opt("core_platform_use", "A ferramenta é o centro de tudo", {"low_code_need": 2}),
            opt("platform_plus_custom_code", "Há uma mistura forte entre a ferramenta e código", {"low_code_need": 2, "integration_need": 1}),
            opt("vendor_bound_platform", "A ferramenta gera forte dependência do fornecedor", {"low_code_need": 2, "dependency_load": 1}),
        ],
        block_type="overlay_block",
    ),
    q(
        "low_code_promotion",
        "Motor Final",
        "overlay_low_code_workflow",
        "Promoção",
        "Como levar o que você montou de um ambiente para outro (ex: de testes para o uso real)?",
        [
            opt("manual_platform_publish", "Publicando na mão, de forma simples", {"low_code_need": 1}),
            opt("managed_package_flow", "Com um fluxo organizado de pacotes", {"low_code_need": 2}),
            opt("controlled_platform_release", "Com controle entre ambientes", {"low_code_need": 2, "governance_load": 1}),
            opt("strict_platform_change_process", "Por um processo formal de mudança", {"low_code_need": 2, "governance_load": 2}),
        ],
        block_type="overlay_block",
    ),
    q(
        "low_code_limits",
        "Motor Final",
        "overlay_low_code_workflow",
        "Limites",
        "Quais limites dessa ferramenta podem atrapalhar seus dados, conexões ou o jeito de montar a solução?",
        [
            opt("few_platform_limits", "Poucos limites relevantes", {"low_code_need": 1}),
            opt("known_limits", "Limites conhecidos e administráveis", {"low_code_need": 2}),
            opt("architectural_limits", "Os limites influenciam fortemente como montar a solução", {"low_code_need": 2, "integration_need": 1}),
            opt("critical_platform_constraints", "Os limites podem bloquear parte da solução", {"low_code_need": 2, "scope_load": 1}),
        ],
        block_type="overlay_block",
    ),
]


QUESTION_INDEX: dict[str, dict[str, Any]] = {question["id"]: question for question in QUESTIONS}


# --------------------------------------------------------------------------- #
# Condicoes de fluxo (Fase 3)
# --------------------------------------------------------------------------- #
# Politica de exibicao, reunida numa tabela unica para poder ser lida como
# politica -- "seguranca proporcional ao risco, continuidade proporcional a
# criticidade, aprofundamento condicional" -- em vez de ficar espalhada por 110
# registros. Aplicada aos registros ja construidos; a semantica e a mesma de
# passar `ask_when=` / `skip_when=` para `q()`.
#
# Regra que governou cada escolha: uma pergunta so pode sair do fluxo se os
# sinais que ela gera nao forem necessarios para decidir preset, overlay ou
# profundidade. Verificado rota a rota por `tools/pif_simulate_flow.py`.
#
# `modules` (que absorveu `data_model`) NAO aparece aqui de proposito: e a
# unica fonte de `tenant_need` no nucleo, e sem ela o overlay `multi_tenant`
# deixa de ativar nas rotas que escolhem `multi_area` ou `corporate`.
# `audience_model = multi_tenant` ativa o overlay diretamente, mas so cobre quem
# ja se declarou multi-tenant no bloco de classificadores.

# Gatilhos especificos. `depth_profile: strict` foi deliberadamente evitado como
# escape geral: usado assim, ele reabria quase todo o banco justamente na rota
# cuja meta e a mais apertada em relacao ao caminho atual.
_DEPTH_BEYOND_LITE = {"depth_profile": ["standard", "strict"]}
_RISCO_RELEVANTE = [
    {"data_risk": ["medium", "high"]},
    {"security_need": {"gte": 3}},
]
# Criticidade operacional deixou de ser um classificador auto-declarado. O gate
# passa a ser: a entrega declarada como critica, OU risco operacional ja medido
# por sinal, OU o impacto de perda concreto.
#
# `ops_need >= 2` e alcancavel antes deste gate por perguntas nao condicionadas
# (`problem`, `urgency`, `main_risks`), que e o que impede o ciclo: se o gate
# dependesse apenas de `data_loss_impact`, a propria pergunta que o satisfaz
# ficaria atras dele e nenhuma das cinco perguntas de continuidade seria feita.
_OPERACAO_RELEVANTE = [
    {"delivery_type": "critical_system"},
    {"ops_need": {"gte": 2}},
    {"data_loss_impact": ["high_impact", "legal_or_trust_impact"]},
]
# Gate proprio de `data_loss_impact`: identico ao acima, sem a auto-referencia.
_OPERACAO_RELEVANTE_SEM_IMPACTO = [
    {"delivery_type": "critical_system"},
    {"ops_need": {"gte": 2}},
]
_EQUIPE_OU_MAIOR = {"audience_model": ["small_team", "multi_area", "corporate", "multi_tenant"]}
_ESCALA_CORPORATIVA = {"audience_model": ["multi_area", "corporate", "multi_tenant"]}

FLOW_CONDITIONS: dict[str, dict[str, Any]] = {
    # -- Identidade: quem aprova so importa quando ha mais de um decisor.
    "approvers": {"ask_when": [
        _ESCALA_CORPORATIVA,
        {"governance_load": {"gte": 2}},
    ]},
    # -- Problema e valor: o gargalo e a hipotese aprofundam o que `problem` ja cobre.
    "bottlenecks": {"ask_when": _DEPTH_BEYOND_LITE},
    "value_hypothesis": {"ask_when": _DEPTH_BEYOND_LITE},
    # -- Publico: `primary_users` absorveu `business_context` e passou a ser
    #    incondicional -- e a unica pergunta que descreve quem usa o sistema.
    # -- Escopo: data so quando existe prazo; dependencias so quando ha integracao.
    # Data so quando existe prazo de fato -- e o exemplo citado nos documentos.
    "deadline": {"ask_when": {
        "urgency": ["managerial_priority", "fixed_deadline", "active_incident"],
    }},
    "external_dependencies": {"ask_when": {"integration_intensity": ["few", "many"]}},
    "non_scope": {"ask_when": _DEPTH_BEYOND_LITE},
    "constraints": {"ask_when": _DEPTH_BEYOND_LITE},
    # -- Dados e risco: proporcional ao risco e a criticidade.
    "access_profile": {"ask_when": _EQUIPE_OU_MAIOR},
    "basic_compliance": {"ask_when": _RISCO_RELEVANTE},
    "data_loss_impact": {"ask_when": _OPERACAO_RELEVANTE_SEM_IMPACTO},
    # -- Motor Final / produto: detalhe de aprofundamento.
    "use_cases": {"ask_when": _DEPTH_BEYOND_LITE},
    "flow_criticality": {"ask_when": _OPERACAO_RELEVANTE},
    "business_rules": {"ask_when": _DEPTH_BEYOND_LITE},
    "permissions": {"ask_when": [_ESCALA_CORPORATIVA, {"access_load": {"gte": 2}}]},
    # -- Motor Final / arquitetura.
    "minimal_audit": {"ask_when": _RISCO_RELEVANTE},
    "base_integrations": {"ask_when": {"integration_intensity": ["few", "many"]}},
    "output_directory": {"ask_when": {"runtime": ["local", "offline_first"]}},
    # -- Motor Final / seguranca minima: proporcional ao risco.
    "authentication": {"ask_when": _RISCO_RELEVANTE},
    "authorization": {"ask_when": _RISCO_RELEVANTE},
    "secrets": {"ask_when": _RISCO_RELEVANTE},
    "retention": {"ask_when": _RISCO_RELEVANTE},
    # -- Motor Final / qualidade: aprofundamento.
    "test_strategy": {"ask_when": _DEPTH_BEYOND_LITE},
    "definition_of_done": {"ask_when": _DEPTH_BEYOND_LITE},
    "acceptance_criteria": {"ask_when": _DEPTH_BEYOND_LITE},
    # -- Motor Final / continuidade: proporcional a criticidade.
    "backup_restore": {"ask_when": _OPERACAO_RELEVANTE},
    "update_strategy": {"ask_when": _OPERACAO_RELEVANTE},
    "continuity_owner": {"ask_when": _OPERACAO_RELEVANTE},
}

for _question_id, _condition in FLOW_CONDITIONS.items():
    QUESTION_INDEX[_question_id].update(_condition)


# --------------------------------------------------------------------------- #
# Defaults declarados (Fase 5)
# --------------------------------------------------------------------------- #
# A alternativa ao corte. Uma pergunta com default nao e removida da entrevista:
# quando a condicao bate e ela nao foi respondida, o sistema **assume** a opcao
# declarada, tira a pergunta do fluxo e registra a assuncao no blueprint, com a
# procedencia `preset_default`. A decisao continua tomada e visivel -- o cliente
# revisa se discordar. Cortar a pergunta perderia a decisao; assumir, nao.
#
# Duas regras governam a tabela, e ambas sao verificadas por
# `tools/pif_test_decisions.py`:
#
# 1. A opcao assumida tem de ser a de MENOR carga de sinais da pergunta. Uma
#    assuncao nunca pode empurrar a rota para cima -- se o projeto de fato tiver
#    aquela necessidade, o cliente responde e o sinal aparece. Assim assumir e
#    sempre conservador em relacao ao esforco proposto.
# 2. A condicao so pode ser satisfeita por rotas de baixa exigencia. Nenhum
#    default vale em `strict`.
#
# Consequencia dos dois pontos: os sinais assumidos sao todos zero, e portanto
# nenhum default altera preset, overlay ou profundidade.
_ROTA_ENXUTA = {"depth_profile": "lite"}

ASSUMPTIONS: dict[str, dict[str, Any]] = {
    # -- Governanca: numa rota enxuta ha um dono unico, sem cadeia de aprovacao.
    "approvers": {"option": "single_chain", "when": _ROTA_ENXUTA},
    # -- Escopo: o nao-escopo explicito e o comportamento padrao de um MVP.
    "non_scope": {"option": "explicit_non_scope", "when": _ROTA_ENXUTA},
    # -- Prazo e restricoes: sem pressao declarada, o cronograma e flexivel.
    "constraints": {"option": "low_constraint", "when": _ROTA_ENXUTA},
    # -- Qualidade: verificacao manual basica e o piso de qualquer entrega.
    "test_strategy": {"option": "basic_manual_checks", "when": _ROTA_ENXUTA},
    "definition_of_done": {"option": "light_dod", "when": _ROTA_ENXUTA},
    "acceptance_criteria": {"option": "simple_acceptance", "when": _ROTA_ENXUTA},
    # -- Auditoria: historico leve, proporcional a uma rota sem risco elevado.
    "minimal_audit": {"option": "light_history", "when": _ROTA_ENXUTA},
    # -- Produto: regras de negocio leves acompanham escopo enxuto.
    "business_rules": {"option": "light_rules", "when": _ROTA_ENXUTA},
    # -- Acesso: um nivel unico de acesso e o padrao de equipe pequena.
    "permissions": {"option": "simple_permissions", "when": _ROTA_ENXUTA},
}

for _question_id, _assumption in ASSUMPTIONS.items():
    QUESTION_INDEX[_question_id]["assumption"] = _assumption

OPTION_INDEX: dict[str, dict[str, dict[str, Any]]] = {
    question["id"]: {option["id"]: option for option in question["options"]}
    for question in QUESTIONS
}
