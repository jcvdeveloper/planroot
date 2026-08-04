# Project Initiation Framework - Motor Final (V4)

## Objetivo
Executar o nucleo tecnico minimo e, depois, apenas os blocos do preset principal e dos overlays ativos.

## Regras
- Sempre perguntar os blocos `core_always`.
- Perguntar exatamente um `preset_block`, conforme `primary_preset`.
- Perguntar todos os `overlay_block` ativos.
- Registrar blocos pulados em `skipped_modules`, com motivo.

---

## Bloco `core_final_product`
Tipo: `core_always`
Profundidade base: `standard`

### Casos de uso
Pergunta: Quais casos de uso precisam existir para o MVP funcionar de verdade?

### Criticidade por fluxo
Pergunta: Quais fluxos sao criticos, importantes e apenas convenientes?

### Regras de negocio
Pergunta: Quais regras de negocio nao podem ser violadas?

### Permissoes
Pergunta: O que cada perfil pode ver, criar, editar, aprovar, exportar ou excluir?

---

## Bloco `core_final_architecture`
Tipo: `core_always`
Profundidade base: `standard`

### Modulos principais
Pergunta: Quais modulos ou dominios principais a solucao precisa ter?

### Modelo de dados
Pergunta: Quais entidades e dados obrigatorios existem?

### Auditoria minima
Pergunta: Quais acoes precisam deixar trilha de historico ou auditoria?

### Integracoes base
Pergunta: Quais integracoes obrigatorias ja estao confirmadas?

### Diretorio de saida
Pergunta: Em qual diretorio a saida final deve ser gerada?

---

## Bloco `core_final_security_min`
Tipo: `core_always`
Profundidade base: `standard`

### Autenticacao
Pergunta: Como o usuario ou sistema vai se autenticar?

### Autorizacao
Pergunta: Como as permissoes serao controladas?

### Segredos
Pergunta: Como segredos, tokens e chaves serao geridos?

### Retencao minima
Pergunta: Quanto tempo dados e logs precisam ser mantidos?

---

## Bloco `core_final_quality`
Tipo: `core_always`
Profundidade base: `standard`

### Estrategia minima de testes
Pergunta: Quais tipos de teste sao obrigatorios antes de liberar uma versao?

### Definition of Done
Pergunta: Quando uma funcionalidade pode ser considerada pronta?

### Criterios de aceite
Pergunta: Como o negocio vai validar cada fluxo critico?

---

## Bloco `core_final_continuity`
Tipo: `core_always`
Profundidade base: `standard`

### Backup e restauracao
Pergunta: O que precisa de backup e como a restauracao sera validada?

### Estrategia de atualizacao
Pergunta: Como novas versoes serao instaladas ou liberadas?

### Owner de continuidade
Pergunta: Quem monitora, corrige e sustenta a solucao depois do go-live?

---

## Bloco `preset_design_discovery_service`
Tipo: `preset_block`
Perguntar quando: `primary_preset = design_discovery_service`

### Artefatos esperados
Pergunta: O resultado principal e mapa de jornada, service blueprint, prototipo, workshop output ou validacao de conceito?

### Metodo de discovery
Pergunta: Havera entrevistas, workshops, observacao, testes com usuarios ou outro metodo?

### Criterio de transicao
Pergunta: O que precisa estar definido para sair de discovery e virar build?

---

## Bloco `preset_local_offline_tool`
Tipo: `preset_block`
Perguntar quando: `primary_preset = local_offline_tool`

### Instalacao local
Pergunta: Como a ferramenta sera instalada na maquina?

### Armazenamento local
Pergunta: Os dados ficam em arquivo, banco embarcado ou outro formato local?

### Atualizacao
Pergunta: Como novas versoes serao distribuidas e aplicadas?

### Recuperacao
Pergunta: Como restaurar a operacao em outra maquina se o equipamento falhar?

---

## Bloco `preset_local_small_team_app`
Tipo: `preset_block`
Perguntar quando: `primary_preset = local_small_team_app`

### Topologia local
Pergunta: A aplicacao roda em uma maquina, em rede local ou em servidor simples da unidade?

### Concorrencia
Pergunta: Quantas pessoas usam ao mesmo tempo e como conflitos devem ser tratados?

### Atualizacao local
Pergunta: Como atualizar a aplicacao sem interromper a equipe de forma caotica?

---

## Bloco `preset_api_integration_service`
Tipo: `preset_block`
Perguntar quando: `primary_preset = api_integration_service`

### Contratos
Pergunta: Quais contratos de API ou troca de dados ja existem ou precisam ser definidos?

### Autenticacao tecnica
Pergunta: Como sistemas externos se autenticam?

### Falhas e retries
Pergunta: Como tratar timeout, retry, idempotencia e erro parcial?

### Versionamento
Pergunta: Como mudancas no contrato serao versionadas?

---

## Bloco `preset_onprem_business_system`
Tipo: `preset_block`
Perguntar quando: `primary_preset = onprem_business_system`

### Infra local
Pergunta: Quem opera servidores, rede, acesso e backup no ambiente on-prem?

### Integracao corporativa local
Pergunta: Havera AD, LDAP, pastas de rede, proxy, firewall ou politicas locais obrigatorias?

### Hardening e patching
Pergunta: Como atualizacoes de sistema, seguranca e aplicacao serao controladas?

### Logs locais
Pergunta: Onde os logs ficam e quem pode consultalos?

---

## Bloco `preset_commerce_frontend_app`
Tipo: `preset_block`
Perguntar quando: `primary_preset = commerce_frontend_app`

### Canais comerciais
Pergunta: A experiencia comercial sera site unico, catalogo com checkout, multicanal ou operacao com parceiros?

