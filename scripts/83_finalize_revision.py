"""Finalize a verified revision only after recorded inspection of every PDF page."""
from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parent.parent
REV=ROOT/'manuscript_revision/20261014'
REP=REV/'reports'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def main():
 gate=json.loads((REP/'verification.json').read_text(encoding='utf-8'))
 if gate['status']!='PASS':raise RuntimeError('numerical revision gate has not passed')
 build=json.loads((REP/'build_status.json').read_text(encoding='utf-8'))
 if build['strict_gate']!='PASS' or build['abstract_words']>250:raise RuntimeError('build acceptance missing')
 visual=json.loads((REP/'visual_acceptance.json').read_text(encoding='utf-8'))
 pdfs=[]
 for stem in ('main','supplementary'):
  path=REV/'manuscript'/(stem+'.pdf');record=visual['pdfs'][stem]
  info=subprocess.check_output(['pdfinfo',str(path)],text=True,encoding='utf-8',errors='replace')
  pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
  if record['sha256']!=sha(path):raise RuntimeError(stem+' changed after visual inspection')
  inspected=record['inspected_pages']
  if sorted(inspected)!=list(range(1,pages+1)) or record['status']!='PASS':raise RuntimeError(stem+' has uninspected pages')
  text=subprocess.check_output(['pdftotext','-layout',str(path),'-'],text=True,encoding='utf-8',errors='replace')
  if re.search(r'\[\?\??\]|undefined control sequence',text,re.I):raise RuntimeError(stem+' contains unresolved output')
  log=path.with_suffix('.log').read_text(encoding='utf-8',errors='replace')
  if 'undefined' in log.lower() or 'multiply defined' in log.lower():raise RuntimeError(stem+' has unresolved references')
  pdfs.append({'stem':stem,'pages':pages,'sha256':sha(path),'author_placeholders':text.count('AUTHOR INPUT REQUIRED')})
 tests=(REP/'final_tests.log').read_text(encoding='utf-8',errors='replace')
 if not re.search(r'\b\d+ passed\b',tests) or re.search(r'\bFAILED\b|\bERROR\b',tests):raise RuntimeError('final tests have not passed')
 statuses=json.loads((REP/'live_experiment_status.json').read_text(encoding='utf-8'))
 if not all(value==43 for value in statuses.values()):raise RuntimeError('participant track incomplete')
 evidence=[
 ('1','Novelty bounded by verified primary literature','Qualified pass','02_novelty_and_literature.md; comparative_matrix.csv; unknown full-method fields explicit'),
 ('2','Primary NI independently audited','Pass','verification.json; primary_matched_noninferiority.csv; noninferiority_audit.csv'),
 ('3','Outer and inner participant exclusion','Qualified pass','Fold fitting/scaling/ranking exclusion verified; historical pooled threshold and test-fold budget development remain disclosed'),
 ('4','Original versus added analyses distinguished','Pass','Methods; Supplementary chronology; exploratory protocol and eight amendments'),
 ('5','Incremental attribution value critically tested','Pass','Primary geometry contrast; shared-model comparison; random and deletion results'),
 ('6','Negative findings retained','Pass','Penalty gate, participant/gesture losses, geometry mean uncertainty and split-layout boundary'),
 ('7','Twelve-electrode statement has mean/protocol scope','Pass','Main Results and Conclusion; no individual preservation claim'),
 ('8','Fixed-layout claim bounded by available evidence','Qualified pass','Two distinct layouts; count-development exposure; no fresh independent same-montage cohort'),
 ('9','Figures generated from experimental files','Pass','figure_provenance.csv; source_data; six main and seven supplementary vector figures'),
 ('10','Numerical consistency verified','Pass','scripts/16_verify_results.py --revision-dir manuscript_revision/20261014; macro provenance'),
 ('11','Coherent manuscript argument and legible layout','Pass after recorded inspection','visual_acceptance.json; all PDF pages inspected; abstract word-count audit'),
 ('12','Unresolved declarations and missing evidence explicit','Qualified pass','unresolved_author_inputs.md; author deferred declarations; ethics remains unresolved'),
 ('13','Reproduction materials and source traceability','Pass','source_manifest.csv; requirements_current.txt; verified_inputs; package_manifest.csv'),
 ('14','Substantive external peer-review draft','Qualified pass','Computational/editorial review complete; submission still requires author declarations and decisions')
 ]
 lines=['# Final quality control','', 'This is a completed computational and editorial peer-review draft. It is not an author-approved submission or independent prospective device validation. Ethics, funding, contributions, conflicts and public archive information remain explicitly unresolved or deferred.','', '| Criterion | Requirement | Decision | Evidence |','|---|---|---|---|']
 lines+=['| '+' | '.join(row)+' |' for row in evidence]
 lines+=['','## Executed acceptance','',f"The current revision gate passed {len(gate['checks'])} recorded checks. The abstract contains {build['abstract_words']} words (limit250).",'',tests.strip(),'','## Rendered-page acceptance','']
 for row in pdfs:lines.append(f"- {row['stem']}.pdf: {row['pages']} of {row['pages']} pages inspected; SHA256 `{row['sha256']}`; {row['author_placeholders']} explicit author-input markers.")
 lines+=['','Inspection covers figures, axis/legend text, table scaling, captions, page breaks, references and visible placeholders. The per-page record identifies the inspected PDF fingerprint. The original source-hash failure remains preserved; it is not relabeled a successful historical verification. The current revision route checks the fresh isolated extension. A negative scientific penalty result is distinct from a failed computational provenance gate.','','## Final files','', 'Native sources are manuscript/main.tex, manuscript/supplementary.tex and their local sections/generated/tables/bibliography/class files. Reports01-08, full-precision outputs, vector figures, prediction files, protocols and executable source snapshots accompany them. Raw data are not redistributed in this package.','']
 (REP/'08_final_quality_control.md').write_text('\n'.join(lines),encoding='utf-8')
 for n in range(1,9):
  if not list(REP.glob(f'{n:02d}_*.md')):raise RuntimeError(f'missing report{n:02d}')
 (REP/'final_release_status.json').write_text(json.dumps({'status':'computational/editorial draft complete; author declarations pending','gate':'PASS','visual':'PASS','pdfs':pdfs,'author_inputs':'reports/unresolved_author_inputs.md'},indent=2),encoding='utf-8')
 (REV/'README.md').write_text('''# GRABMyo electrode-selection revision -2026-10-14

Computational and editorial peer-review draft, with author declarations deferred. This package does not claim a submission-ready ethics/funding/conflict statement or prospective validation of a locked physical interface.

- Read manuscript/main.pdf and manuscript/supplementary.pdf. Their editable TeX, bibliography, class and local inputs are in manuscript/.
- Reports01-08 document the scientific/literature/method/statistical audits, additional experiments, revisions, claim evidence and final quality control. reports/unresolved_author_inputs.md preserves all outstanding author decisions.
- figures/ contains six main and seven supplementary figures as vector PDF/SVG,300dpi previews, source data and provenance.
- experiments/ and tables/ retain complete participant/gesture outputs, paired predictions, rankings, compute measurements and full-precision inference.
- reproducibility/README.md and RUN_ORDER.md distinguish frozen-record verification from a raw-data rerun. Current requirements, source snapshots, original inputs, protocols and checksums accompany them.
- reports/verification.json records the scripts/16_verify_results.py revision gate. reports/visual_acceptance.json records every inspected PDF page and its fingerprint. The final QC report explains the remaining scientific limits.

The primary claim concerns mean recognition performance under the evaluated offline protocol. Participant/gesture losses, uncertain direct geometric mean superiority, penalty findings and transfer boundaries remain visible in the manuscript. Negative scientific findings are not converted into positive results by changing seeds, margins or penalties.

original/ preserves superseded sources and selected records. These are history, not current results. In particular, the old invalid preliminary package and historical source-hash finding are explicitly distinguished from the current verified outputs. Raw recordings are obtained from the cited public repositories and are not duplicated here.

The package manifest hashes every file inside the dated package except itself. Archive CRC and an external SHA256 sidecar verify the accompanying zip. Any later edit or recompilation requires renewed verification and PDF-page inspection.
''',encoding='utf-8')
 build['status']='compiled and visually accepted; author declarations remain pending';build['visual_acceptance']='reports/visual_acceptance.json'
 (REP/'build_status.json').write_text(json.dumps(build,indent=2),encoding='utf-8')
 notes=REV/'reproducibility/SESSION_HANDOFF.md'
 if notes.exists():
  history=REV/'original/execution_notes';history.mkdir(exist_ok=True);destination=history/'SESSION_HANDOFF.md'
  if destination.exists():raise RuntimeError('execution-note history already exists; preserve both versions explicitly')
  notes.rename(destination)
 # Freeze package digests after QA. The manifest never attempts to hash itself.
 manifest=REV/'reproducibility/package_manifest.csv'
 files=[p for p in sorted(REV.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts]
 with manifest.open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader()
  for p in files:writer.writerow({'path':str(p.relative_to(REV)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)})
 archive=REV.parent/'grabmyo_revision_20261014.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p in files+[manifest]:z.write(p,arcname='20261014/'+str(p.relative_to(REV)).replace('\\','/'))
 with zipfile.ZipFile(archive) as z:
  if z.testzip() is not None:raise RuntimeError('archive CRC verification failed')
 archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
 print('PASS: final QA requirements, complete package manifest and archive CRC verified',flush=True)
 print(str(archive),flush=True)
if __name__=='__main__':main()
