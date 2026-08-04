# Project Initiation Framework - Guia Mestre (V3)

## Objetivo
Este arquivo e a fonte canonica da logica e da orquestracao do PIF. Ele existe para responder, sem ambiguidade:

- o que e obrigatorio em qualquer projeto;
- quais respostas classificam o contexto;
- qual preset principal deve ser escolhido;
- quais modulos extras devem ser ativados;
- quando aprofundar ou simplificar a entrevista;
- qual a ordem oficial de leitura e execucao;
- como evitar que a logica falhe em casos atipicos.

---

## Papeis dos arquivos

- `PIF_README.md`: porta de entrada entre interacao humana e LLM
- `PIF_Project-Initiation-Framework.md`: fonte canonica da logica e da orquestracao
- `PIF_Decision_Matrix.md`: matriz deterministica legivel por humanos
- `PIF_Decision_Matrix.json`: matriz deterministica machine-readable
- `PIF_Preset_Catalog.md`: regras de selecao do preset principal
- `PIF_Module_Matrix.md`: matriz de ativacao dos blocos
- `PIF_Motor_Inicial.md`: nucleo + classificadores
- `PIF_Motor_Final.md`: nucleo final + blocos por preset e overlay
- `PIF_Simulation_Scenarios.md`: cenarios humanos de validacao
- `PIF_Routing_Test_Cases.json`: casos machine-readable para simulacao

Precedencia:

1. regras deste Guia Mestre;
2. matriz de decisao deterministica;
3. catalogo de presets e matriz de modulos;
4. motores de perguntas;
5. blueprints de consolidacao.

---

## Entrada oficial

Prompt inicial sugerido:

`Leia o PIF_README.md`

Ao receber esse prompt:

1. ler `PIF_README.md`;
2. ler imediatamente `PIF_Project-Initiation-Framework.md`;
3. seguir a orquestracao oficial definida neste Guia Mestre;
4. consultar os demais arquivos apenas quando este Guia Mestre determinar.

Entrada operacional recomendada:

1. ler o banco de perguntas em `app/pif_question_bank.py`;
2. conduzir a entrevista pelo banco deterministico e registrar detalhes em texto livre fora da matriz;
3. validar o banco com `tools/pif_validate_question_bank.py`;
4. validar o roteamento com `tools/pif_test_routing.py`.

---

## Ordem oficial de leitura

1. Ler `PIF_README.md`.
2. Ler `PIF_Project-Initiation-Framework.md`.
3. Ler `PIF_Decision_Matrix.md`.
4. Ler `PIF_Decision_Matrix.json`.
5. Ler `PIF_Preset_Catalog.md`.
6. Ler `PIF_Module_Matrix.md`.
7. Executar os blocos `core_always` e `classifier` do `PIF_Motor_Inicial.md`.
8. Resolver `primary_preset`, `active_overlays` e `depth_profile`.
9. Executar os blocos `core_always`, depois o bloco do preset e depois os overlays do `PIF_Motor_Final.md`.
10. Consolidar o blueprint inicial a partir de `answers`, `signals`, `primary_preset`, `active_overlays` e `blueprint_profile`.
11. Validar o roteamento com `tools/pif_validate_question_bank.py`, `PIF_Simulation_Scenarios.md` e `PIF_Routing_Test_Cases.json`.
12. Perguntar o diretorio de saida, apresentar a proposta e, so depois da aprovacao, salvar os artefatos finais.

---

## Regras operacionais da entrevista

- Sempre apresentar um disclaimer curto antes de cada pergunta ou bloco.
- Sempre aguardar resposta antes de avancar.
- Nunca inventar informacoes ausentes.
- Sempre marcar ausencia como `[PENDENTE]`.
- Sempre separar fato confirmado de `Assuncao sugerida`.
- Nunca pedir segredos reais, credenciais, tokens, dumps de producao ou dados pessoais desnecessarios.
- Sempre explicitar contradicoes entre entrevistados.

---

## O que nunca pode ser pulado

Mesmo em caso simples, sempre cobrir:

- problema, objetivo e metrica de sucesso;
- sponsor, aprovadores e owner de continuidade;
- usuarios principais e fluxos criticos;
- escopo MVP e nao escopo;
- dados manipulados e impacto de perda ou corrupcao;
- quem acessa e quem aprova;
- validacao, aceite e suporte pos-entrega;
- riscos principais e dependencias externas.

