# PIF — Tabela de migração (Fase 2)

Registro das substituições declaradas em `app/pif_decisions.py`, dos sinais
envolvidos e do efeito medido. Toda divergência no `PIF_Flow_Snapshot.json`
precisa constar aqui antes de o snapshot ser regravado.

## 1. Semântica adotada

`SUPERSEDES` remove a pergunta genérica **somente depois que a especializada foi
respondida**. Enquanto a especializada estiver sem resposta, a genérica
permanece no fluxo — nada é perdido antes de existir substituto.

O plano (`resolve_interview_plan`) governa **exibição e renderização**.
`resolve_routing` continua consumindo todas as respostas coletadas. Portanto uma
genérica já respondida mantém seus sinais no roteamento mesmo depois de sair do
fluxo: **nenhuma substituição desta fase altera preset, overlay ou profundidade.**

## 2. Substituições declaradas

| Especializada | Bloco de origem | Genérica substituída | Decisão | Sinais da genérica | Cobertos pela especializada |
|---|---|---|---|---|---|
| `local_update` | `preset_local_offline_tool` | `update_strategy` | `continuity.strategy` | `continuity_need`, `governance_load` | sim |
| `local_rollout` | `preset_local_small_team_app` | `update_strategy` | `continuity.strategy` | `continuity_need`, `governance_load` | sim |
| `release_rollback` | `overlay_ops_advanced` | `update_strategy` | `continuity.strategy` | `continuity_need`, `governance_load` | sim |
| `local_recovery` | `preset_local_offline_tool` | `backup_restore` | `continuity.strategy` | `continuity_need`, `ops_need` | sim |
| `dr_runbooks` | `preset_cloud_corporate_integrated` | `backup_restore` | `continuity.strategy` | `continuity_need`, `ops_need` | sim |
| `security_audit_scope` | `overlay_security_strong` | `minimal_audit` | `audit.requirements` | `quality_need`, `security_need` | sim |
| `agent_audit` | `overlay_ai_hitl` | `minimal_audit` | `audit.requirements` | `quality_need`, `security_need` | sim |
| `commerce_core_integrations` | `preset_commerce_frontend_app` | `base_integrations` | `integration.landscape` | `dependency_load`, `integration_need` | **parcial** |
| `iam_sso` | `preset_cloud_corporate_integrated` | `authentication` | `access.model` | `access_load`, `security_need` | sim |
| `technical_auth` | `preset_api_integration_service` | `authentication` | `access.model` | `access_load`, `security_need` | sim |
| `privileged_actions` | `overlay_security_strong` | `authorization` | `access.model` | `governance_load`, `security_need` | sim |

### Divergência conhecida

`commerce_core_integrations` não gera `dependency_load`, que `base_integrations`
gera. Sem efeito no roteamento pela semântica da seção 1 (a resposta da genérica
permanece contabilizada). Passa a importar quando a Fase 3 deixar de exibir a
genérica **antes** de respondê-la — nesse momento `dependency_load` precisa ser
transferido para uma opção de `commerce_core_integrations` ou derivado de
`external_dependencies`.

## 3. Efeito medido

Redução de perguntas exibidas por rota, com as 11 substituições ativas:

| Rota | Caminho hoje | Com substituição por resposta | Com substituição por rota (hipótese) |
|---|---:|---:|---:|
| `discovery` | 62 | 62 | 62 |
| `local_offline_tool` | 66 | 66 | 64 |
| `local_team_app` | 62 | 62 | 61 |
| `api_integration` | 63 | 63 | 62 |
| `onprem` | 63 | 63 | 63 |
| `cloud_app` | 62 | 62 | 62 |
| `cloud_corporate` | 66 | 66 | 64 |
| `commerce` | 63 | 63 | 62 |
| `multi_tenant` | 65 | 65 | 65 |
| `ai_hitl` | 66 | 66 | 65 |
| `low_code` | 62 | 62 | 62 |
| `high_security` | 65 | 65 | 63 |
| `critical_ops` | 66 | 66 | 63 |

