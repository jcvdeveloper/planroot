# PIF Simulation Scenarios (V1)

## Objetivo
Validar se a logica de roteamento do framework faz sentido em cenarios representativos.

---

## Cenario 1 - Ferramenta local offline para pequena operacao

### Respostas classificadoras
- delivery_type: `internal_tool`
- interaction_model: `backoffice_simple`
- runtime: `offline_first`
- audience_model: `small_team`
- integration_intensity: `few`
- data_risk: `low`
- ai_usage: `none`

### Resultado esperado
- primary_preset: `local_offline_tool`
- active_overlays: `frontend_light`, `offline_sync`
- depth_profile: `lite`

### Veredito
Faz sentido. O caso nao puxa cloud corporate, SLO formal nem bloco pesado de integracao.

---

## Cenario 2 - Projeto de design thinking e discovery

### Respostas classificadoras
- delivery_type: `design_discovery`
- interaction_model: `mixed`
- runtime: `cloud`
- audience_model: `small_team`
- integration_intensity: `none`
- data_risk: `low`
- ai_usage: `assistive`

### Resultado esperado
- primary_preset: `design_discovery_service`
- active_overlays: `frontend_light`, `ai_hitl`
- depth_profile: `lite`

### Veredito
Faz sentido. O caso prioriza discovery e prototipo, sem forcar uma trilha de deploy corporativo.

---

## Cenario 3 - Sistema on-prem para operacao interna

### Respostas classificadoras
- delivery_type: `business_system`
- interaction_model: `backoffice_simple`
- runtime: `on_prem`
- audience_model: `multi_area`
- integration_intensity: `many`
- data_risk: `high`
- ai_usage: `none`

### Resultado esperado
- primary_preset: `onprem_business_system`
- active_overlays: `frontend_light`, `integrations_heavy`, `security_strong`
- depth_profile: `strict`

### Veredito
Faz sentido. O caso aciona infraestrutura local, seguranca forte e operacao avancada.

---

## Cenario 4 - Aplicacao cloud corporativa integrada

### Respostas classificadoras
- delivery_type: `business_system`
- interaction_model: `ui_rich`
- runtime: `cloud`
- audience_model: `corporate`
- integration_intensity: `many`
- data_risk: `high`
- ai_usage: `automated_with_hitl`

### Resultado esperado
- primary_preset: `cloud_corporate_integrated`
- active_overlays: `frontend_light`, `integrations_heavy`, `security_strong`, `ai_hitl`
- depth_profile: `strict`

### Veredito
Faz sentido. O caso exige IAM, approvals, observabilidade e governanca pesada.

---

## Cenario 5 - Servico de API e integracao

### Respostas classificadoras
- delivery_type: `business_system`
- interaction_model: `api_service`
- runtime: `cloud`
- audience_model: `multi_area`
- integration_intensity: `many`
- data_risk: `medium`
- ai_usage: `none`

### Resultado esperado
- primary_preset: `api_integration_service`
- active_overlays: `integrations_heavy`
- depth_profile: `strict`

### Veredito
Faz sentido. O caso reduz UX e amplia contratos, falhas, retries e operacao.
