# NomBank.BR

Recurso de nomes predicadores do português brasileiro no corpus Porttinari, com acepções, frames, papéis semânticos e instâncias anotadas.

[Explorar o NomBank.BR](https://bryankhelven.github.io/NomBank.BR/)

O recurso reúne 1.605 lemas e 11.021 instâncias. Há 6.024 instâncias com argumentos anotados (54,66%) e 4.997 ainda sem anotação de argumentos.

## Consulta

Busque um nome e filtre por anotação, valência, papel semântico ou realização. Cada página apresenta as descrições disponíveis, os links para os frames de origem, até dois exemplos por roleset e tabelas com todas as instâncias. REL e ARG aparecem em cores nas frases.

## Dados

- `jsons/*.json`: dados de cada lema, com todas as instâncias e marcações.
- `jsons/lemmas.jsonl` e `jsons/lemmas.zip`: conjunto completo por lema.
- `jsons/instances.jsonl`: todas as instâncias, com REL, ARG e posições no texto.
- `data/annotations.jsonl`: exportação técnica com os tokens exatos marcados e os núcleos explicitamente anotados.
- `data/senses.jsonl`, `data/frames.jsonl` e `data/sentences.jsonl`: inventários científicos e sentenças com tokenização e análise UD.
- [Formato dos dados](DATA_FORMAT.md): campos e interpretação das marcações.

Os arquivos de consulta usam referências legíveis para distinguir instâncias do mesmo lema na mesma sentença. `arguments_annotated` distingue a ausência de realização anotada de uma anotação ainda não realizada. Todos os arquivos preservam as informações científicas disponíveis; a exportação técnica permite reproduzir a segmentação original por tokens.

Evidência lexicográfica e autoridade de frames são distintas. Verbetes do DUPB não são descrições de rolesets. As glosas lexicais herdadas ficam em `data/lexical_evidence.jsonl`; as glosas originais de frames de referência ficam em `origin_frames[].gloss`, com identificação do recurso e link. Descrições de roleset sem autoridade documentada permanecem nulas.

## Interface e direitos

O leiaute deriva do [NounBank.DS Expanded](https://github.com/bryankhelven/NounBank.DS-Expanded). Consulte `NOTICE` e `LICENSE-CODE` para os créditos e a licença do código. Essa licença não concede direitos adicionais sobre os textos do corpus ou outros recursos de terceiros.