### Conclusão que contraria o diagnóstico original

Os dois documentos tratam a substituição de genéricas como a correção central da
redundância. Medida, ela vale **0 a 3 perguntas** num caminho de 62 a 66 —
menos de 5%.

O motivo é estrutural: a genérica é `core_always` e aparece muito antes de a
especializada de preset/overlay ser respondida. Mesmo na hipótese mais agressiva
(remover a genérica assim que a especializada entra na rota, com o custo de
recalibrar sinais), o ganho máximo é de 3 perguntas.

**As 45 perguntas `core_always` continuam sendo perguntadas em todas as rotas, e
é aí que está o problema.** A meta de 12–16 perguntas depende quase inteiramente
da Fase 3: núcleo condicional (`ask_when`/`skip_when`), perguntas compostas,
derivação e defaults declarados. A substituição de genéricas é higiene do
artefato, não redução de fluxo.

## 4. Outras mudanças de render nesta fase

| Mudança | Arquivo | Efeito |
|---|---|---|
| `plan_sections()` consome o `InterviewPlan` | `app/pif_blueprint.py` | Pergunta fora do fluxo também some do blueprint |
| "Para versão completa" itera pendências da rota ativa | `app/pif_blueprint.py` | Deixa de listar perguntas de presets e overlays inativos |
| "Pendências da entrevista" cruzada com o plano | `app/pif_blueprint.py` | Idem — era alimentada por `routing["pending_questions"]`, que varre as 110 perguntas do banco |
| `route_summary` expõe `decision_progress` | `server/pif_service.py` | Progresso por decisão ponderada, ao lado da métrica antiga |

Efeito medido no anexo "Para versão completa", rota `local_offline_tool` com
`scope_target = full_version`: passou a listar **10** perguntas, todas do preset
e dos overlays ativos. Antes listaria todas as não respondidas do banco,
incluindo as de rotas que este projeto nunca terá.

### Segundo foco do mesmo defeito

A seção "Pendências da entrevista" tinha o mesmo problema e não estava mapeada
nos documentos. Foi encontrada rodando o fluxo real pela API: com a entrevista
inteira respondida, ela ainda listava **44 perguntas** — todas de presets e
overlays inativos.

Redução de linhas do `blueprint.md`, por rota:

| Rota | Antes | Depois | Redução |
|---|---:|---:|---:|
| `discovery` | 172 | 124 | 48 |
| `local_offline_tool` | 179 | 135 | 44 |
| `local_team_app` | 172 | 124 | 48 |
| `api_integration` | 173 | 126 | 47 |
| `onprem` | 173 | 126 | 47 |
| `cloud_app` | 172 | 124 | 48 |
| `cloud_corporate` | 179 | 135 | 44 |
| `commerce` | 173 | 126 | 47 |
| `multi_tenant` | 178 | 133 | 45 |
| `ai_hitl` | 179 | 135 | 44 |
| `low_code` | 172 | 124 | 48 |
| `high_security` | 178 | 133 | 45 |
| `full_version_annex` | 194 | 150 | 44 |
| `critical_ops` | 179 | 135 | 44 |
| **Total** | **2473** | **1830** | **643 (26%)** |

Nenhuma rota, preset, overlay, profundidade ou sinal mudou: a divergência do
snapshot está inteiramente contida em `renders.*`.

---

# Fase 3 — Corte condicional do fluxo

## 1. O que foi feito

`FLOW_CONDITIONS`, em `app/pif_question_bank.py`, reúne toda a política de
exibição numa tabela única — "segurança proporcional ao risco, continuidade
proporcional à criticidade, aprofundamento condicional". 28 perguntas passaram a
ter `ask_when` ou `skip_when`.

Regra que governou cada escolha: **uma pergunta só pode sair do fluxo se os
sinais que ela gera não forem necessários para decidir preset, overlay ou
profundidade.**

