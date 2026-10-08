# Formato dos dados

## JSON por lema

O formato `nombank-br/2.1` organiza os dados em `lemma` e `senses`, seguindo a organização do NounBank.DS Expanded. Cada acepção contém:

| Campo | Significado |
| --- | --- |
| `pt_roleset` | Código existente do roleset nominal; `null` quando não há código disponível. |
| `sense_label` | Rótulo da acepção, presente quando não há código de roleset. Não constitui um roleset novo. |
| `description` | Descrição do roleset sustentada por autoridade de frame; `null` quando essa descrição não está documentada. Glosas lexicais não preenchem esse campo. |
| `frame_description` | Descrição do frame associado, somente quando disponível e diferente da descrição da acepção. |
| `origin_frames` | Referências de origem: recurso, roleset original, glossa original (`gloss`), URL e indicação de adaptação, quando disponíveis. Uma lista vazia indica ausência de referência registrada. |
| `roles` | Inventário de papéis semânticos: `id` (Arg0, Arg1 etc.), `desc` e `definition`. `null` indica inventário ainda não disponível. |
| `instances` | Todas as instâncias do lema nessa acepção, inclusive aquelas ainda sem anotação de argumentos. |
| `syntactic_profile` | Frequência das relações sintáticas observadas para cada papel. |

O limite de dois exemplos vale somente para a apresentação na página. Os arquivos JSON, JSONL e ZIP contêm todas as instâncias. Uma descrição nula de papel não significa que o papel inexiste. Rolesets com código existente conservam esse código. Rótulos como `lema · acepção 1` ficam em `sense_label` e aparecem como **Acepção** na interface.

O DUPB fornece evidência lexicográfica de acepções e usos, não autoridade de frames, rolesets ou papéis. A descrição de um roleset não é substituída pelo verbete de um dicionário nem pela enumeração dos papéis. As glosas originais do NomBank EN são mantidas literalmente em `origin_frames[].gloss`: nomes breves como `event` são metadados do roleset original, não descrições explicativas do frame brasileiro. Os vínculos com o recurso de origem são preservados; esta correção da apresentação não revalida nem redefine os mapeamentos científicos existentes.

## Instâncias e marcações

| Campo | Significado |
| --- | --- |
| `instance_id` | Referência legível no formato `sent_ID::lemma::n`, distinguindo predicados do mesmo lema na mesma sentença. |
| `sent_ID` | Identificador da sentença no corpus Porttinari. |
| `text` | Texto original da sentença; `null` quando indisponível. |
| `arguments_annotated` | `true` quando a anotação dos argumentos foi realizada; `false` quando ainda não foi realizada. A identificação de REL existe em ambos os casos. |
| `predicate` | REL: forma encontrada no texto (`form`) e posições de início e fim. |
| `realization` | Expressões anotadas para cada ARG. |
| `syntax` | Relações de dependência UD associadas às realizações. Pode conter uma relação ou uma lista de relações. |
| `argument_positions` | Lista de segmentos por papel, cada um com `char_start` e `char_end`. Permite localizar expressões repetidas e argumentos descontínuos. |

A numeração `n` começa em 1 e segue a ordem dos predicados do mesmo lema na sentença, considerando todas as suas acepções. A referência identifica o predicado, não o argumento. Não renumeramos as referências por seleção de exemplos ou por filtros da interface.

As posições contam caracteres Unicode (pontos de código) a partir de zero sobre `text`, sem normalizar espaços ou pontuação. `char_start` é inclusivo e `char_end` é exclusivo. Em Python, o segmento corresponde a `text[char_start:char_end]`; em JavaScript, use `Array.from(text).slice(char_start, char_end).join('')`.

```json
{
  "instance_id": "FOLHA_DOC000173_SENT051::resposta::1",
  "sent_ID": "FOLHA_DOC000173_SENT051",
  "text": "A pergunta de Josimar ainda está sem resposta.",
  "arguments_annotated": true,
  "predicate": {
    "form": "resposta",
    "char_start": 37,
    "char_end": 45
  },
  "realization": {
    "Arg0": null,
    "Arg1": "A pergunta de Josimar",
    "Arg2": null,
    "Arg3": "de Josimar"
  },
  "syntax": {
    "Arg0": null,
    "Arg1": "nsubj",
    "Arg2": null,
    "Arg3": "nmod"
  },
  "argument_positions": {
    "Arg0": [],
    "Arg1": [{"char_start": 0, "char_end": 21}],
    "Arg2": [],
    "Arg3": [{"char_start": 11, "char_end": 21}]
  }
}
```

Quando `arguments_annotated` é `true`, um ARG com realização nula e segmentos vazios não possui realização anotada nessa frase. Quando é `false`, os argumentos ainda não foram analisados: objetos vazios ou valores nulos não devem ser interpretados como ausência de argumentos. Um perfil sintático vazio também não demonstra ausência de relações.

