from pathlib import Path
import json,hashlib,csv,zipfile,re,shutil
ROOT=Path('F:/grabmyo_data');OUT=ROOT/'manuscript_final/20261016';SRC=OUT/'manuscript';QA=ROOT/'manuscript_final/author_materials/20261016'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Record visual acceptance only after inspecting every final rendered page.
visual={'status':'PASS','main_pages':12,'supplementary_pages':13,'all_pages_inspected':True,'render_dpi':110,'render_directory':'C:/Users/Minh Tri SHC/.codex/visualizations/2026/09/22/01a0c89f-1b02-7750-9a24-74a484af5a6d/final_manuscript_20261016_v2','checks':['No clipped text, tables or figures','No overlaps or broken references','Scientific conclusions and limitations retained','No progress, revision, seed, audit or verification-gate wording in reader PDFs','Mostly empty terminal pages eliminated'],'pdf_sha256':{x:sha(SRC/(x+'.pdf')) for x in ('main','supplementary')}}
(QA/'visual_acceptance.json').write_text(json.dumps(visual,indent=2),encoding='utf-8')
p=QA/'presentation_verification.json';v=json.loads(p.read_text(encoding='utf-8'));assert v['status']=='PASS';v['visual_acceptance']='PASS: all 25 pages inspected';p.write_text(json.dumps(v,indent=2),encoding='utf-8')
# Keep only TeX dependencies used by either article.
used=set()
def visit(p):
    p=p.resolve()
    if p in used:return
    used.add(p)
    for name in re.findall(r'\\input\{([^}]+)\}',p.read_text(encoding='utf-8')):
        q=SRC/(name if name.endswith('.tex') else name+'.tex');assert q.exists();visit(q)
for x in ('main.tex','supplementary.tex'):visit(SRC/x)
for p in SRC.rglob('*'):
    if not p.is_file():continue
    if p.suffix in {'.aux','.log','.blg','.out'} or (p.suffix=='.tex' and p.resolve() not in used):
        target=QA/'source_build_materials'/p.relative_to(SRC);target.parent.mkdir(parents=True,exist_ok=True)
        assert p.resolve().is_relative_to(OUT.resolve()) and target.resolve().is_relative_to(QA.resolve())
        shutil.move(str(p),str(target))
# Freeze the clean publication package. Internal records are outside it.
rows=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
with (QA/'publication_manifest.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
archive=ROOT/'manuscript_final/grabmyo_final_20261016.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for row in rows:z.write(OUT/row['path'],row['path'])
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={r['path'] for r in rows}
    for row in rows:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
(archive.with_suffix('.zip.sha256')).write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
shutil.copy2(ROOT/'STATUS.md',QA/'STATUS_before_final_presentation.md')
(ROOT/'STATUS.md').write_text('''# Final manuscript

Current publication files: manuscript_final/20261016/manuscript/main.pdf and supplementary.pdf.

Editable sources, vector figures and supplementary data: manuscript_final/20261016/.

Clean archive: manuscript_final/grabmyo_final_20261016.zip.

Author declarations awaiting confirmation are kept separately in manuscript_final/author_materials/20261016/author_declarations.md. The complete scientific and reproducibility record remains preserved in manuscript_revision/20261014/.
''',encoding='utf-8')
release={'status':'PASS','scientific_values':'unchanged','presentation_checks':v['check_count'],'visual_acceptance':visual,'package_files':len(rows),'archive':str(archive),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'author_declarations':'pending, separate from reader-facing package'}
(QA/'final_release.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','pages':[12,13],'checks':v['check_count'],'package_files':len(rows),'zip_bytes':archive.stat().st_size,'sha256':sha(archive)},indent=2))
