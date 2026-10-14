"""Data/DOM integrity checks for the N067 public candidate, without reannotation."""
import collections,hashlib,json,re,sys,zipfile
from pathlib import Path
from urllib.parse import urlsplit,unquote
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'release_deps'))
from bs4 import BeautifulSoup
from role_translations import TRANSLATIONS
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'nombank-n067-base';H=W/'work/NomBank_BR_SUPER_HANDOFF_N067_ORQUESTRADOR_4';A=W/'release_n067_audit'
def rows(p):return list(map(json.loads,p.read_bytes().splitlines()))
def sha(b):return hashlib.sha256(b).hexdigest()
def soup(p):return BeautifulSoup(p.read_text(),'html.parser')
original=rows(B/'data/annotations.jsonl');current=rows(R/'data/annotations.jsonl');by={x['instance_id']:x for x in current};oldby={x['instance_id']:x for x in original}
assert len(current)==len(by)==11021 and len({x['public_instance_id'] for x in current})==11021
assert (R/'data/annotations.jsonl').read_bytes()==(H/'CURRENT_STATE/CANDIDATE_ANNOTATIONS_11021.jsonl').read_bytes()
science=rows(H/'CURRENT_STATE/CANDIDATE_SCIENTIFIC_10719.jsonl');sci={x['target_instance_id']:x for x in science};local={x['target_instance_id'] for x in science if x.get('annotation_batch')};accepted={x['instance_id'] for x in original if x['annotation_status']=='annotated'};pending={x['instance_id'] for x in current if x['annotation_status']=='not_started'}
assert (len(accepted),len(local),len(pending))==(6024,4695,302) and not accepted&local and not pending&local and accepted|local|pending==set(by)
assert all(by[i]==oldby[i] for i in accepted|pending)
beforelines=(B/'data/annotations.jsonl').read_bytes().splitlines(keepends=True);afterlines=(R/'data/annotations.jsonl').read_bytes().splitlines(keepends=True)
assert all(a==b for a,b,x in zip(beforelines,afterlines,original) if x['instance_id'] not in local)
assert (R/'data/lexical_evidence.jsonl').read_bytes()==(B/'data/lexical_evidence.jsonl').read_bytes()
frozen=rows(H/'CURRENT_STATE/FROZEN_SOURCE/W4_PASSAGE1_FULL_INSTANCES_11021.jsonl');fb0={x['target_instance_id']:x for x in frozen}
frames=rows(R/'data/frames.jsonl');frameby={x['id']:x for x in frames};assert len(frameby)==len(frames)==2699
baseframes=rows(B/'data/frames.jsonl');baseframeby={x['id']:x for x in baseframes}
for f in baseframes:
 now=frameby[f['id']]
 for k,v in f.items():
  if k=='roles':
   assert len(v)==len(now[k])
   for old,new in zip(v,now[k]):assert all(new[kk]==vv for kk,vv in old.items())
  elif k=='origin_frames':
   assert len(v)==len(now[k])
   for old,new in zip(v,now[k]):assert all(new[kk]==vv for kk,vv in old.items())
  else:assert now[k]==v,(f['id'],k)
base_senses=rows(B/'data/senses.jsonl');senses=rows(R/'data/senses.jsonl');senseby={x['id']:x for x in senses};sid={i:x['id'] for x in senses for i in x['instance_ids']}
assert len(senses)==len(senseby)==2287 and len(sid)==11021
for s in base_senses:
 now=senseby[s['id']]
 for k,v in s.items():
  if k=='frame_ids':assert now[k][:len(v)]==v
  else:assert now[k]==v
