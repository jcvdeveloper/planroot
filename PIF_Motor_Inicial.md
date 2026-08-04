# Project Initiation Framework - Motor Inicial (V3)

## Objetivo
Capturar o nucleo obrigatorio do projeto e os classificadores que vao decidir preset, overlays e profundidade da entrevista.

## Regras
- Sempre executar todos os blocos `core_always`.
- Sempre executar o bloco `classifier`.
- Nao inventar respostas ausentes. Marcar como `[PENDENTE]`.
- Antes de cada bloco, explicar rapidamente o que uma boa resposta precisa conter.

---

## Bloco `core_identity`
Tipo: `core_always`
Profundidade base: `lite`

### Nome do projeto
Pergunta: Qual e o nome do projeto?

### Sponsor
Pergunta: Quem responde pelo projeto e tem poder real de aprovacao?

### Aprovadores
Pergunta: Quem aprova produto, orcamento, seguranca e entrada em uso?

---

## Bloco `core_problem_value`
Tipo: `core_always`
Profundidade base: `lite`

### Problema central
Pergunta: Qual problema real precisa ser resolvido?

### Resultado esperado
Pergunta: O que precisa mudar para considerar a iniciativa bem-sucedida?

### Urgencia
Pergunta: Por que isso precisa acontecer agora?

### Metrica de sucesso
Pergunta: Como o sucesso sera medido?

### Hipotese de valor
Pergunta: Qual ganho, economia, reducao de risco ou melhoria operacional se espera obter?

---

## Bloco `core_users_process`
Tipo: `core_always`
Profundidade base: `lite`

### Contexto de negocio
Pergunta: Em que area, processo ou operacao esse projeto se encaixa?

### Usuarios principais
Pergunta: Quem usa, opera, aprova ou depende do resultado?

### Fluxos criticos
Pergunta: Quais sao os 3 a 5 fluxos mais importantes?

### Processo atual
Pergunta: Como isso funciona hoje, na pratica?

### Gargalos e excecoes
Pergunta: Onde o processo quebra, atrasa, retrabalha ou funciona em excecao?

---

## Bloco `core_scope_constraints`
Tipo: `core_always`
Profundidade base: `lite`

### Objetivo do produto
Pergunta: Qual transformacao minima o produto precisa entregar?

### Escopo MVP
Pergunta: O que obrigatoriamente entra no MVP?

### Nao escopo
Pergunta: O que fica explicitamente fora desta fase?

### Prazo
Pergunta: Existe marco fixo ou janela de entrega relevante?

### Capacidade e restricoes
Pergunta: Quais limitacoes de time, orcamento, stack ou fornecedor ja existem?

### Dependencias externas
Pergunta: O projeto depende de terceiros, integracao externa ou aprovacao externa?

---

## Bloco `core_data_access`
Tipo: `core_always`
Profundidade base: `lite`

### Perfil de acesso
Pergunta: Ja existe alguma separacao entre administrador, operador, aprovador, leitor ou auditor?

### Dados manipulados
Pergunta: Que tipos de dados a solucao vai manipular ou armazenar?

### Sensibilidade
Pergunta: Esses dados sao sensiveis, pessoais, financeiros ou sigilosos?

### Impacto de perda
Pergunta: O que acontece se dados forem perdidos, corrompidos ou ficarem indisponiveis?

### Compliance basico
Pergunta: Existe exigencia legal, contratual ou regulatoria relevante?

### Riscos principais
Pergunta: Quais riscos mais preocupam hoje?

---

## Bloco `classifier_block`
Tipo: `classifier`
Profundidade base: `lite`

### Tipo de entrega
Pergunta: O projeto e mais proximo de prototipo, servico de discovery/design, ferramenta interna, sistema de negocio ou sistema critico?

### Modelo principal de interacao
Pergunta: O uso principal sera interface rica, backoffice simples, API/servico, automacao/workflow ou misto?

### Runtime
Pergunta: A solucao deve rodar localmente, offline-first, on-prem, cloud ou hibrido?

### Perfil de conectividade
Pergunta: O uso sera sempre online, intermitente ou majoritariamente offline?

### Escala de usuarios
Pergunta: O uso sera individual, equipe pequena, multi-area ou corporativo?

### Intensidade de integracoes
Pergunta: Havera nenhuma, poucas ou muitas integracoes relevantes?

### Risco dos dados
Pergunta: O risco de dados e baixo, medio ou alto?

### Criticidade operacional
Pergunta: A operacao tolera falha com facilidade ou e de alta criticidade?

### Uso de IA
Pergunta: Havera nenhum uso de IA, uso assistivo ou automacao com HITL?

### Modelo de isolamento
Pergunta: A solucao atende um unico contexto, varias unidades ou varios tenants/clientes?

### Estilo de plataforma
Pergunta: O projeto sera custom code, low-code/workflow ou misto?

---

## Gate de fechamento do Motor Inicial

Antes de seguir para o Motor Final, confirme:

- [ ] Todos os blocos `core_always` foram perguntados
- [ ] O bloco `classifier` foi preenchido
- [ ] Ja existe um `primary_preset` candidato
- [ ] Ja existem `active_overlays` candidatos
- [ ] A profundidade `lite`, `standard` ou `strict` foi definida
- [ ] Itens ausentes foram marcados como `[PENDENTE]`
