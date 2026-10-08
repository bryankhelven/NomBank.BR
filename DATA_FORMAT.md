# Formato dos dados

Os JSONs por lema contêm `lemma` e `senses`. Cada acepção apresenta o roleset em `pt_roleset`, a descrição disponível, os frames e todas as instâncias em `examples`. Esse campo reúne os dados completos; o limite de dois exemplos se aplica apenas à apresentação na página.

`predicate` identifica REL. `spans` identifica os argumentos por papel, como `Arg0` e `Arg1`. `token_ids` referencia os tokens da sentença. `char_start` e `char_end` são offsets de caracteres no texto original, com início inclusivo e fim exclusivo. `head_token_id`, quando presente, registra o núcleo explicitamente anotado. Um argumento sem realização tem uma lista de spans vazia e realização nula.

`annotation_status` distingue `annotated` (argumentos anotados) de `not_started` (argumentos ainda não anotados). A identificação do predicador está disponível em ambos os casos. Valores nulos representam informação ausente; não expressam uma nova análise semântica.

`instance_id`, `sent_ID` e os identificadores de frame permitem relacionar os dados. Os identificadores de token preservam a segmentação do corpus. As marcações não incluem pontuação ou palavras adicionais por conveniência visual.

Em `jsons/instances.jsonl`, cada linha contém uma instância e os identificadores de seus tokens marcados. `tokens[].labels` registra `REL` e os papéis ARG aplicáveis. Os demais tokens não recebem marcação nessa instância. A sentença completa e sua análise UD estão em `data/sentences.jsonl`, relacionadas por `sent_ID` e pelo campo `id` da sentença. As dependências sintáticas não substituem os papéis semânticos. As descrições e os links dos frames de origem aparecem no inventário e nos JSONs por lema quando disponíveis.

Rolesets com código existente conservam esse código. Quando não há código de roleset disponível, a interface apresenta uma acepção numerada do lema, sem atribuir um código de roleset novo.
