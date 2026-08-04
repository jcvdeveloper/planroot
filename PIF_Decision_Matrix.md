# PIF Decision Matrix (V2)

## Objetivo
Esta e a matriz deterministica do framework. Na V2, ela nao cruza apenas o `classifier_block`: ela cruza a entrevista inteira.

Cada pergunta possui de 3 a 5 respostas substantivas no `app/pif_question_bank.py`. Cada resposta faz duas coisas:

- pode derivar um classificador estrutural;
- pode somar sinais deterministas para o blueprint inicial.

As saidas continuam sendo:

- `depth_profile`
- `primary_preset`
- `active_overlays`
- `blueprint_profile`
- `skipped_modules`

Se houver conflito entre texto explicativo e a matriz JSON, `PIF_Decision_Matrix.json` vence.

---

## Ordem de avaliacao

1. Normalizar `answers` ou `classifiers`
2. Derivar classificadores a partir das respostas, quando a entrada vier da entrevista
3. Somar `signal_fields`
4. Resolver `depth_profile`
5. Resolver `primary_preset`
6. Resolver `active_overlays`
7. Resolver `blueprint_profile`
8. Registrar `skipped_modules`

---

## Dominios aceitos

Sao 7 campos. Eram 11 ate a consolidacao -- ver "Classificadores consolidados",
mais abaixo, para o que cada campo removido virou.

| Campo | Valores |
|---|---|
| `delivery_type` | `design_discovery`, `internal_tool`, `business_system`, `commerce_experience`, `critical_system` |
| `interaction_model` | `ui_rich`, `backoffice_simple`, `api_service`, `workflow_automation`, `mixed` |
| `runtime` | `local`, `offline_first`, `on_prem`, `cloud`, `hybrid` |
| `audience_model` | `individual`, `small_team`, `multi_area`, `corporate`, `multi_tenant` |
| `integration_intensity` | `none`, `few`, `many` |
| `data_risk` | `low`, `medium`, `high` |
| `ai_usage` | `none`, `assistive`, `automated_with_hitl` |

Nos dois modos de entrada (`answers` e `classifiers`) os classificadores geram
sinais. No modo `classifiers` eles sao derivados por
`derive_signals_from_classifiers`, para que a mesma rota nao decida diferente
conforme o modo de entrada. Apenas o modo `answers` acrescenta o peso das
respostas de nucleo.

---

## Eixos de sinal

Toda resposta pode somar pontos em um ou mais eixos:

- `clarity_risk`
- `governance_load`
- `problem_pressure`
- `scope_load`
- `delivery_pressure`
- `dependency_load`
- `access_load`
- `security_need`
- `ops_need`
- `integration_need`
- `frontend_need`
- `ai_need`
- `tenant_need`
- `low_code_need`
- `quality_need`
- `continuity_need`

Esses eixos permitem que perguntas fora do classificador influenciem overlays, profundidade e perfis de blueprint sem perder determinismo.

---

## Matriz de profundidade

Primeira regra valida vence.

| Prioridade | Se | Resultado |
|---|---|---|
| 10 | alto risco estrutural (`data_risk = high`, `runtime = on_prem`, `audience_model = corporate`, `delivery_type = critical_system`, `integration_intensity = many`) ou `security_need >= 4` ou `ops_need >= 4` ou `governance_load >= 4` | `strict` |
| 20 | pequena escala + poucas integracoes + baixo risco + `ops_need <= 3` + baixa governanca/dependencia | `lite` |
| 99 | qualquer outro caso | `standard` |

`audience_model = multi_tenant` de proposito NAO entra na regra 10: multi-tenancy
e tratada pelo overlay `multi_tenant`, e promover todo micro-SaaS a `strict`
reabriria quase todo o banco de perguntas.

---

## Matriz de preset principal

Primeira regra valida vence.

| Prioridade | Se | `primary_preset` |
|---|---|---|
| 10 | `delivery_type = design_discovery` | `design_discovery_service` |
| 20 | `runtime = offline_first` + pequena escala + poucas integracoes | `local_offline_tool` |
| 30 | `runtime = on_prem` | `onprem_business_system` |
| 40 | `interaction_model = api_service` | `api_integration_service` |
| 45 | `delivery_type = commerce_experience` | `commerce_frontend_app` |
| 50 | `runtime = cloud` e houver peso corporate / integracoes / criticidade / governanca | `cloud_corporate_integrated` |
| 60 | `runtime = cloud` | `cloud_business_app` |
| 70 | `runtime in {local, offline_first}` | `local_small_team_app` |
| 99 | qualquer outro caso | `cloud_business_app` com `Assuncao sugerida` |

