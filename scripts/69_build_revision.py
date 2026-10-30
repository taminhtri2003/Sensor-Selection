"""Assemble and compile the completed revision; visual acceptance is a separate recorded step."""
import hashlib,json,platform,subprocess,sys,shutil,re
from datetime import datetime,timezone
from pathlib import Path
import importlib.metadata as metadata
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';BASE=REV/'manuscript';REP=REV/'reports'
sys.path.insert(0, str(ROOT))
from src.semg_sparse.reporting import snapshot_run_provenance
def run(args,log,cwd=ROOT):
 if log.exists():
  history=REP/'build_history';history.mkdir(exist_ok=True);destination=history/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+log.name)
  if not log.resolve().is_relative_to(REV.resolve()) or not destination.resolve().is_relative_to(REV.resolve()):raise ValueError('build-log archive escapes revision')
  log.rename(destination)
 with log.open('w',encoding='utf-8') as f:subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 (REP/'build_status.json').write_text(json.dumps({'status':'building; previous acceptance invalidated','strict_gate':'PENDING'}),encoding='utf-8')
 python=sys.executable
 run([python,str(ROOT/'scripts/63_completion_statistics.py')],REP/'completion_statistics_execution.log')
 run([python,str(ROOT/'scripts/66_revision_statistics.py')],REP/'revision_statistics_execution.log')
 run([python,str(ROOT/'scripts/16_verify_results.py'),'--revision-dir',str(REV)],REP/'strict_revision_verification.log')
 run([python,str(ROOT/'scripts/73_revision_reports.py')],REP/'revision_reports_execution.log')
 for stem in ('main','supplementary'):
  run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error',stem+'.tex'],REP/(stem+'_compile_pass1.log'),BASE)
  if stem=='main':run(['bibtex',stem],REP/'main_bibliography_build.log',BASE)
  for j in (2,3):run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error',stem+'.tex'],REP/f'{stem}_compile_pass{j}.log',BASE)
  log=(BASE/(stem+'.log')).read_text(encoding='utf-8',errors='replace')
  if 'undefined' in log.lower() or 'multiply defined' in log.lower():raise RuntimeError(stem+' has unresolved citations/references')
 # Expand numeric macros for the structured abstract's word-count audit.
 macros={}
 for file in ['results_macros.tex','revision_macros.tex']:
  text=(BASE/'generated'/file).read_text(encoding='utf-8');macros.update(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^\n]+)\}',text))
 source=(BASE/'main.tex').read_text(encoding='utf-8');abstract=source.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
 for key,value in sorted(macros.items(),key=lambda kv:-len(kv[0])):abstract=re.sub(r'\\'+key+r'\b',lambda m:value,abstract)
 plain=re.sub(r'\\[A-Za-z]+','',abstract);plain=re.sub(r'[{}$]','',plain);word_count=len(plain.split())
 if word_count>250:raise ValueError('abstract exceeds250 words: '+str(word_count))
 (REP/'abstract_word_count.json').write_text(json.dumps({'words':word_count,'limit':250,'method':'expand generated numerical macros, remove TeX control words, whitespace count','abstract':plain},indent=2),encoding='utf-8')
 # Snapshot the executable source graph after experiments complete; original fingerprints persist.
 code=REV/'reproducibility/code';code.mkdir(exist_ok=True)
 for name in ('scripts','src','configs','tests'):
  dest=code/name;dest.mkdir(exist_ok=True)
  for p in (ROOT/name).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.yaml','.yml','.toml','.md'):
    target=dest/p.relative_to(ROOT/name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 # Preserve original build metadata separately; it is not a lock for the executed environment.
 legacy=code/'legacy_build_metadata';legacy.mkdir(exist_ok=True)
 for name in ('pyproject.toml','requirements-lock.txt','uv.lock','Makefile','AGENTS.md'):
  if (ROOT/name).is_file():shutil.copy2(ROOT/name,legacy/name)
 (legacy/'README.md').write_text('These are the repository metadata as found. The historical lock differs from the executed environment; use reproducibility/requirements_current.txt and environment.json for this revision. Placeholder package-author metadata is not an author declaration.\n',encoding='utf-8')
 # Retain the exact quantitative inputs behind the manuscript, without copying raw signal caches.
 inputs=REV/'reproducibility/verified_inputs';inputs.mkdir(exist_ok=True);source_paths={'data/features/db5_features.parquet'}
 for file in ['macro_provenance.csv','revision_macro_provenance.csv']:
  source_paths.update(pd.read_csv(BASE/'generated'/file).source)
 source_paths.update(pd.read_csv(REV/'figures/figure_provenance.csv').source)
 for folder in ['metrics','statistics','rankings','selection_baselines','stability','cross_session','faithfulness','db5','bipolar','predictions','prediction_audit','completion_analyses']:
  for path in (ROOT/'artifacts'/folder).rglob('*'):
   if path.is_file() and path.suffix in ('.csv','.json','.parquet') and 'putemg' not in str(path).lower():source_paths.add(str(path.relative_to(ROOT)))
 for folder in ('data/manifests','data/cache'):
  for path in (ROOT/folder).rglob('*'):
   if path.is_file() and (path.suffix=='.json' or (folder=='data/manifests' and path.suffix=='.csv')) and 'putemg' not in str(path).lower():source_paths.add(str(path.relative_to(ROOT)))
 for name in ('SHA256SUMS.txt','RECORDS','LICENSE.txt','readme.txt','subject-info.csv','MotionSequence.txt'):
  if (ROOT/name).is_file():source_paths.add(name)
 for relative in sorted(source_paths):
  path=ROOT/relative
  if path.is_relative_to(REV):continue
  if path.is_file():
   target=inputs/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
 (REV/'reproducibility/verified_input_sources.json').write_text(json.dumps(sorted(source_paths),indent=2),encoding='utf-8')
 packages={}

 for name in ('numpy','pandas','scipy','scikit-learn','xgboost','matplotlib','pytest','pyarrow','h5py','tabulate','PyYAML'):
  packages[name]=metadata.version(name)
 local_packages={d.metadata['Name']:d.version for d in metadata.distributions(path=[str(ROOT/'.test_dependencies')])}
 try:wfdb_version=metadata.version('wfdb')
 except metadata.PackageNotFoundError:
  if 'wfdb' not in local_packages:raise RuntimeError('raw-audit wfdb distribution metadata missing')
  wfdb_version=local_packages['wfdb']
 (REV/'reproducibility/local_dependency_versions.json').write_text(json.dumps(local_packages,indent=2),encoding='utf-8')
 requirements={**packages,'wfdb':wfdb_version}
 (REV/'reproducibility/requirements_current.txt').write_text('# Executed revision analysis/raw-audit/test dependencies; Python3.10.\n'+'\n'.join(n+'=='+v for n,v in requirements.items())+'\n',encoding='utf-8')
 hardware={'processor':platform.processor(),'machine':platform.machine()}
 if platform.system()=='Windows':
  query="$c=Get-CimInstance Win32_Processor; $m=Get-CimInstance Win32_ComputerSystem; @{cpu=$c.Name;physical_cores=$c.NumberOfCores;logical_processors=$c.NumberOfLogicalProcessors;RAM_bytes=$m.TotalPhysicalMemory}|ConvertTo-Json -Compress"
  hardware['Windows_CIM']=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True))
 try:
  gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True)
  hardware['GPU_query']=gpu.stdout.strip() if gpu.returncode==0 else 'query unavailable'
 except FileNotFoundError:hardware['GPU_query']='nvidia-smi unavailable'
 execution=snapshot_run_provenance(ROOT,REV/'reproducibility/execution')
 (REV/'reproducibility/environment.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':packages,'hardware':hardware,'execution':execution},indent=2),encoding='utf-8')
 with (REV/'reproducibility/pip_freeze.txt').open('w',encoding='utf-8') as f:subprocess.run([python,'-m','pip','freeze'],stdout=f,check=True)
 for path in ROOT.glob('environment*'):
  if path.is_file():shutil.copy2(path,REV/'reproducibility'/path.name)
 shutil.copy2(ROOT/'scripts/67_revision_figures.py',REV/'figures/source/67_revision_figures.py')
 # Reproducibility source manifest; package final checksums are written after visual QA.
 rows=[]
 for p in sorted(code.rglob('*')):
  if p.is_file():rows.append({'path':str(p.relative_to(REV)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
 pd.DataFrame(rows).to_csv(REV/'reproducibility/source_manifest.csv',index=False)
 (REP/'build_status.json').write_text(json.dumps({'status':'compiled, awaiting visual and narrative inspection','narrative_review':'PENDING: compare interpretation with current independent results','abstract_words':word_count,'pdfs':['manuscript/main.pdf','manuscript/supplementary.pdf'],'strict_gate':'PASS','source_snapshot':'reproducibility/code'},indent=2),encoding='utf-8')
 print('PASS: numerical verification and PDF compilation complete; review current-result interpretation and every rendered page before release',flush=True)
if __name__=='__main__':main()