## 2. Como o risco foi medido antes de cortar

Removendo cada bloco e recalculando o roteamento das 14 rotas, **com respostas
de sinal máximo** (a opção de maior carga em cada pergunta):

| Bloco | Perguntas | Rotas que mudam |
|---|---:|---|
| `core_final_product` | 4 | 0/14 |
| `core_final_architecture` | 5 | **13/14 — perde o overlay `multi_tenant`** |
| `core_final_security_min` | 4 | 0/14 |
| `core_final_quality` | 3 | 0/14 |
| `core_final_continuity` | 3 | 0/14 |
| `core_data_access` | 6 | 0/14 |
| `core_scope_constraints` | 7 | 0/14 |
| `core_users_process` | 5 | 0/14 |
| `core_problem_value` | 5 | 0/14 |
| `core_identity` | 3 | 0/14 |

`modules` e `data_model` são as únicas fontes de `tenant_need`, e a regra do
overlay exige `tenant_need >= 2`. Por isso ficaram **fora** das condições.

Uma primeira medição, com as respostas neutras da `BASE_CORE`, apontou 0/14 em
todos os blocos. Era artefato das próprias fixtures: a `BASE_CORE` escolhe a
opção de menor sinal, e os thresholds nunca eram cruzados. A medição com carga
máxima é a que vale.

## 3. Rede de segurança

`tools/pif_simulate_flow.py` simula a entrevista **já cortada** até o ponto fixo:
a cada rodada só permanecem as respostas das perguntas que o fluxo exibiria, e o
roteamento resultante é comparado com o do fluxo completo.

Resultado: **14/14 rotas estáveis** — nenhum preset, overlay ou profundidade
mudou. Roda no gate (`pif_check_all.py`).

## 4. Resultado medido

| Rota | Profundidade | Antes | Depois | Piso | Meta | Status |
|---|---|---:|---:|---:|---:|---|
| `discovery` | `lite` | 62 | 36 | 17 | 16 | **acima — piso estrutural** |
| `local_offline_tool` | `lite` | 66 | 38 | 21 | 16 | **acima — piso estrutural** |
| `local_team_app` | `lite` | 62 | 37 | 17 | 16 | **acima — piso estrutural** |
| `api_integration` | `lite` | 63 | 39 | 18 | 16 | **acima — piso estrutural** |
| `onprem` | `strict` | 63 | 48 | 18 | 32 | acima |
| `cloud_app` | `lite` | 62 | 38 | 17 | 16 | **acima — piso estrutural** |
| `cloud_corporate` | `strict` | 66 | 53 | 21 | 32 | acima |
| `commerce` | `lite` | 63 | 37 | 18 | 16 | **acima — piso estrutural** |
| `multi_tenant` | `standard` | 65 | 50 | 20 | 24 | acima |
| `ai_hitl` | `lite` | 66 | 40 | 21 | 16 | **acima — piso estrutural** |
| `low_code` | `lite` | 62 | 36 | 17 | 16 | **acima — piso estrutural** |
| `high_security` | `strict` | 65 | 54 | 20 | 32 | acima |
| `full_version_annex` | `lite` | 66 | 38 | 21 | 16 | **acima — piso estrutural** |
| `critical_ops` | `strict` | 66 | 54 | 21 | 32 | acima |
| **Total** | | **897** | **598** | | | **-33%** |


Nenhuma divergência do snapshot fora de `flow.*`, `sections` e `renders.*`.

## 5. Limite atingido: o piso estrutural

> **Superado pela Fase 3 (seção 6).** Com 7 classificadores, o piso caiu para
> 13–17 e passou a caber na meta em **11 das 14 rotas** — restam 3 rotas `lite`
> a 1 pergunta de distância. O gargalo deixou de ser o piso e passou a ser o
> núcleo. Os números abaixo descrevem o estado que motivou a Fase 3.

