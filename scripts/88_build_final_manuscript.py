from pathlib import Path
import subprocess,json,re,hashlib,csv
ROOT=Path('F:/grabmyo_data');OLD=ROOT/'manuscript_revision/20261014';OUT=ROOT/'manuscript_final/20261016';SRC=OUT/'manuscript';QA=ROOT/'manuscript_final/author_materials/20261016';checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,label):
    if not ok:raise ValueError(label)
    checks.append(label)
def names(s):return s.replace('RevFixedSwapSeed','FixedLayoutMonteCarlo').replace('DBFiveSeed','DBFiveMonteCarlo').replace('BipSeed','BipolarMonteCarlo')
# The scientific results were verified by scripts/16_verify_results.py. Check that
# this presentation-only build retains that verified numerical source graph.
report=json.loads((OLD/'reports/verification.json').read_text(encoding='utf-8'))
check(report['status']=='PASS' and len(report['checks'])==4593,'scripts/16 verified scientific source record: 4593 checks')
for row in csv.DictReader((OLD/'reproducibility/package_manifest.csv').open(encoding='utf-8')):
    check(sha(OLD/row['path'])==row['sha256'],'frozen package unchanged: '+row['path'])
for old,new in [('results_macros.tex','results_macros.tex'),('revision_macros.tex','analysis_macros.tex')]:
    parse=lambda t:dict(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^\n]+)\}',names(t)))
    check(parse((OLD/'manuscript/generated'/old).read_text(encoding='utf-8'))==parse((SRC/'generated'/new).read_text(encoding='utf-8')),'all numerical macro values unchanged: '+new)
for p in (OLD/'manuscript').rglob('*.tex'):
    if 'macros' in p.name:continue
    q=SRC/p.relative_to(OLD/'manuscript')
    if p.name=='ni_audit.tex':q=SRC/'generated/count_inference.tex'
    original=p.read_text(encoding='utf-8');current=q.read_text(encoding='utf-8')
    # Captions and headers can change; numerical table cells cannot.
    cells=lambda t:[re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?',line) for line in t.splitlines() if '&' in line and re.search(r'^\s*(?:[0-9$\\]|Derived bipolar|NinaPro|Geometric|Participant|Fold|RF|Rest|Window|SHAP|PERM)',line)]
    a=cells(original);b=cells(current)
    if '\\begin{tabular}' in original:
        # Restrict to table bodies and compare all numerical payloads directly.
        def payload(t):
            blocks=re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)
            return [[re.findall(r'\d+(?:\.\d+)?',x) for x in block.splitlines() if '&' in x] for block in blocks]
        check(payload(original)==payload(current),'all numerical table cells unchanged: '+p.name)
for p in (OUT/'figures/vector').glob('*.pdf'):check(sha(p)==sha(OLD/'figures/vector'/p.name),'figure unchanged: '+p.name)
for folder,source in [('data/statistical_results','tables'),('data/figure_data','figures/source_data')]:
    for p in (OUT/folder).glob('*.csv'):
        original=p.name.replace('count_inference','completed_ni_audit').replace('minimum_counts','kstar_audit').replace('noninferiority_comparisons','noninferiority_audit').replace('selector_activity','selection_change_audit')
        check(sha(p)==sha(OLD/source/original),'supplementary data unchanged: '+p.name)

for stem in ('main','supplementary'):
    for n in range(1,4):
        args=['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error',stem+'.tex']
        with (QA/f'{stem}_compile_{n}.log').open('w',encoding='utf-8') as f:subprocess.run(args,cwd=SRC,stdout=f,stderr=subprocess.STDOUT,check=True)
        if n==1 and stem=='main':
            with (QA/'bibliography_build.log').open('w',encoding='utf-8') as f:subprocess.run(['bibtex',stem],cwd=SRC,stdout=f,stderr=subprocess.STDOUT,check=True)
    log=(SRC/(stem+'.log')).read_text(encoding='utf-8',errors='replace')
    check(not re.search(r'undefined|multiply defined|Overfull \\hbox|Overfull \\vbox',log,re.I),'no unresolved references or overflowing boxes: '+stem)
    text=subprocess.check_output(['pdftotext','-layout',str(SRC/(stem+'.pdf')),'-'],text=True,encoding='utf-8')
    (QA/(stem+'_text.txt')).write_text(text,encoding='utf-8')
    check(not re.search(r'\b(?:revision|progress|seed(?:s)?|audit|gate|fingerprint|amendment|rerun|placeholder)\b|AUTHOR INPUT|20260728',text,re.I),'no workflow or seed wording in reader PDF: '+stem)
    check('?'+'?' not in text,'no unresolved visible references: '+stem)
    check('45%' in text if stem=='main' else True,'adverse numerical sensitivity retained: '+stem)
macros={}
for f in ('results_macros.tex','analysis_macros.tex'):macros.update(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^\n]+)\}',(SRC/'generated'/f).read_text(encoding='utf-8')))
a=(SRC/'main.tex').read_text(encoding='utf-8').split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
for key,value in sorted(macros.items(),key=lambda kv:-len(kv[0])):a=re.sub(r'\\'+key+r'\b',lambda m:value,a)
a=re.sub(r'\\[A-Za-z]+','',a);a=re.sub(r'[{}$]','',a);words=len(a.split());check(words<=250,'abstract word limit: '+str(words))
(QA/'presentation_verification.json').write_text(json.dumps({'status':'PASS','checks':checks,'check_count':len(checks),'scientific_verification':'unchanged 4593-check PASS record from scripts/16_verify_results.py','abstract_words':words,'visual_acceptance':'PENDING'},indent=2),encoding='utf-8')
print('PASS:',len(checks),'presentation and source-integrity checks; abstract',words,'words')
