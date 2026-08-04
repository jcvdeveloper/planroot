# PIF Preset Catalog (V2)

## Objetivo
Este arquivo define os presets oficiais por forma de solucao. Cada projeto deve terminar com exatamente um `primary_preset`.

---

## Como usar

1. Ler os classificadores no `Motor Inicial`
2. Aplicar a ordem de decisao do Guia Mestre
3. Escolher um preset principal
4. Ativar overlays complementares
5. Registrar o motivo da escolha

---

## Presets oficiais

### `design_discovery_service`

Use quando:
- o entregavel principal e discovery, workshop, service design, design thinking, mapa de jornada, blueprint de servico, prototipo ou validacao de conceito
- ainda nao existe escopo tecnico fechado de build

Nao use quando:
- o objetivo principal ja e construir e operar um sistema em producao

Profundidade base:
- `lite` ou `standard`

Overlays comuns:
- `frontend_light`
- `ai_hitl`

Blocos normalmente pulados:
- `preset_cloud_corporate`
- `preset_onprem_business_system`

---

### `local_offline_tool`

Use quando:
- a ferramenta roda localmente
- a conectividade e baixa ou ausente
- o uso tende a ser individual ou de equipe pequena
- integracoes sao poucas ou inexistentes

Nao use quando:
- ha dependencia forte de nuvem, multi-area grande ou governanca corporativa

Profundidade base:
- `lite`

Overlays comuns:
- `frontend_light`
- `security_strong` se houver dado sensivel

Blocos normalmente pulados:
- `preset_cloud_business_app`
- `preset_cloud_corporate_integrated`
- `overlay_ops_advanced` quando criticidade for baixa

---

### `local_small_team_app`

Use quando:
- a aplicacao e local ou em rede pequena
- existe mais estrutura que um app offline individual
- ha uso por pequena equipe ou unidade operacional

Nao use quando:
- o problema principal for API sem UI
- o ambiente exigir governanca on-prem complexa
- o uso for corporativo cloud

Profundidade base:
- `lite` ou `standard`

Overlays comuns:
- `frontend_light`
- `offline_sync`

---

### `api_integration_service`

Use quando:
- a interface principal e API, integracao, automacao de dados ou servico sem frontend relevante
- contratos, autenticacao tecnica, retries e observabilidade importam mais que UX detalhada

Nao use quando:
- a principal complexidade estiver em experiencia de tela e operacao humana direta

Profundidade base:
- `standard`

Overlays comuns:
- `integrations_heavy`
- `security_strong`
- `ops_advanced`
- `ai_hitl`, quando houver agentes

Blocos normalmente pulados:
- `overlay_frontend_light`, salvo UI administrativa minima

---

### `onprem_business_system`

Use quando:
- a aplicacao precisa rodar on-prem
- ha dependencia de rede interna, servidor local, AD/LDAP, firewalls, hardening ou ownership interno de infraestrutura

Nao use quando:
- a hospedagem principal e cloud sem requisitos on-prem relevantes

Profundidade base:
- `strict`

Overlays comuns:
- `frontend_light`
- `security_strong`
- `ops_advanced`
- `integrations_heavy`

---

### `commerce_frontend_app`

Use quando:
- o entregavel principal e uma experiencia comercial publica ou semi-publica;
- catalogo, jornada de conversao, checkout, proposta, pedido ou canal de venda sao centrais;
- UX, conversao e integracoes comerciais importam tanto quanto a operacao interna.

Nao use quando:
- o projeto for principalmente um sistema interno sem experiencia comercial externa;
- a principal complexidade estiver em API sem jornada de compra ou navegacao relevante.

Profundidade base:
- `standard` ou `strict`

Overlays comuns:
- `frontend_light`
- `integrations_heavy`
- `security_strong`, quando houver pagamento, dados pessoais ou antifraude
- `multi_tenant`, quando houver operacao por lojista, parceiro ou cliente

---

### `cloud_business_app`

Use quando:
- a aplicacao roda em cloud
- nao ha peso corporativo extremo
- o uso pode ser de area, produto de negocio ou sistema operacional sem governanca enterprise muito pesada

Nao use quando:
- o ambiente exigir SSO corporativo, segregacao forte, change control pesado e integracoes numerosas

Profundidade base:
- `standard`

Overlays comuns:
- `frontend_light`
- `security_strong`
- `integrations_heavy`

---

### `cloud_corporate_integrated`

Use quando:
- a aplicacao roda em cloud corporativa
- ha multiplas areas ou escala corporativa
- ha necessidade forte de IAM, SSO, ambientes segregados, observabilidade, runbooks, approvals, integracoes ou compliance

Nao use quando:
- o caso for simples e de baixa governanca

Profundidade base:
- `strict`

Overlays comuns:
- `frontend_light`
- `integrations_heavy`
- `security_strong`
- `ops_advanced`
- `multi_tenant`
- `ai_hitl`

---

## Regra para casos mistos

Se o projeto combinar caracteristicas de varios presets:

- escolha o preset do entregavel predominante;
- use overlays para o restante;
- registre a segunda melhor opcao em `Assuncao sugerida`.

Exemplos:

- prototipo de experiencia com pouca engenharia -> `design_discovery_service`
- app local com sincronizacao ocasional -> `local_small_team_app` + `offline_sync`
- catalogo, checkout e operacao comercial -> `commerce_frontend_app` + overlays de integracao/seguranca conforme o caso
- sistema cloud com forte integracao e SLA alto -> `cloud_corporate_integrated`
