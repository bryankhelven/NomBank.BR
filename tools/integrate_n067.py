"""Apply the immutable N067 cumulative data to the current public projection.

Run with the repository HEAD unchanged, using the sibling base worktree and
the supplied super handoff. No new semantic decisions or remote writes.
"""
import collections,copy,hashlib,html,json,re,shutil,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'release_deps'))
from bs4 import BeautifulSoup
from role_translations import TRANSLATIONS,pt
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'nombank-n067-base';H=W/'work/NomBank_BR_SUPER_HANDOFF_N067_ORQUESTRADOR_4';A=W/'release_n067_audit';A.mkdir(exist_ok=True)
def readrows(p):return list(map(json.loads,p.read_bytes().splitlines()))
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def jl(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b''.join((json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n').encode() for x in v))
def soup(s):return BeautifulSoup(s,'html.parser')
def esc(x):return html.escape(str(x),quote=True)
techbytes=(H/'CURRENT_STATE/CANDIDATE_ANNOTATIONS_11021.jsonl').read_bytes();tech=list(map(json.loads,techbytes.splitlines()));tb={x['instance_id']:x for x in tech};pubid={x['public_instance_id']:x['instance_id'] for x in tech};assert len(pubid)==11021
base=readrows(B/'data/annotations.jsonl');baseby={x['instance_id']:x for x in base};assert sha((B/'data/annotations.jsonl').read_bytes())=='4942916b0b4a44ef996a04d2ad9cc1d3e0e4e544b8f05c2d42a9f86b16377e59'
sci=readrows(H/'CURRENT_STATE/CANDIDATE_SCIENTIFIC_10719.jsonl');sb={x['target_instance_id']:x for x in sci};local={x['target_instance_id'] for x in sci if x.get('annotation_batch')};pending={x['instance_id'] for x in tech if x['annotation_status']=='not_started'};assert (len(local),len(pending))==(4695,302)
senses=readrows(B/'data/senses.jsonl');senseby={x['id']:x for x in senses};sid={i:x['id'] for x in senses for i in x['instance_ids']};assert len(sid)==11021
frames=readrows(B/'data/frames.jsonl');fb={x['id']:x for x in frames};baseframeids=set(fb)
originals=H/'SOURCE_NOMBANK_ORIGINALS';source_dir=R/'data/nombank_sources';source_dir.mkdir(exist_ok=True)
def role_source(r):
 src=r.get('inventory_provenance',{}).get('source',r)
 roleset=src.get('source_frame',src.get('source_roleset'));stem=roleset.rsplit('.',1)[0] if roleset else None
 if stem and (originals/(stem+'.xml')).exists():shutil.copyfile(originals/(stem+'.xml'),source_dir/(stem+'.xml'))
 return {'resource':src.get('source_resource'),'roleset':roleset,'source_arg':src.get('source_arg'),'original_role_definition':src.get('source_original_role_definition'),'original_role_attributes':src.get('source_original_role_attributes'),'source_xml_sha256':src.get('source_file_sha256',src.get('source_nominal_XML_sha256')),'source_xml_url':('data/nombank_sources/'+stem+'.xml') if stem and (source_dir/(stem+'.xml')).exists() else None,'mapping_relation':src.get('relation',src.get('relation_to_w4_arg'))}
for f in frames:
 f['inventory_authority']='accepted_in_formal_base'
 for r in f['roles']:
  r['label_pt']=pt(r['label']);r['definition_pt']=pt(r.get('definition',r['label']))
 for origin in f.get('origin_frames',[]):
  code=origin.get('roleset');stem=code.rsplit('.',1)[0] if code else None
  if stem and (originals/(stem+'.xml')).exists():
   shutil.copyfile(originals/(stem+'.xml'),source_dir/(stem+'.xml'));origin['source_xml_url']='data/nombank_sources/'+stem+'.xml';origin['source_xml_sha256']=sha((originals/(stem+'.xml')).read_bytes())
aliases=[]
for x in sci:
 i=x['target_instance_id']
 if i not in local:continue
 fid=tb[i]['frame_id'];scientificfid=x['argument_frame_id']
 if fid!=scientificfid:aliases.append({'target_instance_id':i,'public_frame_id':fid,'scientific_frame_id':scientificfid,'relation':'EXISTING_ACCEPTED_INVENTORY_REUSE_WITH_DISTINCT_IDENTIFIERS'})
 if fid not in fb:
  rr=[{'slot':sl,'label':r['role_label'],'definition':r['role_definition'],'label_pt':pt(r['role_label']),'definition_pt':pt(r['role_definition']),'nominal_provenance':role_source(r)} for sl,r in x['roles'].items()]
  origin={p['roleset']:p for p in [r['nominal_provenance'] for r in rr] if p['roleset']}
  f={'id':fid,'sense_id':sid[i],'lemma':x['lemma'],'roles':rr,'valency':len(rr),'instance_ids':[],'description':None,'origin_frames':[{'roleset':code,'resource':'English NomBank','url':p['source_xml_url'],'source_xml_url':p['source_xml_url'],'source_xml_sha256':p['source_xml_sha256'],'adapted':True,'gloss':None} for code,p in origin.items()],'inventory_authority':'local_proposal_pending_reconciliation','scientific_frame_id':scientificfid}
  frames.append(f);fb[fid]=f
 if fid not in baseframeids:fb[fid]['instance_ids'].append(i)
 else:fb[fid]['local_instance_ids']=fb[fid].get('local_instance_ids',[])+[i]
for s in senses:
 additions=list(dict.fromkeys(tb[i]['frame_id'] for i in s['instance_ids'] if i in local and tb[i]['frame_id'] not in s['frame_ids']))
 s['frame_ids']+=additions
def authority(i):return 'local_completed_pending_reconciliation' if i in local else ('manual_review_required' if i in pending else 'accepted_in_formal_base')
def details(i):
 a=tb[i];x=sb.get(i);rr=[]
 for sl,spans in a['spans'].items():
  if sl not in {r['slot'] for r in fb.get(a['frame_id'],{}).get('roles',[])}:continue
  scientific=x.get('roles',{}).get(sl,{}) if x else {}
  rr.append({'slot':sl,'realization_mode':a.get('role_realization_mode',{}).get(sl,'INDEPENDENT_SPAN' if spans else 'NONE_SELECTED'),'status':scientific.get('status','REALIZED' if spans else 'UNREALIZED_IN_CONTEXT'),'spans':spans})
 return {'predicate_token_ids':a['predicate']['token_ids'],'predicate_spans':a['predicate']['spans'],'arguments':rr}
frozenby={x['target_instance_id']:x for x in readrows(H/'CURRENT_STATE/FROZEN_SOURCE/W4_PASSAGE1_FULL_INSTANCES_11021.jsonl')}
publicscience=[]
for a in tech:
 i=a['instance_id'];x=sb.get(i);roledata={}
 if x:
  for sl,r in x['roles'].items():
   if sl not in {v['slot'] for v in fb.get(a['frame_id'],{}).get('roles',[])}:continue
   frame_role=next((v for v in fb.get(a['frame_id'],{}).get('roles',[]) if v['slot']==sl),{})
   roledata[sl]={'slot':sl,'label':pt(r.get('role_label',frame_role.get('label',sl))),'definition':pt(r.get('role_definition',frame_role.get('definition',''))),'status':r['status'],'spans':r.get('spans',a['spans'].get(sl,[])),'nominal_provenance':role_source(r)}
 publicscience.append({'target_instance_id':i,'public_instance_id':a['public_instance_id'],'sentence_id':a['sent_ID'],'lemma':a['lemma'],'sense_id':sid[i],'canonical_semantic_unit_id':(x or {}).get('canonical_semantic_unit_id') or frozenby[i]['canonical_semantic_unit_id'],'frame_id':a['frame_id'],'scientific_frame_id':x.get('argument_frame_id',x.get('local_argument_frame_id')) if x else None,'annotation_status':a['annotation_status'],'annotation_authority':authority(i),'roles':roledata,'predicate':a['predicate']})
jl(R/'data/scientific_annotations.jsonl',publicscience);jl(R/'data/annotation_authority.jsonl',[{k:x[k] for k in ['target_instance_id','public_instance_id','sense_id','annotation_status','annotation_authority']} for x in publicscience]);jl(R/'data/pending_instances.jsonl',[{k:x[k] for k in ['target_instance_id','public_instance_id','lemma','sentence_id','sense_id','canonical_semantic_unit_id','annotation_status','annotation_authority']} for x in publicscience if x['target_instance_id'] in pending]);jl(R/'data/frame_identity_map.jsonl',aliases)
(R/'data/annotations.jsonl').write_bytes(techbytes);jl(R/'data/frames.jsonl',frames);jl(R/'data/senses.jsonl',senses)
j(R/'data/role_translations.json',{'authority':'editorial_portuguese_display_translation_original_labels_preserved','translations':TRANSLATIONS})
# Additive source recovery: retain every pre-existing sentence unchanged except nine empty/absent UD blocks.
sourcebytes=(H/'CURRENT_STATE/USER_SUPPLIED_SOURCE/USER_SUPPLIED_SENTENCES_9.conllu').read_bytes();supplied={re.search(r'^# sent_id = (.+)$',b,re.M).group(1):b.strip()+'\n\n' for b in sourcebytes.decode().split('\n\n') if re.search(r'^# sent_id = (.+)$',b,re.M)}
sentences=readrows(B/'data/sentences.jsonl');sentenceby={x['id']:x for x in sentences}
for key,b in supplied.items():
 cols=[l.split('\t') for l in b.splitlines() if l and not l.startswith('#')];text=next(l[9:] for l in b.splitlines() if l.startswith('# text = '))
 rec={'id':key,'text':text,'tokens':[{'id':int(c[0]),'form':c[1],'lemma':c[2],'upos':c[3],'xpos':c[4],'feats':c[5],'head':int(c[6]),'deprel':c[7],'deps':c[8],'misc':c[9]} for c in cols if c[0].isdigit()],'multiword_tokens':[{'id':c[0],'form':c[1],'misc':c[9]} for c in cols if '-' in c[0]],'source_authority':'user_supplied_conllu_transcription','conllu_sha256':sha(b.encode())}
 if key in sentenceby:
  old=sentenceby[key];assert old['text']==text;sentences[sentences.index(old)]=rec
 else:sentences.append(rec)
 sentenceby[key]=rec
jl(R/'data/sentences.jsonl',sentences)
(R/'data/sentences.conllu').write_bytes((H/'CURRENT_STATE/FROZEN_SOURCE/W4_PASSAGE1_EXACT_AVAILABLE_SENTENCES_5829.conllu').read_bytes()+sourcebytes)
jl(R/'data/source_recovery.jsonl',[{'sentence_id':k,'source_authority':'user_supplied_conllu_transcription','external_original_byte_identity_verified':False,'normalized_conllu_sha256':sha(b.encode()),'enhanced_dependencies_inferred':False} for k,b in supplied.items()])
def enrich(inst,i):
 inst['target_instance_id']=i;inst['annotation_authority']=authority(i);inst['annotation_status']=tb[i]['annotation_status'];inst['frame_id']=tb[i]['frame_id'];inst['argument_details']=details(i)
 return inst
lemma_data={};old_instance_objects={};basegroups={}
for p in sorted((B/'jsons').glob('*.json')):
 data=json.loads(p.read_text());slug=p.stem;groups=[]
 for group in data['senses']:
  copied=copy.deepcopy(group);insts=copied['instances'];originalids=[pubid[x['instance_id']] for x in insts];sid0=sid[originalids[0]]
  fid=next((baseby[i]['frame_id'] for i in originalids if baseby[i]['frame_id']),None)
  copied['sense_id']=sid0;copied['frame_id']=fid
  copied['inventory_authority']=fb[fid]['inventory_authority'] if fid in fb else 'no_defined_inventory'
  if fid in fb:
   for r in copied['roles'] or []:r['desc_pt']=pt(r['desc']);r['definition_pt']=pt(r.get('definition',r['desc']))
   for origin in copied.get('origin_frames') or []:
    reference=next((o for o in fb[fid].get('origin_frames',[]) if o.get('roleset')==origin.get('roleset')),None)
    if reference and reference.get('source_xml_url'):
     origin['source_xml_url']=reference['source_xml_url'];origin['source_xml_sha256']=reference['source_xml_sha256']
  kept=[]
  for inst in insts:
   i=pubid[inst['instance_id']];old_instance_objects[i]=copy.deepcopy(inst)
   if i not in local:kept.append(enrich(inst,i))
  copied['instances']=kept
  groups.append(copied);basegroups[(sid0,fid)]=copied
 data['senses']=groups;lemma_data[slug]=data
index=json.loads((B/'data/lemma_index.json').read_text());slugby={x['id']:x['slug'] for x in index['instances']}
for a in tech:
 i=a['instance_id']
 if i not in local:continue
 fid=a['frame_id'];f=fb[fid];key=(sid[i],fid);data=lemma_data[slugby[i]]
 if key not in basegroups:
  origins=copy.deepcopy(f.get('origin_frames',[]))
  group={'sense_id':sid[i],'frame_id':fid,'pt_roleset':a['roleset'],'sense_label':senseby[sid[i]]['label'],'description':None,'inventory_authority':f['inventory_authority'],'origin_frames':origins,'roles':[{'id':r['slot'],'desc':r['label'],'definition':r['definition'],'desc_pt':r['label_pt'],'definition_pt':r['definition_pt']} for r in f['roles']],'instances':[],'syntactic_profile':{}}
  data['senses'].append(group);basegroups[key]=group
 inst={'instance_id':a['public_instance_id'],'sent_ID':a['sent_ID'],'text':a['text'],'arguments_annotated':True,'predicate':{'form':a['predicate']['form'],'char_start':a['predicate']['spans'][0]['char_start'],'char_end':a['predicate']['spans'][0]['char_end']},'realization':a['realization'],'syntax':a['syntax'],'argument_positions':{sl:[{'char_start':s['char_start'],'char_end':s['char_end']} for s in spans] for sl,spans in a['spans'].items()}}
 basegroups[key]['instances'].append(enrich(inst,i))
for slug,data in lemma_data.items():
 for group in data['senses']:
  if any(x['target_instance_id'] in local for x in group['instances']):
   slots=[r['id'] for r in group['roles'] or []];profile={}
   for inst in group['instances']:
    for sl,dep in inst['syntax'].items():
     if dep and sl in slots:
      for relation in (dep if isinstance(dep,list) else [dep]):
       if relation:profile.setdefault(relation,{s:0 for s in slots})[sl]+=1
   group['syntactic_profile']=profile
 j(R/'jsons'/f'{slug}.json',data)
all_instances=[]
for data in lemma_data.values():
 for group in data['senses']:
  for inst in group['instances']:all_instances.append({'lemma':data['lemma'],'pt_roleset':group['pt_roleset'],'sense_label':group.get('sense_label',senseby[group['sense_id']]['label']),**inst})
jl(R/'jsons/instances.jsonl',all_instances);jl(R/'jsons/lemmas.jsonl',lemma_data.values())
with zipfile.ZipFile(R/'jsons/lemmas.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for slug in lemma_data:z.write(R/'jsons'/f'{slug}.json',f'{slug}.json')
for item in index['instances']:
 i=item['id'];a=tb[i];fid=a['frame_id'];item['status']=a['annotation_status'];item['authority']=authority(i)
 if i in local:
  item['valency']=fb[fid]['valency'];item['roles']=[{'slot':sl,'status':{'REALIZED':'realized','UNREALIZED_IN_CONTEXT':'unrealized','ENCODED_IN_REL':'encoded_in_rel'}[r['status']]} for sl,r in sb[i]['roles'].items()]
counts={'instances':11021,'arg_annotated':10719,'arg_not_started':302,'formal_accepted':6024,'local_completed':4695,'manual_pending':302,'lemmas':1605,'senses':2287,'frames':len(frames)};index['counts']=counts;j(R/'data/lemma_index.json',index)
STATUSTEXT={'accepted_in_formal_base':'Aceita na base formal','local_completed_pending_reconciliation':'Concluída localmente · sem homologação global','manual_review_required':'Pendente de verificação manual'}
def trace(i):
 d=details(i);parts=[f"<details class='traceability'><summary>Spans e HEADs</summary><p>REL: tokens {esc(d['predicate_token_ids'])}</p><ul>"]
 for r in d['arguments']:
  if r['status']=='ENCODED_IN_REL':parts.append(f"<li>{esc(r['slot'])}: incorporado em REL; sem duplicar span.</li>")
  elif not r['spans']:parts.append(f"<li>{esc(r['slot'])}: sem span independente no contexto.</li>")
  for s in r['spans']:parts.append(f"<li>{esc(r['slot'])}: tokens {esc(s['token_ids'])}; caracteres [{s['char_start']}, {s['char_end']}); HEAD {esc(s.get('head_token_id','não anotado'))} ({esc(s.get('head_form',''))}, {esc(s.get('head_deprel',''))}).</li>")
 return ''.join(parts)+f"</ul><a href='../jsons/{slugby[i]}.json' download>JSON desta ocorrência e do lema</a></details>"
source_blocks={re.search(r'^# sent_id = (.+)$',b,re.M).group(1):b for b in (H/'CURRENT_STATE/FROZEN_SOURCE/W4_PASSAGE1_EXACT_AVAILABLE_SENTENCES_5829.conllu').read_text().split('\n\n') if re.search(r'^# sent_id = (.+)$',b,re.M)}|supplied
recovered_bytes=(A/'recovered_porttinari_68.conllu').read_bytes()
recovered_blocks={re.search(r'^# sent_id = (.+)$',b,re.M).group(1):b for b in recovered_bytes.decode().split('\n\n') if re.search(r'^# sent_id = (.+)$',b,re.M)}
source_blocks|=recovered_blocks
(R/'data/sentences.conllu').write_bytes((H/'CURRENT_STATE/FROZEN_SOURCE/W4_PASSAGE1_EXACT_AVAILABLE_SENTENCES_5829.conllu').read_bytes()+recovered_bytes+sourcebytes)
unit_cache={}
def marked(i):
 a=tb[i];text=a['text'];key=a['sent_ID'];marks={t['id']:t['labels'] for t in a['tokens']}
 if key not in unit_cache:
  cursor=0;covered=set();units=[]
  source_rows=[line.split('\t') for line in source_blocks[key].splitlines() if line and not line.startswith('#')]
  for c in source_rows:
   tid=c[0]
   if '-' in tid:
    low,high=map(int,tid.split('-'));u=set(range(low,high+1));covered|=u
   elif tid.isdigit() and int(tid) not in covered:u={int(tid)}
   else:continue
   lo=text.find(c[1],cursor);assert lo>=cursor,(i,c[1]);hi=lo+len(c[1]);units.append((lo,hi,u));cursor=hi
  unit_cache[key]=units
 out=[];cursor=0
 for lo,hi,u in unit_cache[key]:
  out.append(esc(text[cursor:lo]));roles=collections.defaultdict(list)
  for tok in sorted(u):
   for label in marks.get(tok,[]):roles[label].append(tok)
  piece=esc(text[lo:hi])
  if roles:
   labels=list(roles);attrs=' '.join(labels);tokenids=sorted({v for ids in roles.values() for v in ids});partial=any(set(ids)!=u for ids in roles.values())
   out.append(f"<span class='marked {' '.join(sl.lower() for sl in labels)}' data-role='{attrs}' data-token-ids='{','.join(map(str,tokenids))}' data-surface-token-ids='{','.join(map(str,sorted(u)))}' data-role-token-ids='{esc(json.dumps(roles,separators=(',',':')))}' data-partial-mwt='{str(partial).lower()}' data-char-start='{lo}' data-char-end='{hi}' aria-label='{attrs}'>{piece}</span>")
  else:out.append(piece)
  cursor=hi
 out.append(esc(text[cursor:]));return ''.join(out)

def localrow(i,slots):
 a=tb[i];cells=''.join(f"<td class='{sl.lower()}'>{esc(a['realization'].get(sl) or '')}</td>" for sl in slots)
 return f"<tr data-instance-id='{i}' id='instance-{i}'>{cells}<td class='texto'>{marked(i)}</td></tr>"
def frame_section(fid,ids):
 f=fb[fid];slots=[r['slot'] for r in f['roles']];source=''.join(f"<a href='../{esc(o.get('source_xml_url') or o.get('url'))}'>{esc(o['roleset'])}</a> " for o in f.get('origin_frames',[]) if o.get('source_xml_url') or o.get('url'))
 roles=''.join(f"<li class='{r['slot'].lower()}'><strong>{r['slot']}:</strong> {esc(r['label_pt'])} — {esc(r['definition_pt'])}</li>" for r in f['roles'])
 status='Inventário da base formal; ocorrências locais identificadas individualmente.' if fid in baseframeids else 'Proposta local de inventário nominal · pendente de reconciliação.'
 return f"<section class='frame-section' id='{esc(fid)}'><div class='roleset-line'><p><strong>Acepção:</strong> {esc(senseby[f['sense_id']]['label'])}</p><p class='inventory-status'>{status}</p><p>Valência: {f['valency']} · Fonte nominal: {source}</p></div><h3>Papéis semânticos</h3><ul class='roles-list'>{roles}</ul><h3>Ocorrências e argumentos</h3><div class='table-scroll' role='region' aria-label='Tabela de argumentos' tabindex='0'><table class='arg-table occ-table'><thead><tr>{''.join(f'<th scope="col" class="{s.lower()}">{s}</th>' for s in slots)}<th scope='col'>Texto</th></tr></thead><tbody>{''.join(localrow(i,slots) for i in ids)}</tbody></table></div></section>"
# Preserve the existing page shell and all prior accepted occurrence markup.
for slug,data in lemma_data.items():
 page=soup((B/'site_pages'/f'{slug}.html').read_text());main=page.select_one('main .content');localids={x['target_instance_id'] for g in data['senses'] for x in g['instances'] if x['target_instance_id'] in local}
 for node in list(page.select('[data-instance-id]')):
  if int(node['data-instance-id']) in localids:node.decompose()
 for sec in page.select('.frame-section[id]'):
  f=fb.get(sec['id'])
  if f:
   for li,r in zip(sec.select('.roles-list > li'),f['roles']):
    li.clear();li.append(soup(f"<strong>{r['slot']}:</strong> {esc(r['label_pt'])} — {esc(r['definition_pt'])}"))
   for o in f.get('origin_frames',[]):
    if o.get('source_xml_url'):
     for a in sec.select('a'):
      if a.get_text()==o.get('roleset'):a['href']='../'+o['source_xml_url']
 localgroup=collections.defaultdict(list)
 for i in localids:localgroup[(sid[i],tb[i]['frame_id'])].append(i)
 for (senseid,fid),ids in sorted(localgroup.items()):
  existing=page.find(id=fid)
  if existing and existing.select_one('.occ-table tbody'):
   slots=[r['slot'] for r in fb[fid]['roles']]
   for i in sorted(ids):existing.select_one('.occ-table tbody').append(soup(localrow(i,slots)))
  else:
   sense_sec=page.find(id=senseid)
   if sense_sec is None:
    sense_sec=page.new_tag('section',attrs={'class':'sense-section','id':senseid});main.append(sense_sec)
   sense_sec.append(soup(frame_section(fid,sorted(ids))))
 for table in page.select('.occ-table'):
  head=table.select_one('thead tr')
  if head:head.append(soup('<th scope="col">Situação da anotação</th><th scope="col">Rastreabilidade</th>'))
  for row in table.select('tbody tr[data-instance-id]'):
   i=int(row['data-instance-id']);row['data-annotation-authority']=authority(i)
   row.append(soup(f"<td class='annotation-state {authority(i)}'>{STATUSTEXT[authority(i)]}</td><td>{trace(i)}</td>"))
 for article in page.select('article[data-instance-id]'):
  i=int(article['data-instance-id']);article.append(soup(f"<p class='annotation-state {authority(i)}'>{STATUSTEXT[authority(i)]}</p>"))
 # Remove abandoned empty sections, without touching sections containing any occurrence.
 for sec in list(page.select('.frame-section')):
  if not sec.select('[data-instance-id]'):sec.decompose()
 stats=main.select_one('p.muted');n=sum(len(g['instances']) for g in data['senses']);annot=sum(x['arguments_annotated'] for g in data['senses'] for x in g['instances'])
 if stats:stats.string=f'{n} instâncias · {annot} com ARG anotados · {n-annot} pendentes de verificação manual'
 (R/'site_pages'/f'{slug}.html').write_text(str(page))
 print('pages',slug,flush=True) if len(lemma_data)<2 else None
 # Existing accepted objects are preserved field-for-field; metadata additions are explicit.
 for g in data['senses']:
  for inst in g['instances']:
   i=inst['target_instance_id']
   if i not in local:
    assert all(inst[k]==v for k,v in old_instance_objects[i].items()),i
j(R/'data/release.json',{'release':'N067','counts':counts,'completed_percent':10719/11021*100,'formal_accepted_percent':6024/11021*100,'local_decisions_globally_homologated':False,'manual_review_pending':302,'open_identified_source_gaps':0,'scientific_reset':False,'annotation_authority_values':STATUSTEXT})
j(A/'integration.json',{'base_commit':'fe8a948babd1e6e6e83a7fd5bfbda62cdaa90861','counts':counts,'frame_identity_alias_records':len(aliases),'accepted_public_instance_fields_preserved':6024,'technical_annotations_sha256':sha(techbytes),'local_delta':4695,'manual_pending':302,'source_recovery':len(supplied),'source_xml_files':len(list(source_dir.glob('*.xml'))),'nested_argument_exceptions':[10214,12500]})
print(json.dumps({'result':'PROJECTION_BUILT','counts':counts,'aliases':len(aliases)},ensure_ascii=False),flush=True)
