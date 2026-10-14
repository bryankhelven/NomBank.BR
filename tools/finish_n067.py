import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'release_deps'))
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];B=R.parent/'nombank-n067-base'
def soup(s):return BeautifulSoup(s,'html.parser')
release=json.loads((R/'data/release.json').read_text());counts=release['counts']
metrics=[('1.605','lemas'),('11.021','ocorrências'),('10.719','anotações concluídas · 97,26%'),('6.024','aceitas na base formal'),('4.695','decisões locais · sem homologação global'),('302','pendentes de verificação manual')]
notice='<p class="authority-notice">N067: 6.024 anotações aceitas na base formal e 4.695 concluídas localmente, ainda sem homologação global. As 302 pendências de verificação manual permanecem no recurso. Ausência de ARG realizado não significa ausência de anotação.</p>'
for filename in ['index.html','statistics.html']:
 page=soup((B/filename).read_text());grid=page.select_one('.metric-grid');grid.clear()
 for value,label in metrics:grid.append(soup(f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>'))
 grid.insert_after(soup(notice))
 if filename=='index.html':
  filters=page.select_one('.filters');filters.append(soup('<label>Autoridade<select id="authority"><option value="all">Todas</option><option value="accepted_in_formal_base">Aceita na base formal</option><option value="local_completed_pending_reconciliation">Concluída localmente</option><option value="manual_review_required">Pendente de verificação manual</option></select></label>'))
  page.select_one('#status option[value="annotated"]').string='Anotação concluída (formal ou local)';page.select_one('#status option[value="not_started"]').string='Pendente de verificação manual'
  page.select_one('#realization').append(soup('<option value="encoded_in_rel">Incorporado em REL</option>'))
  vals=sorted({x['valency'] for x in json.loads((R/'data/lemma_index.json').read_text())['instances'] if x['valency'] is not None})
  sel=page.select_one('#valency');sel.clear();sel.append(soup('<option value="all">Todas</option>'))
  for v in vals:sel.append(soup(f'<option value="{v}">V{v}</option>'))
 else:
  for p in page.select('p'):
   if '54,66%' in p.get_text():p.string='Anotação concluída: 97,2598% de 11.021 ocorrências. Autoridade formal preservada: 6.024 (54,6593%). A publicação das 4.695 decisões locais não as promove a Gold formal.'
  page.select_one('main .content').append(soup(f'<p>{counts["senses"]} acepções e {counts["frames"]} variantes de inventário de frame, incluindo propostas locais identificadas.</p>'))
 (R/filename).write_text(str(page))
script=(B/'scripts.js').read_text().replace("['search', 'status', 'valency', 'role', 'realization']","['search', 'status', 'valency', 'role', 'realization', 'authority']")
script=script.replace("if (f.status !== 'all' && o.status !== f.status) return false;","if (f.status !== 'all' && o.status !== f.status) return false;\n    if (f.authority && f.authority !== 'all' && o.authority !== f.authority) return false;")
script=script.replace("${matches.filter(o => o.status === 'annotated').length} com ARG","${matches.filter(o => o.status === 'annotated').length} com anotação concluída")
(R/'scripts.js').write_text(script)
for p in (R/'site_pages').glob('*.html'):
 page=soup(p.read_text());main=page.select_one('main .content');seen=[]
 data=json.loads((R/'jsons'/f'{p.stem}.json').read_text())
 for group in data['senses']:
  key=group['sense_id'];label=group.get('sense_label') or group.get('pt_roleset') or f'{data["lemma"]} · acepção'
  if key not in {k for k,l in seen}:seen.append((key,label))
 nav=page.new_tag('nav',attrs={'class':'sense-navigation','aria-label':'Acepções'})
 for key,label in seen:
  a=page.new_tag('a',href='#'+key);a.string=label;nav.append(a)
 heading=main.select_one('.lemma-heading');heading.insert_after(nav)
 nav.insert_after(soup(notice))
 for row in page.select('.occ-table tr[data-instance-id]'):
  key='instance-'+row['data-instance-id']
  if page.find(id=key) is None:row['id']=key
 p.write_text(str(page))
page=soup((B/'downloads.html').read_text());page.select_one('main .content p').insert_after(soup(notice));ul=page.select_one('.download-list')
for path,label in [('data/scientific_annotations.jsonl','Anotações científicas e proveniência nominal (JSONL)'),('data/annotation_authority.jsonl','Autoridade por ocorrência: formal, local ou pendente (JSONL)'),('data/pending_instances.jsonl','As 302 ocorrências pendentes de verificação manual (JSONL)'),('data/sentences.conllu','Sentenças CoNLL-U: fonte congelada e nove blocos adicionais'),('data/source_recovery.jsonl','Proveniência dos nove blocos CoNLL-U fornecidos pelo usuário (JSONL)'),('data/frame_identity_map.jsonl','Correspondência explícita entre IDs públicos e científicos de frame (JSONL)'),('data/release.json','Estado e contagens da release N067 (JSON)')]:ul.append(soup(f'<li><a href="{path}" download>{label}</a></li>'))
(R/'downloads.html').write_text(str(page))
style=(B/'styles.css').read_text()+'''
/* N067: authority and traceability additions preserve the existing layout. */
.authority-notice{line-height:1.6;padding:14px 16px;border-left:4px solid #8b9ce8;background:#303744;border-radius:8px;overflow-wrap:anywhere}
.sense-navigation{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.sense-navigation a{padding:7px 10px;background:#303744;border-radius:7px}
.traceability{min-width:220px;text-align:left;overflow-wrap:anywhere}.traceability summary{cursor:pointer;font-weight:600}.traceability ul{padding-left:20px;line-height:1.5}
.annotation-state{font-size:.88rem;overflow-wrap:anywhere}.local_completed_pending_reconciliation{color:#f3d995}.manual_review_required{color:#ffb0a6}.accepted_in_formal_base{color:#aae4b0}
.marked.arg1.arg4,.marked.arg1.arg2{background:linear-gradient(180deg,transparent 70%,#ad7adb44 70%);text-decoration:underline;text-decoration-style:dotted}
.table-scroll{max-width:100%;overflow-x:auto}.inventory-status{font-weight:600}
@media(max-width:600px){.filters{max-width:100%}.filters label{min-width:0}.authority-notice{font-size:.9rem}.sense-navigation a{font-size:.9rem}}
'''
style+='\n/* Keep all six N067 metrics balanced and filters usable on narrow screens. */\n.hero-metrics{grid-template-columns:repeat(3,minmax(0,1fr));max-width:900px}\n@media(max-width:600px){.hero-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.filters{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.filters label{min-width:0}.filters select,.filters input{width:100%;min-width:0}}\n'
(R/'styles.css').write_text(style)
readme=(B/'README.md').read_text().replace('Há 6.024 instâncias com argumentos anotados (54,66%) e 4.997 ainda sem anotação de argumentos.','Há 10.719 instâncias com anotação concluída (97,2598%): 6.024 aceitas na base formal e 4.695 decisões locais ainda sem homologação global. Permanecem 302 ocorrências pendentes de verificação manual, preservadas em todos os exports e nas páginas.')
readme+='''\n## Release N067\n\nA publicação distingue anotação concluída de autoridade formal. Consulte `data/annotation_authority.jsonl` e o filtro Autoridade. Nenhuma das 4.695 decisões locais é promovida automaticamente a Gold formal. As 302 pendências continuam disponíveis em `data/pending_instances.jsonl`.\n\nSpans, tokens e HEADs estão acessíveis nas tabelas e nos JSONs por lema. Os XMLs nominais de referência ficam em `data/nombank_sources/`; a proveniência científica está separada da evidência lexical. As traduções editoriais dos rótulos para apresentação em português preservam os rótulos e as definições originais nos inventários técnicos.\n\nAs nove sentenças recuperadas são transcrições fornecidas pelo usuário, sem afirmação de identidade byte a byte com um arquivo externo original. Os campos DEPS `_` foram preservados. Os dois aninhamentos ARG–ARG históricos justificados permanecem; não há nova adjudicação ou reanotação geral nesta integração.\n'''
(R/'README.md').write_text(readme)
doc=(B/'DATA_FORMAT.md').read_text()+'''
## N067: autoridade, inventários e rastreabilidade

`annotation_status` e `arguments_annotated` continuam indicando se a anotação foi concluída, mesmo quando não há argumento realizado. `annotation_authority` distingue `accepted_in_formal_base` (6.024), `local_completed_pending_reconciliation` (4.695) e `manual_review_required` (302). A soma das duas primeiras classes é 10.719; somente a primeira representa a base formal aceita. A publicação não é novo ACK científico.

Os JSONs por lema adicionam `target_instance_id`, `sense_id`, `frame_id`, `argument_details` e metadados de autoridade. As posições têm índices Unicode de início inclusivo e fim exclusivo. `argument_details` preserva os tokens e HEADs do TECH, incluindo modo incorporado em REL quando explícito. Papéis sem span continuam no inventário; slots históricos sem definição não são reintroduzidos como papéis definidos na projeção científica.

Cada variante de inventário tem autoridade própria. `label_pt`, `definition_pt`, `desc_pt` e `data/role_translations.json` são traduções editoriais para a interface, preservando campos originais. `data/frame_identity_map.jsonl` registra 61 ocorrências que reutilizam inventários aceitos com IDs públicos e científicos distintos, sem renomear silenciosamente o frame. As acepções e seus IDs permanecem preservados.

`data/scientific_annotations.jsonl` fornece uma projeção pública da ciência, com proveniência nominal e sem arquivos de rollback, mensagens, políticas de envio, caminhos privados ou bridge administrativo. `data/lexical_evidence.jsonl` permanece literal e separado. Os arquivos XML de origem são cópias literais; seus hashes e rótulos originais não são substituídos por explicações editoriais.

`data/source_recovery.jsonl` identifica nove blocos CoNLL-U transcritos pelo usuário. `data/sentences.conllu` reúne a fonte congelada original e esses blocos adicionais, sem reescrever o congelado. A publicação preserva os campos fornecidos, incluindo DEPS `_`, e não afirma verificação byte a byte contra o corpus externo original.

As instâncias 12500 (Arg1/Arg4) e 10214 (Arg1/Arg2) preservam aninhamentos ARG–ARG historicamente documentados. Tokens compartilhados aparecem com os dois rótulos; o REL não é duplicado como argumento. Os exemplos e as tabelas podem apresentar a mesma ocorrência, mas cada ocorrência possui um único destino de navegação `#instance-ID`.
'''
(R/'DATA_FORMAT.md').write_text(doc)
page=soup((B/'sobre.html').read_text())
for p in page.select('p'):
 if 'Os rótulos semânticos e spans são os aceitos da anotação.' in p.get_text():p.string='A release N067 reúne 6.024 anotações aceitas na base formal e 4.695 decisões locais ainda sem homologação global. As 302 pendências de verificação manual continuam no recurso. HEAD e SPAN são distintos; a sintaxe UD não determina automaticamente os papéis semânticos.'
page.select_one('main .content').append(soup('<p>As nove transcrições CoNLL-U fornecidas pelo usuário complementam a fonte congelada e preservam os campos recebidos. A publicação não equivale a novo ACK científico.</p>'))
(R/'sobre.html').write_text(str(page))
page=soup((B/'all-lemmas.html').read_text());page.select_one('h1').insert_after(soup('<p class="authority-notice">11.021 ocorrências preservadas: 10.719 com anotação concluída (6.024 na base formal e 4.695 locais) e 302 pendentes de verificação manual.</p>'));(R/'all-lemmas.html').write_text(str(page))
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and not any(v.startswith('.') and v!='.nojekyll' for v in p.relative_to(R).parts) and p!=R/'data/manifest.json':
  b=p.read_bytes();files.append({'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(R/'data/manifest.json').write_text(json.dumps({'schema_version':'nombank-br/2.2-n067','counts':counts,'files':files},ensure_ascii=False,indent=2)+'\n')
print('N067 frontend, docs, downloads and SHA-256 manifest assembled')