### Fluxo de conversao
Pergunta: A jornada de venda e simples, configuravel, depende de aprovacao ou combina varios passos?

### Catalogo, pagamento e logistica
Pergunta: O nucleo comercial depende de catalogo, pagamento, antifraude, estoque, frete ou ERP?

### Backoffice comercial
Pergunta: A operacao comercial precisa de painel simples, operacao de catalogo, pedidos ou governanca mais forte?

---

## Bloco `preset_cloud_business_app`
Tipo: `preset_block`
Perguntar quando: `primary_preset = cloud_business_app`

### Conta e hospedagem
Pergunta: Em qual conta, tenant ou ambiente cloud a solucao rodara?

### Ambientes
Pergunta: Quais ambientes alem do desenvolvimento local precisarao existir?

### Observabilidade basica
Pergunta: Quais logs, metricas e alertas minimos precisam existir?

---

## Bloco `preset_cloud_corporate_integrated`
Tipo: `preset_block`
Perguntar quando: `primary_preset = cloud_corporate_integrated`

### IAM e SSO
Pergunta: Quais requisitos de IAM, SSO e segregacao de acesso precisam ser atendidos?

### Ambientes e promotao
Pergunta: Como a promocao entre ambientes sera controlada?

### IaC e approvals
Pergunta: O que precisa ser gerido como codigo e quais aprovacoes formais de release existem?

### DR e runbooks
Pergunta: Existe expectativa de desastre, recuperacao, runbooks e governanca de incidentes?

---

## Bloco `overlay_frontend_light`
Tipo: `overlay_block`
Perguntar quando: `interaction_model = ui_rich|backoffice_simple|mixed`

### Pontos de interacao
Pergunta: Quais telas, formularios, dashboards ou passos de navegacao existem?

### Responsividade e acessibilidade
Pergunta: Existe exigencia minima de mobile, desktop, responsividade ou acessibilidade?

### Atalho de execucao do MVP
Pergunta: No desenvolvimento do MVP, precisa criar `run-mvp.cmd` e `run-mvp.command` para abrir o frontend web? Responda apenas `sim` ou `nao`.

---

## Bloco `overlay_offline_sync`
Tipo: `overlay_block`
Perguntar quando: `runtime = offline_first` ou `continuity_need >= 3`

### Fonte de verdade
Pergunta: Qual e a fonte oficial de verdade quando houver sincronizacao?

### Conflito
Pergunta: Como conflitos de sincronizacao devem ser resolvidos?

### Janela de sincronizacao
Pergunta: Quando e como os dados devem sincronizar?

---

## Bloco `overlay_integrations_heavy`
Tipo: `overlay_block`
Perguntar quando: `integration_intensity = many`

### Sistemas e owners
Pergunta: Quais sistemas externos existem e quem responde por cada um?

### Contratos e limites
Pergunta: Existem SLA, rate limit, dependencia de arquivos, filas ou janelas de integracao?

### Monitoramento de integracao
Pergunta: Como falhas de integracao serao detectadas e tratadas?

---

## Bloco `overlay_security_strong`
Tipo: `overlay_block`
Perguntar quando: `data_risk = high` ou compliance forte

### Criptografia
Pergunta: Quais dados exigem criptografia em transito, repouso ou mascaramento?

### Auditoria forte
Pergunta: Quais eventos sensiveis precisam de trilha completa?

### Acoes privilegiadas
Pergunta: Quais acoes exigem elevacao, dupla aprovacao ou controle reforcado?

---

## Bloco `overlay_ops_advanced`
Tipo: `overlay_block`
Perguntar quando: `delivery_type = critical_system` ou `ops_need >= 4`

### Nivel de servico
Pergunta: Existe SLA, SLO, RTO ou RPO esperado?

### Alertas e incidente
Pergunta: Quais alertas sao acionaveis e qual e o fluxo de incidente?

### Rollback
Pergunta: Como sera feita a reversao de falha em release?

---

## Bloco `overlay_multi_tenant`
Tipo: `overlay_block`
Perguntar quando: `audience_model = multi_tenant`

### Isolamento
Pergunta: Como dados, configuracoes e acessos serao segregados por tenant?

### Onboarding e offboarding
Pergunta: Como um tenant entra e sai da plataforma?

### Configuracao por tenant
Pergunta: O que pode variar por tenant sem quebrar o core?

---

## Bloco `overlay_ai_hitl`
Tipo: `overlay_block`
Perguntar quando: `ai_usage = assistive|automated_with_hitl`

### Escopo dos agentes
Pergunta: Quais atividades poderao ser assistidas ou executadas por IA/agentes?

### Tarefas proibidas
Pergunta: Quais acoes os agentes nao podem executar de forma autonoma?

### Checkpoints humanos
Pergunta: Em quais pontos a aprovacao humana sera obrigatoria?

### Auditoria
Pergunta: Como prompts, outputs, aprovacoes e falhas serao registrados?

---

## Bloco `overlay_low_code_workflow`
Tipo: `overlay_block`
Perguntar quando: `interaction_model = workflow_automation`

### Plataforma
Pergunta: Qual plataforma low-code ou workflow sera usada?

### Promocao
Pergunta: Como ambientes, pacotes e versoes serao promovidos?

### Limites
Pergunta: Quais limites da plataforma influenciam arquitetura, dados e integracoes?

---

## Gate de fechamento do Motor Final

Antes de gerar o blueprint final, confirme:

- [ ] Todos os blocos `core_always` foram perguntados
- [ ] Exatamente um `preset_block` foi executado
- [ ] Todos os overlays ativos foram executados
- [ ] `skipped_modules` foram registrados com motivo
- [ ] `depth_profile` continua coerente com o risco do projeto
- [ ] Tudo que segue pendente foi marcado como `[PENDENTE]`