**9 das 14 rotas têm piso acima da meta.** O piso é o que sobra quando todo o
núcleo é cortado: classificadores (10–11) + preset (3–4) + overlays (3–6).

Nenhuma condição adicional resolve isso. Para uma rota `lite`, os 11
classificadores sozinhos consomem 69% do orçamento de 16 perguntas.

Rotas `standard` e `strict` ainda têm folga (piso 18–21 contra metas de 24 e 32),
mas fechá-la por condição exigiria cortar problema, usuários e escopo — as
decisões centrais, cuja ausência degrada o artefato.

**Conclusão:** o caminho para 12–16 é consolidar perguntas, não condicioná-las.
Os próprios documentos apontam para isso ao descrever o núcleo como 9–10
interações — "tipo de solução e modo de uso" já é `delivery_type` +
`interaction_model` + `platform_style` numa pergunta só. Isso exige perguntas
compostas novas, com mapeamento explícito de cada opção para os valores de
classificador e os sinais correspondentes — e é a decisão que abre a próxima
etapa, porque muda o texto que o cliente lê.

---

## 6. Fase 3 — consolidação dos classificadores (11 → 7)

A etapa apontada no fim da seção 5, executada. O piso estrutural das rotas `lite`
era dominado pelos classificadores; consolidá-los era a única forma de baixá-lo
sem cortar decisões centrais.

### 6.1 Equivalências

| Campo removido | Absorvido por | Substituto da regra |
|---|---|---|
| `connectivity_profile` | `runtime` | `runtime = offline_first` (era `local` + `mostly_offline`); `on_prem` cobre `isolated_network` |
| `tenant_model` | `audience_model` (fusão com `user_scale`) | `audience_model = multi_tenant` ou `tenant_need >= 2` |
| `operational_criticality` | — | `delivery_type = critical_system` ou `ops_need >= 4` |
| `platform_style` | `interaction_model` | `interaction_model = workflow_automation` ou `low_code_need >= 2` |

Fundamento de `operational_criticality`: o núcleo alimenta `ops_need` até 13
pontos por 9 perguntas (`data_loss_impact`, `flow_criticality`, `main_risks`,
`continuity_owner`, `backup_restore`, entre outras), muito acima do gatilho 4 das
regras que o campo governava. Ele era uma auto-avaliação abstrata sobreposta a
fatos que a entrevista já coletava.

`ai_usage` e a fonte de `low_code_need` **não** puderam ser removidos: o núcleo
gera `ai_need = 0` e `low_code_need = 1` no máximo, abaixo dos gatilhos. Por isso
`platform_style` foi absorvido por um valor de `interaction_model` em vez de
eliminado.

### 6.2 Efeito no roteamento

**Nenhum.** As 13 fixtures de regressão produzem `primary_preset`,
`active_overlays`, `depth_profile` e os 6 perfis de blueprint idênticos aos de
antes da consolidação.

Duas regras precisaram ser ajustadas para preservar isso:

- `audience_model = multi_tenant` foi deliberadamente **mantido fora** de
  `depth_rules[10]` e `preset_rules[50]`. Incluí-lo promovia todo micro-SaaS a
  `strict` + `cloud_corporate_integrated`, reabrindo quase todo o banco.
- O gate `ops_advanced` permanece em `ops_need >= 4`. `PIF_Decision_Matrix.md`
  documentava `>= 3` — divergência anterior a esta fase, corrigida no texto, não
  no comportamento: baixar o gate ativava `ops_advanced` na rota `onprem`.

### 6.3 Efeito no volume de perguntas

Fase 1 caiu de **37 para 33** perguntas em todas as rotas.