Esses itens continuam obrigatorios mesmo quando a profundidade for `lite`.

---

## Regra oficial para salvar as saidas

Ao final da entrevista aprovada, a saida deve ser salva em ordem de execucao, com pastas numeradas e um `README.md` na raiz.

### Estrutura padrao

```text
<diretorio_de_saida>/
|-- README.md
|-- 1. discovery/
|-- 2. prd-produto/
|-- 3. arquitetura-solucao/
|-- 4. dados-e-integracoes/
|-- 5. seguranca-e-compliance/
|-- 6. qualidade-e-testes/
|-- 7. devops-e-deploy/
|-- 8. operacao-e-observabilidade/
|-- 9. backlog-e-roadmap/
`-- 10. agents-e-governanca/
```

### Conteudo minimo do README final

- objetivo do projeto;
- ordem recomendada de leitura;
- o que existe em cada pasta;
- owners e aprovadores;
- dependencias externas;
- pendencias criticas;
- avisos gerais nao tecnicos relevantes;
- limites de automacao e HITL.

---

## Fluxo de aprovacao

1. Entrevistar usando `core_always` e `classifier`.
2. Definir `primary_preset`, `active_overlays` e `depth_profile`.
3. Entrevistar usando `core_always`, o bloco do preset e os overlays ativos.
4. Consolidar nos blueprints.
5. Verificar coerencia com os cenarios de simulacao.
6. Validar o blueprint de agentes em modo estrito.
7. Apresentar a proposta de saida.
8. Se aprovado, gerar artefatos e salvar.
9. Se nao aprovado, revisar pendencias, ajustar e submeter novamente.

---

## Avisos gerais nao tecnicos que devem aparecer quando relevantes

- dependencia de sponsor ou aprovador unico;
- prazo imposto sem validacao tecnica;
- escopo instavel ou mal definido;
- dependencia forte de fornecedor externo;
- risco de baixa adesao do usuario;
- falta de baseline para medir sucesso;
- ausencia de owner de operacao;
- uso de IA ou agentes em contexto sensivel sem HITL claro.

---
## Invariantes do framework

### 1. Nao inventar
Informacao ausente deve ser registrada como `[PENDENTE]`.

### 2. Core sempre existe
O nucleo minimo nunca pode ser removido. Apenas sua profundidade muda.

### 3. Simplicidade com guarda-corpo
Contexto simples reduz profundidade, mas nunca elimina ownership, dados, aceite, risco e continuidade.

### 4. Maior risco prevalece
Quando houver conflito entre simplicidade e protecao, vale a regra mais conservadora para:

- dados sensiveis;
- acesso privilegiado;
- auditoria;
- continuidade;
- operacao critica.

### 5. Um preset principal por projeto
Cada entrevista deve terminar com exatamente um `primary_preset`.

### 6. Overlays acumulativos
Os overlays sao complementares e podem coexistir.

---

## Taxonomia oficial

### Tipos de bloco

- `core_always`: sempre perguntar
- `classifier`: sempre perguntar para definir roteamento
- `preset_block`: perguntar apenas se `primary_preset` corresponder
- `overlay_block`: perguntar apenas se o overlay estiver ativo

### Niveis de profundidade

- `lite`: pequeno porte, baixo risco, baixa criticidade, poucas integracoes
- `standard`: caso normal
- `strict`: dado sensivel, alto impacto, operacao relevante, forte compliance, on-prem complexo ou cloud corporate

---

## Nucleo obrigatorio

As perguntas abaixo formam o nucleo invariavel do framework:

### Identidade e ownership
- nome do projeto;
- sponsor;
- aprovadores;
- owner de operacao / continuidade.

### Problema e valor
- problema real;
- urgencia;
- resultado esperado;
- metrica de sucesso;
- hipotese de valor.

### Usuarios e processo
- usuarios principais;
- fluxos criticos;
- processo atual;
- gargalos e excecoes.

### Escopo e restricoes
- MVP;
- nao escopo;
- prazo;
- capacidade;
- dependencias externas.

### Dados e acesso
- dados manipulados;
- sensibilidade;
- impacto de perda/corrupcao;
- quem acessa ou aprova.

### Validacao e continuidade
- como validar;
- quem aceita;
- quem sustenta;
- riscos principais.

---

## Classificadores oficiais

Os classificadores devem ser coletados no `Motor Inicial` e consolidados em forma normalizada.

### Campos obrigatorios

- `delivery_type`
  - `prototype`
  - `design_service`
  - `internal_tool`
  - `business_system`
  - `critical_system`

- `interaction_model`
  - `ui_rich`
  - `backoffice_simple`
  - `api_service`
  - `workflow_automation`
  - `mixed`

- `runtime`
  - `local`
  - `offline_first`
  - `on_prem`
  - `cloud`
  - `hybrid`

- `audience_model`
  - `individual`
  - `small_team`
  - `multi_area`
  - `corporate`
  - `multi_tenant`

- `integration_intensity`
  - `none`
  - `few`
  - `many`

- `data_risk`
  - `low`
  - `medium`
  - `high`

- `ai_usage`
  - `none`
  - `assistive`
  - `automated_with_hitl`

Sao 7 campos. `connectivity_profile`, `tenant_model`, `operational_criticality` e
`platform_style` foram consolidados nos campos acima -- a tabela de equivalencia
e as perdas assumidas estao em `PIF_Decision_Matrix.md`, secao "Classificadores
consolidados".

---

## Pipeline de decisao

Execucao normativa:

- usar a `PIF_Decision_Matrix.md` como referencia humana
- usar a `PIF_Decision_Matrix.json` quando o roteamento precisar ser consumido por agente, script ou validacao automatizada
- se houver conflito entre a prosa abaixo e a matriz, a matriz vence

### Blueprint: do MVP, com parcimonia

O blueprint gerado pelo Planroot segue a regra do mais basico possivel:

- nasce sempre do MVP;
- so inclui uma secao de `preset_block` quando a matriz escolheu um preset;
- so inclui uma secao de `overlay_block` quando a matriz ativou o overlay;
- respostas ausentes viram `[PENDENTE]`, nunca conteudo inventado;
- quando a resposta `scope_target` aponta para versao completa, o blueprint abre um anexo `Para versao completa` listando perguntas que ainda precisam ser feitas.

### Camada executavel de roteamento

O caminho operacional principal e o banco deterministico de perguntas em `app/pif_question_bank.py` junto com o roteador CLI.

Depois de coletar respostas deterministicas, a validacao automatizada pode ser executada com:

```powershell
python tools\pif_router.py --input caminho\answers.json
```

O mesmo roteador tambem aceita entrada direta por classificadores:

```powershell
python tools\pif_router.py --input caminho\classificadores.json
```

Para validar os cenarios oficiais de regressao:

```powershell
python tools\pif_test_routing.py
```

Antes de consolidar o blueprint inicial, valide o banco de perguntas com:

```powershell
python tools\pif_validate_question_bank.py
```

As instrucoes de uso ficam no `PIF_README.md` e nos scripts em `tools/`.

### Regra das respostas deterministicas

Toda pergunta do banco executavel deve ter entre 3 e 5 respostas substantivas.

As respostas nao servem para substituir os detalhes humanos: elas servem para classificar o estado da resposta e alimentar a matriz. Nomes, exemplos, restricoes e observacoes continuam sendo registrados fora da matriz.

Resposta ausente continua virando pendencia explicita. O projeto nao usa mais a opcao generica `Nao entra no MVP` como resposta padrao do banco.

### Passo 1 - Perguntar o nucleo
Executar todos os blocos `core_always` do Motor Inicial.

### Passo 2 - Perguntar os classificadores
Executar o bloco `classifier`.

### Passo 3 - Definir profundidade base

- usar `lite` quando:
  - `audience_model = individual|small_team`
  - `integration_intensity = none|few`
  - `data_risk = low`
  - a entrega nao foi declarada critica e `ops_need` ficou abaixo de 4

- usar `strict` quando qualquer uma destas for verdadeira:
  - `data_risk = high`
  - `runtime = on_prem`
  - `audience_model = corporate`
  - `delivery_type = critical_system` ou `ops_need >= 4`
  - `integration_intensity = many`

- caso contrario, usar `standard`

### Passo 4 - Selecionar o preset principal

Aplicar na seguinte ordem:

1. se `delivery_type = prototype|design_service`, usar `design_discovery_service`
2. senao, se `runtime = offline_first` e `audience_model = individual|small_team` e `integration_intensity = none|few`, usar `local_offline_tool`
3. senao, se `runtime = on_prem`, usar `onprem_business_system`
4. senao, se `interaction_model = api_service`, usar `api_integration_service`
5. senao, se `runtime = cloud` e (`audience_model = corporate` ou `integration_intensity = many` ou `delivery_type = critical_system` ou `ops_need >= 4`), usar `cloud_corporate_integrated`
6. senao, se `runtime = cloud`, usar `cloud_business_app`
7. senao, se `runtime = local|offline_first`, usar `local_small_team_app`
8. senao, escolher o preset mais conservador compativel e registrar `Assuncao sugerida`

### Passo 5 - Ativar overlays

Ativar overlays com estas regras:

- `frontend_light`
  - ativar se `interaction_model = ui_rich|backoffice_simple|mixed`
  - inclui a pergunta operacional sim/nao sobre criar `run-mvp.cmd` e `run-mvp.command` para abrir o frontend web no desenvolvimento do MVP
  - essa resposta nao altera matriz, preset, overlays ou profundidade; ela apenas orienta empacotamento e experiencia local de execucao

- `offline_sync`
  - ativar se `runtime = offline_first` ou `continuity_need >= 3`

- `integrations_heavy`
  - ativar se `integration_intensity = many`

- `security_strong`
  - ativar se `data_risk = high`
  - ou se houver compliance/regulacao relevante
  - ou se houver aprovacao privilegiada / auditoria forte

- `ops_advanced`
  - ativar se `delivery_type = critical_system` ou `ops_need >= 4`
  - ou se houver SLA/SLO formal
  - ou se houver suporte estruturado / observabilidade forte

- `multi_tenant`
  - ativar se `audience_model = multi_tenant`

- `ai_hitl`
  - ativar se `ai_usage = assistive|automated_with_hitl`

- `low_code_workflow`
  - ativar se `interaction_model = workflow_automation` e o produto depender fortemente dessa plataforma

### Passo 6 - Executar o Motor Final

No Motor Final, sempre seguir esta ordem:

1. blocos `core_always`
2. bloco `preset_block` do `primary_preset`
3. todos os `overlay_block` ativos
4. registrar blocos pulados em `skipped_modules`

---

## Presets oficiais desta versao

- `design_discovery_service`
- `local_offline_tool`
- `local_small_team_app`
- `api_integration_service`
- `onprem_business_system`
- `cloud_business_app`
- `cloud_corporate_integrated`

Os detalhes de uso e anti-uso estao no `PIF_Preset_Catalog.md`.

---

## Overlays oficiais desta versao

- `frontend_light`
- `offline_sync`
- `integrations_heavy`
- `security_strong`
- `ops_advanced`
- `multi_tenant`
- `ai_hitl`
- `low_code_workflow`

Os blocos correspondentes estao mapeados no `PIF_Module_Matrix.md`.

---

## Regras de fallback

### Se o classificador estiver incompleto

- manter todos os `core_always`
- marcar classificadores ausentes como `[PENDENTE]`
- escolher o preset mais conservador compativel
- ativar pelo menos:
  - `security_strong` se houver qualquer indicio de dado sensivel
  - `ops_advanced` se houver qualquer indicio de alta criticidade

### Se duas rotas parecerem validas

- escolher a de maior restricao operacional;
- registrar a alternativa descartada em `Assuncao sugerida`.

### Se o projeto misturar discovery e implementacao

- usar o preset do entregavel predominante;
- ativar overlays para o restante.

Exemplo:
- pesquisa + prototipo navegavel sem build final -> `design_discovery_service` + `frontend_light`
- app cloud com trilha forte de descoberta -> `cloud_business_app` + uso intensivo de blocos de discovery no core

---

## Regras de consolidacao

Ao finalizar a entrevista:

1. preencher o blueprint humano com:
   - classificadores;
   - `primary_preset`;
   - `active_overlays`;
   - `depth_profile`;
   - `skipped_modules` e motivo.
2. preencher o blueprint de agentes com a mesma estrutura, em formato legivel por automacao.
3. nao esconder pendencias.

---

## Checklist de validade logica

- [ ] O projeto recebeu exatamente um `primary_preset`
- [ ] O preset escolhido e compativel com runtime e tipo de entrega
- [ ] Overlays foram ativados por regra clara, nao por intuicao vaga
- [ ] Nenhum bloco de risco, acesso ou continuidade foi removido
- [ ] `depth_profile` foi definido
- [ ] `skipped_modules` foram registrados com motivo
- [ ] O resultado faz sentido frente aos cenarios de simulacao