authority=rows(R/'data/annotation_authority.jsonl');authby={x['target_instance_id']:x for x in authority};assert len(authority)==len(authby)==11021
assert collections.Counter(x['annotation_authority'] for x in authority)=={'accepted_in_formal_base':6024,'local_completed_pending_reconciliation':4695,'manual_review_required':302}
index=json.loads((R/'data/lemma_index.json').read_text());ib={x['id']:x for x in index['instances']};assert len(ib)==11021
publicscience=rows(R/'data/scientific_annotations.jsonl');ps={x['target_instance_id']:x for x in publicscience};assert len(ps)==11021
pendingexport=rows(R/'data/pending_instances.jsonl');assert {x['target_instance_id'] for x in pendingexport}==pending and len(pendingexport)==302
allpublic=[];lemmaobjects=[];public_before={x['instance_id']:x for x in rows(B/'jsons/instances.jsonl')};slugby={x['id']:x['slug'] for x in index['instances']}
for p in sorted((R/'jsons').glob('*.json')):
 data=json.loads(p.read_text());lemmaobjects.append(data)
 for g in data['senses']:
  if g['frame_id'] in frameby:assert {r['id'] for r in g['roles'] or []}=={r['slot'] for r in frameby[g['frame_id']]['roles']}
  for inst in g['instances']:
   i=inst['target_instance_id'];a=by[i];assert inst['instance_id']==a['public_instance_id'] and inst['sent_ID']==a['sent_ID'] and inst['text']==a['text']
   assert inst['arguments_annotated']==(a['annotation_status']=='annotated') and inst['annotation_authority']==authby[i]['annotation_authority']
   assert g['sense_id']==sid[i] and inst['frame_id']==a['frame_id']
   if i in accepted:
    old=public_before[inst['instance_id']]
    for k in ['sent_ID','text','arguments_annotated','predicate','realization','syntax','argument_positions']:assert inst[k]==old[k],(i,k)
   if i in local:
    assert inst['realization']==a['realization'] and inst['syntax']==a['syntax']
    assert {r['slot'] for r in inst['argument_details']['arguments']}==set(sci[i]['roles'])
    for r in inst['argument_details']['arguments']:assert r['spans']==a['spans'][r['slot']]
   allpublic.append(inst)
assert len(lemmaobjects)==1605 and len(allpublic)==len({x['target_instance_id'] for x in allpublic})==11021
flat=rows(R/'jsons/instances.jsonl');flatby={x['target_instance_id']:x for x in flat};assert len(flat)==11021
for inst in allpublic:assert all(flatby[inst['target_instance_id']][k]==v for k,v in inst.items())
exportlemmas=rows(R/'jsons/lemmas.jsonl');assert {x['lemma']:x for x in exportlemmas}=={x['lemma']:x for x in lemmaobjects}
with zipfile.ZipFile(R/'jsons/lemmas.zip') as z:
 assert z.testzip() is None and len(z.namelist())==1605
 for n in z.namelist():assert z.read(n)==(R/'jsons'/n).read_bytes()
alias=rows(R/'data/frame_identity_map.jsonl');assert len(alias)==61
for i in pending:assert ps[i]['canonical_semantic_unit_id']==fb0[i]['canonical_semantic_unit_id']
for x in alias:assert x['public_frame_id']==by[x['target_instance_id']]['frame_id'] and x['scientific_frame_id']==sci[x['target_instance_id']]['argument_frame_id']
nested=[];spans=0;heads=0
for i in local:
 a=by[i];x=sci[i];f=frameby[a['frame_id']];assert len(f['roles'])==f['valency']==ib[i]['valency'] and {r['slot'] for r in f['roles']}==set(x['roles'])
 assert ps[i]['annotation_authority']=='local_completed_pending_reconciliation' and set(ps[i]['roles'])==set(x['roles'])
 assert a['predicate']==oldby[i]['predicate'] and a['roleset']==oldby[i]['roleset'] and x['canonical_semantic_unit_id']==fb0[i]['canonical_semantic_unit_id']
 for token in a['tokens']:
  assert not ('REL' in token['labels'] and len(token['labels'])>1)
  if len(token['labels'])>1:nested.append((i,token['id'],token['labels']))
 for slot,r in x['roles'].items():
  for span in r['spans']:
   spans+=1;heads+=span['head_token_id'] in span['token_ids'];assert a['text'][span['char_start']:span['char_end']]==span['surface']
   assert not set(span['token_ids'])&set(a['predicate']['token_ids'])
assert spans==heads==5139 and len(nested)==9 and {i for i,t,l in nested}=={12500,10214}
for i,t,l in nested:assert l==(['Arg1','Arg4'] if i==12500 else ['Arg1','Arg2'])
sentences=rows(R/'data/sentences.jsonl');sentby={x['id']:x for x in sentences};assert len(sentby)==len(sentences)==5906
recover=rows(R/'data/source_recovery.jsonl');userids={x['sentence_id'] for x in recover};assert len(userids)==9
for x in rows(B/'data/sentences.jsonl'):
 if x['id'] not in userids:assert sentby[x['id']]==x