| Rota | Profundidade | Antes | Depois | Δ |
|---|---|---|---|---|
| `discovery` | lite | 36 | 32 | -4 |
| `local_offline_tool` | lite | 38 | 35 | -3 |
| `local_team_app` | lite | 37 | 33 | -4 |
| `api_integration` | lite | 39 | 35 | -4 |
| `onprem` | strict | 48 | 49 | +1 |
| `cloud_app` | lite | 38 | 34 | -4 |
| `cloud_corporate` | strict | 53 | 49 | -4 |
| `commerce` | lite | 37 | 33 | -4 |
| `multi_tenant` | standard | 50 | 46 | -4 |
| `ai_hitl` | lite | 40 | 41 | +1 |
| `low_code` | lite | 36 | 32 | -4 |
| `high_security` | strict | 54 | 50 | -4 |
| `full_version_annex` | lite | 38 | 35 | -3 |
| `critical_ops` | strict | 54 | 50 | -4 |
| **Total** | | **598** | **554** | **-44** |

As rotas `onprem` e `ai_hitl` **ganham** uma pergunta. É intencional: o gate de
continuidade (`_OPERACAO_RELEVANTE`) deixou de depender do campo auto-declarado e
passou a aceitar `ops_need >= 2`, que `runtime = on_prem` (3) e `ai_usage =
automated_with_hitl` (1 + núcleo) alcançam. Essas rotas antes **não** eram
perguntadas sobre continuidade porque a linha de base declarava
`operational_criticality = low` — um sistema on-premise que nunca respondia sobre
backup e recuperação.

### 6.4 Correção estrutural acoplada

`resolve_routing` nunca derivou sinais em `input_mode="classifiers"` — entrava nas
regras com todos os sinais em zero, fazendo a mesma rota decidir diferente
conforme o modo de entrada. Tolerável enquanto cada classificador era condição
direta; incompatível com uma matriz que agora depende de sinais como substitutos.

`derive_signals_from_classifiers` (`tools/pif_router.py`) lê os sinais do próprio
banco de perguntas e os aplica nesse modo. Não altera `input_mode="answers"`: as
13 fixtures seguem idênticas.

### 6.5 Divergências assumidas

Casos de teste em modo `classifiers` puro perderam `ops_advanced`
(`onprem_high_risk`, `cloud_corporate_integrated`, `api_integration_service`) e
`low_code_workflow` (`design_discovery`). Sem entrevista, os sinais derivados de
classificadores sozinhos não alcançam `ops_need >= 4`; rigor operacional passa a
exigir `delivery_type = critical_system`. Cada caso registra o motivo em
`consolidation_note`.

`fallback_hybrid` mudou de `lite` para `strict` + `ops_advanced`. O caso declarava
`critical_system` com `operational_criticality = low` — combinação contraditória
que só era expressável porque os campos eram independentes.

Correções pré-existentes encontradas de passagem: `PIF_Simulation_Scenarios.md`
declarava `delivery_type: design_service`, valor que nunca esteve no domínio, e o
Cenário 1 omitia `offline_sync`. Os 5 cenários agora são validados contra o motor.

---

## 7. Fase 4 — consolidação do núcleo (45 → 40 perguntas `core_always`)

Com o piso resolvido pela Fase 3, o gargalo passou a ser o núcleo: 343 perguntas
`core_always` somadas nas 14 rotas. A análise por decisão mostrou que **4
decisões concentravam 54% desse total**, cada uma com múltiplas perguntas
disparadas em todas as rotas.

### 7.1 Fusões

| Perguntas fundidas | Resultado | Evidência de redundância |
|---|---|---|
| `product_objective` + `critical_flows` + `mvp_scope` | `mvp_scope` | As três graduavam `scope_load` 0–2 em todas as rotas. Eram "quão grande é isto?" perguntado por três ângulos: objetivo, tarefas e recorte. |
| `handled_data` + `data_sensitivity` | `handled_data` | `data_sensitivity` era subconjunto exato: mesma escala `security_need` 0–2, nenhum sinal exclusivo, perguntada logo após a pessoa já ter escolhido entre "cadastro simples" e "protegido por lei". |
| `primary_users` + `business_context` | `primary_users` | Ambas resolviam `users.audience_and_scale` e descreviam o mesmo público — quem usa e onde se encaixa. |
| `modules` + `data_model` | `modules` | Ambas mediam tamanho estrutural e eram as duas únicas fontes de `tenant_need` no núcleo. |

