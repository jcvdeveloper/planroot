# Planroot

Planroot e o sucessor do **Project Initiation Framework (PIF3)** com nova marca.
E um framework deterministico e open para transformar uma ideia de projeto em um blueprint executavel, usando uma entrevista estruturada, uma matriz de decisao reproduzivel e um roteador executavel.

Este repositorio contem **apenas o nucleo logico** necessario para validar e evoluir a matriz deterministica de perguntas. Frontend, instaladores e o app local ficam em outros diretorios.

> Renomeacao de marca em andamento. Os arquivos internos ainda usam o prefixo `PIF_` por compatibilidade. Renomear e tarefa separada e nao foi feita para nao poluir esta entrega.

## Estrutura

```
Planroot/
|-- README.md                              este arquivo
|-- PIF_README.md                          porta de entrada do framework
|-- PIF_Project-Initiation-Framework.md    Guia Mestre - spec canonica da logica e orquestracao
|-- PIF_Decision_Matrix.md                 matriz deterministica (legivel por humanos)
|-- PIF_Decision_Matrix.json               matriz deterministica (legivel por maquina)
|-- PIF_Motor_Inicial.md                   nucleo + classificadores (perguntas iniciais)
|-- PIF_Motor_Final.md                     nucleo final + blocos por preset/overlay
|-- PIF_Preset_Catalog.md                  regras dos presets oficiais
|-- PIF_Module_Matrix.md                   regras de ativacao dos overlays
|-- PIF_Routing_Test_Cases.json            casos oficiais de teste do roteador
|-- PIF_Simulation_Scenarios.md            cenarios humanos de validacao
|-- app/
|   `-- pif_question_bank.py               banco de perguntas deterministico (QUESTIONS, OPTION_INDEX)
`-- tools/
    |-- pif_router.py                      roteador deterministico (answers/classifiers -> sinais + preset + overlays + profundidade)
    |-- pif_test_routing.py                runner de testes de regressao do roteador
    |-- pif_build_blueprint.py             renderizador parcimonioso de blueprint a partir de answers
    |-- pif_test_blueprint.py              runner de testes do blueprint parcimonioso
    `-- pif_validate_question_bank.py      valida opcoes 3-5 por pergunta e detecta respostas genericas
```

## O que NAO esta aqui

Por decisao, esta pasta nao contem nada de frontend, instalacao ou runtime:

- nenhum `frontend/`, `app-front/`, `app-local/`
- nenhum `PIF_INSTALL.cmd`, `PIF_INSTALL.command`, `PIF_RUN_FRONTEND.*`
- nenhum `schemas/`, `install/`, `requirements.txt`
- nenhum arquivo de output (`PIF_HUMAN_Master-Blueprint.md`, `PIF_AGENTS_Master-Blueprint.json`, `PIF_BLUEPRINT_VALIDATION.md`)
- nenhum `memory/`, `.gitignore`, `VER_APOS_CLONAR.md`, `FIP_ROADMAP_PUBLIC_DEPLOY.md`

Esses artefatos vivem no repositorio legado em `D:\Worthness\FIP3\` e podem ser migrados em ondas seguintes, sob demanda.

## Ordem de leitura recomendada

1. `PIF_README.md` - porta de entrada
2. `PIF_Project-Initiation-Framework.md` - Guia Mestre (fonte canonica)
3. `PIF_Decision_Matrix.md` e `PIF_Decision_Matrix.json` - a matriz em si
4. `PIF_Preset_Catalog.md` e `PIF_Module_Matrix.md` - o que a matriz consulta
5. `PIF_Motor_Inicial.md` e `PIF_Motor_Final.md` - o banco de perguntas organizado por fase
6. `app/pif_question_bank.py` - banco executavel com respostas deterministicas por pergunta
7. `tools/pif_router.py` - como a matriz agrega respostas, sinais, preset, overlays e profundidade
8. `app/pif_blueprint.py` e `tools/pif_build_blueprint.py` - blueprint parcimonioso em Markdown

## Como rodar a validacao da matriz

A matrix e validavel hoje, sem frontend e sem internet. Apos o Python 3.11+ disponivel:

```powershell
python tools\pif_test_routing.py
python tools\pif_test_blueprint.py
python tools\pif_validate_question_bank.py
```

O comando:

 - carrega `PIF_Decision_Matrix.json`;
- valida que toda pergunta tem 3 a 5 respostas substantivas;
- executa todos os casos em `PIF_Routing_Test_Cases.json` e `PIF_Blueprint_Test_Cases.json`;
- compara `primary_preset`, `depth_profile`, `active_overlays` e, quando definido, `blueprint_profile` com o esperado;
- garante que o blueprint respeita parcimônia (sem preset/overlay inativo, sem `[PENDENTE]` em blocos desligados);
- retorna `0` se todos os casos passam, `1` se algum falha.

Para rodar o roteador contra um payload arbitrario de `answers` ou `classifiers` (debug):

```powershell
cd D:\Worthness\Planroot
python tools\pif_router.py --input answers.json
```

## Invariantes a preservar durante a validacao

Estes pontos sao invariantes do framework e nao podem ser quebrados por nenhuma edicao:

- Exatamente um `primary_preset` por projeto.
- `depth_profile` em `lite | standard | strict` definido para todo caso.
- `core_always` nunca e removido, apenas muda de profundidade.
- `[PENDENTE]` continua sendo o marcador padrao de informacao ausente.
- `Assuncao sugerida` continua marcando tudo que veio do agente.
- Toda matriz nova precisa passar no `pif_test_routing.py` antes de virar canonica.

## Pendencias conhecidas

- Renomear arquivos `PIF_*` para `Planroot_*` (nao bloqueia).
- Atualizar caminhos hardcoded em `pif_router.py` e `pif_test_routing.py` caso a estrutura mude (hoje ambos assumem `PIF_Decision_Matrix.json` e `PIF_Routing_Test_Cases.json` na raiz desta pasta).
- Decidir destino da pasta legada `D:\Worthness\FIP3\` apos validacao.