---

## Matriz de overlays

Todas as regras validas sao acumuladas.

| Overlay | Ativar quando |
|---|---|
| `frontend_light` | `interaction_model` com UI ou `frontend_need >= 2` |
| `offline_sync` | `runtime = offline_first` ou `continuity_need >= 3` |
| `integrations_heavy` | `integration_intensity = many` ou `integration_need >= 3` |
| `security_strong` | `data_risk = high` ou `security_need >= 3` |
| `ops_advanced` | `delivery_type = critical_system` ou `ops_need >= 4` ou `continuity_need >= 3` |
| `multi_tenant` | `audience_model = multi_tenant` ou `tenant_need >= 2` |
| `ai_hitl` | `ai_usage` ativo ou `ai_need >= 2` |
| `low_code_workflow` | `interaction_model = workflow_automation` ou `low_code_need >= 2` |

---

## Perfis iniciais de blueprint

Depois do roteamento, a matriz tambem devolve perfis resumidos para orientar o blueprint inicial:

- `discovery_profile`: `exploratory | aligning | defined`
- `governance_profile`: `lean | managed | formal`
- `delivery_profile`: `flexible | scheduled | urgent`
- `risk_profile`: `low | managed | high`
- `experience_profile`: `internal | service | interface | commerce`
- `operability_profile`: `simple | managed | critical`

Esses perfis nao substituem o blueprint final. Eles apenas sintetizam a entrevista para a primeira versao do plano.

---

## Classificadores consolidados

De 11 para 7. Cada remocao teve um substituto verificado antes de sair, e as 13
fixtures de regressao continuam produzindo preset, overlays, `depth_profile` e
os 6 perfis de blueprint identicos aos de antes.

| Campo removido | Para onde foi | Por que era redundante |
|---|---|---|
| `connectivity_profile` | `runtime` | Conectividade nunca foi independente do lugar onde o sistema roda: `local`/`offline_first` ja implicavam o regime de conexao, e `isolated_network` era `on_prem` com outro nome. |
| `tenant_model` | `audience_model` (com `user_scale`) | As duas perguntas ja resolviam a mesma decisao, `users.audience_and_scale`. |
| `operational_criticality` | `delivery_type = critical_system` + `ops_need` | Auto-avaliacao abstrata ("pequeno/medio/grande"). O nucleo alimenta `ops_need` ate 13 pontos a partir de fatos concretos (`data_loss_impact`, `flow_criticality`, `main_risks`, `continuity_owner`, `backup_restore`), muito acima do gatilho 4. |
| `platform_style` | `interaction_model = workflow_automation` | Escolha de implementacao que o entrevistado raramente sabe responder no inicio; seu unico efeito era o overlay `low_code_workflow`. |

Efeito medido: fase 1 caiu de 37 para 33 perguntas em todas as rotas, e o
caminho ativo somado das 14 fixtures caiu de 598 para 554 perguntas.

### O que se perdeu, explicitamente

- **Rede isolada fora de on-premise.** Um sistema em nuvem numa rede fechada nao
  tem mais como declarar isolamento; o caminho passa a ser `on_prem`.
- **Escala e isolamento em eixos separados.** `audience_model` nao distingue mais
  "empresa inteira, contexto unico" de "empresa inteira, varias unidades", nem
  expressa multi-tenancy em escala pequena versus corporativa.
- **Low-code fora de automacao.** Uma interface rica montada em ferramenta visual
  nao ativa mais o overlay `low_code_workflow` pelo classificador -- so por
  `low_code_need >= 2`.
- **Criticidade no modo `classifiers` puro.** Sem passar pela entrevista, rigor
  operacional so pode ser declarado por `delivery_type = critical_system`: os
  sinais derivados de classificadores sozinhos nao alcancam `ops_need >= 4`.

## Regras de fallback

| Situacao | Regra |
|---|---|
| Resposta ausente | manter `core_always`, marcar pendencia, seguir pela rota mais conservadora compativel |
| Conflito entre simplicidade e risco | vence a rota mais conservadora |
| Dois presets parecem validos | vence o de maior restricao operacional |

---

## Regra de execucao final

Depois de resolver a matriz:

1. Perguntar todos os blocos `core_always`
2. Perguntar o `preset_block` do `primary_preset`
3. Perguntar todos os `overlay_block` ativos
4. Registrar como `skipped_modules` tudo que ficou inativo por regra