Um predicado descontínuo pode usar `predicate.segments`, com uma lista de pares `char_start`/`char_end`, em lugar do par único. `text`, `predicate.form` e posições podem ser nulos quando a fonte estiver indisponível. As 77 instâncias anteriormente sem texto foram recuperadas no Porttinari-base UD 2.15, pelo ID exato da sentença e pela correspondência dos tokens de REL ao lema. Não houve reconstrução artificial de frases ou anotação de novos argumentos.

As posições de caracteres preservam os intervalos existentes da anotação. Uma contração pode corresponder a mais de um token UD na mesma posição textual; por isso, posições de caracteres não distinguem componentes internos de tokens de superfície compartilhados. Para reproduzir exatamente a segmentação, as marcações e os núcleos, use a exportação técnica. As expressões de `realization` também conservam a apresentação existente, que pode diferir do recorte literal em pontuação ou representação de segmentos descontínuos.

## Arquivos de consulta

- `jsons/*.json`: um arquivo por lema.
- `jsons/lemmas.jsonl`: uma linha por lema, com o mesmo conteúdo dos JSONs individuais.
- `jsons/lemmas.zip`: todos os JSONs individuais.
- `jsons/instances.jsonl`: uma linha por instância, com `lemma`, `pt_roleset`, `sense_label` quando necessário e os campos da instância acima.

## Exportação técnica

`data/annotations.jsonl` preserva integralmente as anotações por tokens. Cada linha contém `lemma`, `roleset`, os identificadores originais da instância e do frame, a sentença, `annotation_status`, `predicate`, `realization`, `syntax`, `spans`, `tokens` e `public_instance_id`. Este último corresponde a `instance_id` nos arquivos de consulta.

`annotations.roleset` contém somente um código existente. Nos registros que tinham apenas um rótulo de acepção, `roleset` é nulo e `sense_label` conserva o rótulo. Isso corrige o nome do metadado, sem criar ou alterar um roleset.

- `instance_id`: identificador numérico original, usado nos inventários e nas referências das tabelas HTML.
- `frame_id`: vínculo com `id` em `data/frames.jsonl`; nulo quando não há frame atribuído.
- `annotation_status`: `annotated` ou `not_started`, correspondentes a `arguments_annotated` verdadeiro ou falso.
- `predicate.token_ids` e `spans[ARG][].token_ids`: tokens exatos marcados como REL ou ARG, sem incluir tokens adicionais por conveniência visual.
- `spans[ARG][].head_token_id`: núcleo explicitamente anotado, quando presente. Sua ausência não autoriza inferir um núcleo novo.
- `tokens`: referências aos tokens marcados; `labels` informa REL e os ARG aplicáveis. Tokens sem marcação nessa instância não são repetidos nessa lista.

`data/sentences.jsonl` contém a tokenização completa e a análise UD uma vez por sentença. Relacione `annotations.sent_ID` a `sentences.id` e os identificadores de token a `sentences.tokens[].id`. O campo UD `head` representa a dependência entre tokens; não substitui o núcleo explicitamente anotado de um ARG. As 77 sentenças recuperadas têm `source` com recurso, versão e URL fixada no commit `92658155db297cd12778021634cdbafba72df449` do repositório oficial do Porttinari. A análise das sentenças que já estavam disponíveis não foi substituída.

`data/senses.jsonl` e `data/frames.jsonl` preservam os inventários científicos e seus vínculos originais. `frames.sense_id` referencia `senses.id`; suas listas `instance_ids` referenciam os identificadores numéricos de `data/annotations.jsonl`. Identificadores de frame e acepção são chaves de associação, não descrições linguísticas.

`data/lexical_evidence.jsonl` conserva separadamente as glosas lexicais herdadas, com `sense_id`, `lemma`, `sense_label`, `text` e `resource`. `senses.lexical_evidence_id`, quando presente, referencia `lexical_evidence.sense_id`. Esses registros são evidência lexical, não definições de frame ou roleset. A fonte DUPB está identificada nos casos explicitamente documentados de “acidente” e “acusação”; nos demais registros sem identificação verificável, `resource` permanece nulo. Não se infere a autoridade de um texto por sua formatação. As glosas lexicais foram retiradas das descrições de roleset, das descrições de frame e do índice da interface.

## Migração do formato anterior

O formato 2 substitui `examples` por `instances`, remove `lemma_base` quando redundante, reúne os metadados do frame na acepção e elimina identificadores opacos e tokens dos arquivos de consulta. `arguments_annotated` explicita o estado da anotação. As posições de ARG passam a `argument_positions`; as posições de REL ficam diretamente em `predicate`. As anotações por tokens e os identificadores originais continuam disponíveis em `data/annotations.jsonl`, sem alteração das marcações científicas.

O formato 2.1 separa a evidência lexical da autoridade de frames; rótulos de acepção sem código passam de `pt_roleset` a `sense_label`, com `pt_roleset` nulo. `origin_frames[].description` passa a `origin_frames[].gloss` para representar fielmente o nome breve do roleset original. As 77 fontes ausentes foram recuperadas e os blocos HTML duplicados de um mesmo roleset foram reunidos, mantendo os argumentos ainda não anotados nesse estado.
