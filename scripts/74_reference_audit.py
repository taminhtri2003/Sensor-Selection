"""Verify cited bibliography DOI metadata through Crossref; preserve unavailable statuses."""
from pathlib import Path
import re,json,urllib.request,difflib
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';BASE=REV/'manuscript';OUT=REV/'reproducibility/literature';OUT.mkdir(parents=True,exist_ok=True)
def entries(text):
 records={}
 for m in re.finditer(r'@\w+\s*\{\s*([^,]+),',text):
  start=m.end();depth=1;i=start
  while i<len(text) and depth:
   depth+=int(text[i]=='{')-int(text[i]=='}');i+=1
  records[m.group(1).strip()]=text[start:i-1]
 return records

def field(entry,key):
 m=re.search(r'\b'+key+r'\s*=\s*\{([^}]*)\}',entry,re.I);return m.group(1) if m else ''
def main():
 e=entries((BASE/'references.bib').read_text(encoding='utf-8'));used=set()
 for path in BASE.rglob('*.tex'):
  for m in re.finditer(r'\\cite\w*\s*(?:\[[^]]*\])*\{([^}]+)\}',path.read_text(encoding='utf-8')):used.update(x.strip() for x in m.group(1).split(','))
 missing=used-set(e)
 if missing:raise ValueError('Missing bibliography entries '+str(missing))
 def work(key):
  title=field(e[key],'title');doi=field(e[key],'doi');url=field(e[key],'url');row={'key':key,'doi':doi,'manuscript_title':title,'url':url,'status':'no DOI; primary URL/source audit required','verified_title':'','title_similarity':None}
  if not doi:return row
  try:
   req=urllib.request.Request('https://api.crossref.org/works/'+urllib.parse.quote(doi,safe=''),headers={'User-Agent':'ResearchMetadataAudit/1.0'})
   with urllib.request.urlopen(req,timeout=45) as r:d=json.load(r)['message']
   (OUT/(key+'_verified_crossref.json')).write_text(json.dumps(d,indent=2),encoding='utf-8');verified=d['title'][0];clean=lambda s:re.sub(r'[^a-z0-9]','',s.lower());sim=difflib.SequenceMatcher(None,clean(title),clean(verified)).ratio();row.update(status='DOI metadata retrieved',verified_title=verified,title_similarity=sim)
  except Exception as exc:row['status']='metadata unavailable: '+str(exc)
  return row
 with ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(work,sorted(used)))
 pd.DataFrame(rows).to_csv(OUT/'cited_reference_audit.csv',index=False)
 for row in rows:
  if row['status']!='DOI metadata retrieved' or row['title_similarity']<.8:print(row['key'],row['status'],row['title_similarity'],flush=True)
 print(f'Cited entries={len(used)}; DOI metadata retrieved={sum(r["status"]=="DOI metadata retrieved" for r in rows)}',flush=True)
if __name__=='__main__':main()