source=(R/'data/sentences.conllu').read_text();conllublocks={re.search(r'^# sent_id = (.+)$',b,re.M).group(1):b for b in source.split('\n\n') if re.search(r'^# sent_id = (.+)$',b,re.M)};assert len(conllublocks)==5906 and set(conllublocks)==set(sentby)
for i in local|pending:assert by[i]['sent_ID'] in conllublocks
links_checked=0;dom_ids=set();local_marks=0;pending_dom=set();accepted_dom=set();local_dom=set()
for p in (R/'site_pages').glob('*.html'):
 page=soup(p);ids=[x['id'] for x in page.select('[id]')];assert len(ids)==len(set(ids)),(p.name,'duplicate anchors')
 expected={i for i,x in ib.items() if x['slug']==p.stem};rows_dom=page.select('.occ-table tbody tr[data-instance-id]');assert {int(x['data-instance-id']) for x in rows_dom}==expected and len(rows_dom)==len(expected),(p.name,'missing rows')
 for row in rows_dom:
  i=int(row['data-instance-id']);assert row.select_one('.texto').get_text()==by[i]['text'],(i,'surface')
  assert row['data-annotation-authority']==authby[i]['annotation_authority'] and page.find(id='instance-'+str(i))
  assert row.select_one('.traceability') and row.select_one('.annotation-state')
  if i in local:
   actual=collections.defaultdict(set)
   for node in row.select('.texto .marked'):
    rr=json.loads(node['data-role-token-ids']);local_marks+=1
    for sl,tokens in rr.items():actual[sl]|=set(tokens)
   expectedmarks=collections.defaultdict(set)
   for token in by[i]['tokens']:
    for sl in token['labels']:expectedmarks[sl].add(token['id'])
   assert dict(actual)==dict(expectedmarks),(i,'highlight tokens');local_dom.add(i)
  elif i in pending:pending_dom.add(i)
  else:accepted_dom.add(i)
 for a in page.select('a[href]'):
  u=urlsplit(a['href'])
  if u.scheme or u.netloc or not u.path:continue
  target=(p.parent/unquote(u.path)).resolve();assert target.is_relative_to(R) and target.is_file(),(p.name,a['href']);links_checked+=1
assert (local_dom,accepted_dom,pending_dom)==(local,accepted,pending)
for p in [R/'index.html',R/'statistics.html',R/'downloads.html',R/'sobre.html',R/'all-lemmas.html']:
 page=soup(p)
 for a in page.select('a[href]'):
  u=urlsplit(a['href'])
  if u.scheme or u.netloc or not u.path:continue
  target=(p.parent/unquote(u.path)).resolve();assert target.is_relative_to(R) and target.is_file(),(p.name,a['href']);links_checked+=1
indexpage=soup(R/'index.html');assert indexpage.select_one('#authority') and indexpage.select_one('#realization option[value="encoded_in_rel"]')
assert [o['value'] for o in indexpage.select('#valency option')][1:]==[str(v) for v in sorted({x['valency'] for x in ib.values() if x['valency'] is not None})]
forbidden=['baseline_not_started_annotation','frozen_passage1_record','eventual_reconciliation_target','published_base_commit','source_repository_credential','/workspace/','/home/bryan/','PHD_KNOWLEDGE_BRIDGE','ACK_ORCH325_ORIGINAL','ROLLBACK_TO_','send_now']
for p in list((R/'data').glob('*.jsonl'))+list((R/'jsons').glob('*.json')):
 text=p.read_text()
 assert not any(s in text for s in forbidden),(p.name,'private administrative data')
manifest=json.loads((R/'data/manifest.json').read_text());assert manifest['counts']==index['counts']
for f in manifest['files']:
 p=R/f['path'];b=p.read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'],f['path']
report={'result':'PASS','base_commit':'fe8a948babd1e6e6e83a7fd5bfbda62cdaa90861','counts':index['counts'],'preserved_formal_annotations':6024,'preserved_non_delta_technical_lines':6326,'local_spans_and_heads':5139,'local_frame_identity_aliases':61,'manual_instances_in_json_jsonl_and_dom':302,'nested_argument_overlap_tokens_preserved':9,'nested_argument_overlap_instances':[10214,12500],'rel_argument_overlap_new':0,'all_occurrence_rows':11021,'local_highlight_segments':local_marks,'internal_links_checked':links_checked,'ud_sentences_preserved_or_additively_recovered':5906,'lexical_evidence_byte_exact':True,'private_administrative_data_in_public_payloads':False,'global_gold_promotion':False,'browser_qa':'separate required browser report'}
(A/'DATA_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
