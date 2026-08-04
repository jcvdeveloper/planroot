# PIF Module Matrix (V1)

## Objetivo
Este arquivo mapeia cada bloco do framework para o arquivo de origem, tipo, regra de ativacao e papel na entrevista.

---

## Blocos do Motor Inicial

| Block ID | Arquivo | Tipo | Perguntar quando | Finalidade |
|---|---|---|---|---|
| `core_identity` | `PIF_Motor_Inicial.md` | `core_always` | sempre | identidade, sponsor, aprovadores |
| `core_problem_value` | `PIF_Motor_Inicial.md` | `core_always` | sempre | problema, resultado esperado, urgencia |
| `core_users_process` | `PIF_Motor_Inicial.md` | `core_always` | sempre | usuarios, jornada, processo atual |
| `core_scope_constraints` | `PIF_Motor_Inicial.md` | `core_always` | sempre | MVP, nao escopo, prazo, capacidade |
| `core_data_access` | `PIF_Motor_Inicial.md` | `core_always` | sempre | dados, acesso, compliance basico, riscos |
| `classifier_block` | `PIF_Motor_Inicial.md` | `classifier` | sempre | selecionar preset, overlays e profundidade |

---

## Blocos do Motor Final - Nucleo

| Block ID | Arquivo | Tipo | Perguntar quando | Finalidade |
|---|---|---|---|---|
| `core_final_product` | `PIF_Motor_Final.md` | `core_always` | sempre | casos de uso, criticidade, permissoes, regras |
| `core_final_architecture` | `PIF_Motor_Final.md` | `core_always` | sempre | modulos, dados, auditoria, integracoes base |
| `core_final_security_min` | `PIF_Motor_Final.md` | `core_always` | sempre | autenticacao, autorizacao, segredos, retencao minima |
| `core_final_quality` | `PIF_Motor_Final.md` | `core_always` | sempre | testes, DoD, aceite |
| `core_final_continuity` | `PIF_Motor_Final.md` | `core_always` | sempre | backup, release, suporte, continuidade |

---

## Blocos do Motor Final - Preset

| Block ID | Arquivo | Tipo | Perguntar quando | Finalidade |
|---|---|---|---|---|
| `preset_design_discovery_service` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = design_discovery_service` | discovery, workshops, prototipos, transicao para build |
| `preset_local_offline_tool` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = local_offline_tool` | instalacao local, armazenamento local, atualizacao e restore |
| `preset_local_small_team_app` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = local_small_team_app` | rede local, equipe pequena, atualizacao simples |
| `preset_api_integration_service` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = api_integration_service` | contratos, retries, idempotencia, auth tecnica |
| `preset_onprem_business_system` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = onprem_business_system` | AD/LDAP, rede, hardening, patching, logs locais |
| `preset_commerce_frontend_app` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = commerce_frontend_app` | canais comerciais, conversao, catalogo/pagamento/logistica e backoffice comercial |
| `preset_cloud_business_app` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = cloud_business_app` | cloud baseline, ambientes, observabilidade basica |
| `preset_cloud_corporate_integrated` | `PIF_Motor_Final.md` | `preset_block` | `primary_preset = cloud_corporate_integrated` | IAM, SSO, IaC, approvals, runbooks, DR |

---

## Blocos do Motor Final - Overlays

| Block ID | Arquivo | Tipo | Perguntar quando | Finalidade |
|---|---|---|---|---|
| `overlay_frontend_light` | `PIF_Motor_Final.md` | `overlay_block` | `interaction_model = ui_rich|backoffice_simple|mixed` | telas, formularios, dashboards, responsividade, acessibilidade e decisao sim/nao sobre atalhos `run-mvp` para frontend web |
| `overlay_offline_sync` | `PIF_Motor_Final.md` | `overlay_block` | `runtime = offline_first` ou `continuity_need >= 3` | sincronizacao, conflitos, fonte de verdade |
| `overlay_integrations_heavy` | `PIF_Motor_Final.md` | `overlay_block` | `integration_intensity = many` | contratos, owners, retries, rate limits |
| `overlay_security_strong` | `PIF_Motor_Final.md` | `overlay_block` | `data_risk = high` ou compliance forte | criptografia, auditoria, privilegio, trilha forte |
| `overlay_ops_advanced` | `PIF_Motor_Final.md` | `overlay_block` | `delivery_type = critical_system` ou `ops_need >= 4` | alertas, SLO/SLA, suporte formal, incidentes |
| `overlay_multi_tenant` | `PIF_Motor_Final.md` | `overlay_block` | `audience_model = multi_tenant` | segregacao, onboarding/offboarding, configuracao por tenant |
| `overlay_ai_hitl` | `PIF_Motor_Final.md` | `overlay_block` | `ai_usage = assistive|automated_with_hitl` | tarefas permitidas, proibidas, checkpoints, auditoria |
| `overlay_low_code_workflow` | `PIF_Motor_Final.md` | `overlay_block` | `interaction_model = workflow_automation` | limites da plataforma, promocao de ambientes, versionamento |

---

## Regras de profundidade

| Condicao | Profundidade recomendada |
|---|---|
| baixo risco, pequena escala, poucas integracoes | `lite` |
| caso normal | `standard` |
| alto risco, operacao critica, on-prem ou cloud corporate | `strict` |

---

## Regras de pulo

Um bloco so pode ser pulado quando:

- ele nao for `core_always`;
- a condicao de ativacao estiver claramente falsa;
- o motivo do pulo for registrado em `skipped_modules`.

Exemplo de registro:

- `overlay_ops_advanced`: pulado porque a entrega nao foi declarada critica e `ops_need` ficou abaixo de 4 e nao ha SLA formal
- `preset_onprem_business_system`: pulado porque `runtime = cloud`