### 7.2 Por que foi seguro

`scope_load`, `access_load`, `quality_need` e `problem_pressure` **não governam
nenhuma regra** da matriz — só informam o blueprint. Fundir perguntas que
diferiam apenas nesses eixos não podia alterar roteamento.

Os sinais exclusivos que **sim** governam regras foram preservados opção a opção:
`integration_need` (fluxos que cruzam sistemas), `frontend_need` (jornada de
cliente), `clarity_risk` (escopo em aberto) e `tenant_need`. Neste último, a
opção mais pesada de `modules` passou a carregar `tenant_need: 2` — a soma das
duas originais — para que o overlay `multi_tenant` continue alcançável pelo
núcleo, sem depender de `audience_model = multi_tenant`.

**Efeito no roteamento: nenhum.** As 13 fixtures seguem idênticas à baseline
anterior à Fase 3.

### 7.3 Efeito no volume

| Rota | Profundidade | Fase 3 | Fase 4 | Meta | Gap |
|---|---|---:|---:|---:|---:|
| `discovery` | lite | 32 | 27 | 16 | +11 |
| `local_offline_tool` | lite | 35 | 31 | 16 | +15 |
| `local_team_app` | lite | 33 | 28 | 16 | +12 |
| `api_integration` | lite | 35 | 30 | 16 | +14 |
| `onprem` | strict | 49 | 44 | 32 | +12 |
| `cloud_app` | lite | 34 | 29 | 16 | +13 |
| `cloud_corporate` | strict | 49 | 44 | 32 | +12 |
| `commerce` | lite | 33 | 28 | 16 | +12 |
| `multi_tenant` | standard | 46 | 41 | 24 | +17 |
| `ai_hitl` | lite | 41 | 36 | 16 | +20 |
| `low_code` | lite | 32 | 27 | 16 | +11 |
| `high_security` | strict | 50 | 45 | 32 | +13 |
| `full_version_annex` | lite | 35 | 31 | 16 | +15 |
| `critical_ops` | strict | 50 | 45 | 32 | +13 |
| **Total** | | **554** | **486** | | **-68** |

Acumulado das Fases 3 e 4: **598 → 486 (-19%)**; banco de 110 → 101 perguntas.

### 7.4 Perdas assumidas

- **Muitos perfis numa única área.** A fusão `primary_users` + `business_context`
  não distingue mais "vários perfis num setor só" de "vários perfis em várias
  áreas". Por isso `governance_load` foi retirado da opção de múltiplos perfis:
  mantê-lo puniria o primeiro caso, e o alcance organizacional já carrega essa
  carga por `audience_model`. Detectado por `answer_driven_security_signal`, que
  mudava de `cloud_business_app` para `cloud_corporate_integrated`.
- **Escopo amplo porém decidido.** `mvp_scope` perdeu o `delivery_pressure: 1` que
  `broad_scope` gerava — o limite de 5 opções por pergunta não comportava separar
  "muita coisa" de "ainda decidindo". O sinal tem outras 5 fontes (9 pontos no
  total), então nenhuma regra ficou sem alcance.
- **Módulos e entidades em eixos separados.** `modules` não distingue mais um
  sistema de poucos blocos com dados complexos de um com muitos blocos e dados
  simples.

### 7.5 Onde o limite está agora

O gap remanescente é de +11 a +20 perguntas por rota. O que sobrou no núcleo são
decisões de conteúdo distinto — problema, resultado, medição, prazo, restrições,
acesso, continuidade, qualidade — não mais reformulações do mesmo eixo. Reduzir
além disto deixa de ser consolidação e passa a ser **corte de decisão**: escolher
que o artefato não cobrirá determinado assunto. Essa é uma decisão de produto, não
de engenharia, e precisa ser tomada assunto a assunto.
