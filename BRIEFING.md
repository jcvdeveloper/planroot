# Briefing inicial do PIF

O PIF faz 110 perguntas. A maioria cai em duas categorias:

- **Classificadores** — os 7 campos estruturais (`delivery_type`, `interaction_model`, `runtime`, `audience_model`, `integration_intensity`, `data_risk`, `ai_usage`). Eles definem preset, overlays e profundidade.
- **Conteúdo** — problema, usuários, escopo, dados, segurança, qualidade, continuidade. Eles preenchem o blueprint.

Um briefing inicial curto, escrito em prosa + poucas linhas objetivas, costuma desbloquear 70-80% das respostas dos classificadores e dar o esqueleto do conteúdo. O resto é confirmação na entrevista.

---

## Modelo curto (cola)

Copie o bloco abaixo, preencha em uma página, e use como entrada inicial.

```
# Projeto
- Nome (provisório ou definitivo):
- Sponsor (quem responde pelo projeto):
- Contexto de negócio (1-2 frases):

# Problema e valor
- Problema central que estamos resolvendo:
- Resultado esperado (outcome de negócio):
- Como vamos medir sucesso:
- Por que isso vale o investimento (receita, custo, risco, compliance):

# Usuários e fluxos
- Quem usa e em qual contexto:
- 1 a 3 fluxos críticos:
- O que existe hoje (planilha, sistema, processo manual, nada):

# Escopo e restrições
- Objetivo do produto (1 frase):
- MVP em 3 a 5 bullets:
- O que está fora do MVP:
- Prazo e restrições de equipe/orçamento:

# Dados, acesso e riscos
- Dados que entram/saem e onde moram:
- Sensibilidade (PII, financeiro, saúde, nenhum):
- Compliance mínimo (LGPD, PCI, SOX, nenhum):
- O que acontece se o sistema falhar ou vazar:

# Pistas técnicas (se já souber — chute informado serve)
- Tipo de entrega: produto interno, app para cliente, API, automação, painel, marketplace
- Como o usuário interage: UI rica, UI leve, API, batch/eventos
- Onde roda: cloud, on-prem, híbrido, local sem rede
- Conectividade: sempre online, intermitente, isolado
- Escala de usuários: piloto, time, área, empresa, público
- Integrações: poucas e conhecidas, várias e instáveis, missão crítica
- Multi-tenant: sim, não, ainda não sei
- IA no fluxo: nenhuma, assistente, agente autônomo
- Continuidade: pode parar horas, precisa de SLA, precisa de DR
```

---

## Exemplo preenchido

```
# Projeto
- Nome: Hub de Pedidos B2B
- Sponsor: Diretoria Comercial
- Contexto de negócio: Representantes recebem pedidos por WhatsApp e e-mail
  e digitam à mão no ERP. Hoje vira 1.500 pedidos/mês com erro e atraso.

# Problema e valor
- Problema central: Pedidos B2B chegam por canais não estruturados e
  viram retrabalho no backoffice.
- Resultado esperado: Tempo médio de registro cair de 2h para <15min e
  taxa de erro de digitação abaixo de 1%.
- Métrica de sucesso: tempo médio de registro + % de pedidos sem ajuste manual.
- Valor: redução de custo operacional + menos perda de venda por atraso.

# Usuários e fluxos
- Usuários: 30 representantes externos (celular) + 5 analistas de backoffice (desktop).
- Fluxos críticos: (1) representante envia pedido, (2) cliente confirma,
  (3) pedido vira ordem no ERP.
- Hoje: WhatsApp → planilha → ERP, com conferências manuais.

# Escopo e restrições
- Objetivo: registrar pedidos B2B de forma estruturada, do canal à ordem no ERP.
- MVP: app mobile para representante, fila de pedidos, integração com 1 ERP.
- Fora do MVP: cotação, comissão, BI avançado.
- Prazo: 90 dias para MVP; equipe 1 PM + 2 devs + 1 designer.

# Dados, acesso e riscos
- Dados: pedidos, clientes B2B, itens, condições comerciais.
- Sensibilidade: médio (PII + valor financeiro).
- Compliance: LGPD; sem PCI no MVP.
- Impacto se falhar: atraso no faturamento, não é catastrófico.

# Pistas técnicas
- Tipo: app para cliente (representantes) + produto interno (backoffice).
- Interação: UI rica no desktop, UI leve no mobile.
- Runtime: cloud.
- Conectividade: sempre online (celular com 4G).
- Escala: 30-50 usuários no MVP, escala para 200 em 12 meses.
- Integrações: ERP (1), WhatsApp Business API (1), poucas e conhecidas.
- Multi-tenant: não (uma única empresa).
- IA: nenhuma no MVP.
- Continuidade: pode parar horas; sem DR forte no MVP.
```

---

## O que este exemplo destrava

Sem rodar o roteador, dá para prever:

- **Preset principal**: `commerce_frontend_app` (UI rica + commerce + integrações) ou
  `cloud_corporate_integrated` (cloud + ERP + LGPD). A entrevista confirma.
- **Depth profile**: `standard` (risco médio, cloud, sem IA/autonomia).
- **Overlays prováveis**: `frontend_light` (mobile + desktop) e `integrations_heavy`
  (se a integração com ERP for crítica). `multi_tenant`, `security_strict`,
  `ops_advanced` e `agent_autonomy` ficam desligados no MVP.
- **Blueprint**: sai enxuto — identidade, problema, usuários, escopo, dados,
  produto, arquitetura mínima, segurança básica, qualidade e continuidade leve.

## O que ainda precisa ser perguntado

Mesmo com o briefing, a entrevista ainda é necessária para:

- confirmar e refinar cada classificador;
- capturar nuances que não cabem em prosa (ex: política de segredo, versionamento de contrato, janela de sync);
- fechar critérios de aceite e Definition of Done;
- mapear quem é o owner de continuidade.

Regra de ouro: **briefing bom não substitui a entrevista, ele só reduz o tempo dela.**
