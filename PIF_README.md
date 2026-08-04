# Project Inception Workflow - Porta de Entrada

## Prompt inicial sugerido

Use este prompt para iniciar:

`Leia o PIF_README.md`

## Papel deste arquivo

Este repositorio agora guarda apenas o nucleo deterministico do PIF/Planroot:

- banco de perguntas com 3 a 5 respostas substantivas por pergunta;
- matriz deterministica de decisao;
- roteador executavel;
- testes e validacoes da entrevista.

Nao existe frontend operacional neste projeto. A entrevista deve ser conduzida pelo banco de perguntas e pelo roteador CLI.

## Ordem de trabalho recomendada

1. Ler `PIF_Project-Initiation-Framework.md`.
2. Tratar o Guia Mestre como fonte unica de verdade.
3. Ler `PIF_Decision_Matrix.md` e `PIF_Decision_Matrix.json`.
4. Ler `PIF_Motor_Inicial.md` e `PIF_Motor_Final.md`.
5. Usar `app/pif_question_bank.py` como catalogo executavel de respostas deterministicas.
6. Validar o banco com `tools/pif_validate_question_bank.py`.
7. Validar o roteamento com `tools/pif_test_routing.py`.

## Como validar

```powershell
python tools\pif_validate_question_bank.py
python tools\pif_test_routing.py
python tools\pif_test_blueprint.py
```

O primeiro comando garante que:

- toda pergunta tem de 3 a 5 respostas;
- nenhuma resposta cai nos textos genericos antigos;
- cada resposta contribui para sinal ou classificador.

O segundo comando garante que:

- a matriz carrega;
- os cenarios oficiais passam;
- preset, overlays, profundidade e perfis iniciais permanecem coerentes.

O terceiro comando garante que:

- o blueprint nasce do mais basico possivel (parcimonia);
- preset e overlay inativos nao aparecem;
- `[PENDENTE]` so aparece em bloco ativo;
- o anexo `Para versao completa` so aparece quando `scope_target` pede.

## Uso do roteador

Entrada por `classifiers`:

```powershell
python tools\pif_router.py --input caminho\classificadores.json
```

Entrada por `answers` da entrevista:

```json
{
  "answers": {
    "project_name": "approved_name",
    "delivery_type": "commerce_experience",
    "interaction_model": "ui_rich"
  }
}
```

```powershell
python tools\pif_router.py --input caminho\answers.json
```

## Geracao de blueprint

```powershell
python tools\pif_build_blueprint.py --input caminho\answers.json --output blueprint.md
```

O blueprint nasce do MVP. Ele so cresce quando:

- existe resposta para a pergunta;
- a matriz ativou o bloco (preset/overlay).

Para abrir o anexo `Para versao completa`, basta responder `scope_target` com uma opcao alem do MVP.
## Invariantes

- Exatamente um `primary_preset` por projeto.
- `depth_profile` sempre em `lite | standard | strict`.
- `core_always` nunca e removido.
- Resposta ausente continua virando pendencia explicita.
- Toda mudanca de matriz precisa passar no validador e no runner de roteamento.

## Regra de precedencia

Se houver conflito entre este arquivo e qualquer outro artefato, `PIF_Project-Initiation-Framework.md` prevalece.
