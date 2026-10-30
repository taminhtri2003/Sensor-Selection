"""Current fail-closed, cross-platform study build; no legacy/fabricated generators."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def run(args, name, cwd=ROOT):
    logs = ROOT / 'runs/completion_20260922'
    logs.mkdir(parents=True, exist_ok=True)
    print(f'RUN {name}', flush=True)
    with (logs / f'{name}.log').open('w', encoding='utf-8') as f:
        subprocess.run(args, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--finish-experiments', action='store_true')
    ap.add_argument('--no-pdf', action='store_true')
    args = ap.parse_args()
    local_deps = ROOT / '.test_dependencies'
    if local_deps.exists():
        os.environ['PYTHONPATH'] = str(local_deps) + os.pathsep + os.environ.get('PYTHONPATH','')
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    if args.finish_experiments:
        run([sys.executable,'scripts/36_bipolar_sensitivity.py','--device','cuda','--k-workers','4','--resume'], 'bipolar')
        run([sys.executable,'scripts/53_participant_attribution.py'], 'participant_attribution')
    run([sys.executable,'-m','pytest','-q','tests'], 'tests')
    run([sys.executable,'scripts/57_penalty_gate.py'], 'upgraded_penalty_gate')
    for script in ('59_audit_feature_chain.py','audit_leakage.py','28_statistics.py'):
        run([sys.executable, f'scripts/{script}'], Path(script).stem)
    # Current repository instructions limit new analyses to GRABMyo and DB5.
    run([sys.executable,'scripts/37_secondary_statistics.py','h2','h3','h4','cs','ni','h1holm'], 'secondary_statistics')
    run([sys.executable,'scripts/16_verify_results.py'], 'publication_gate')
    run([sys.executable,'manuscript/revision_scripts/fill_bipolar_text.py'], 'bipolar_text')
    run([sys.executable,'scripts/58_study_diagrams.py'], 'study_diagrams')
    for script in ('42_generate_tables.py','44_figures.py','45_check_manuscript_numbers.py',
                   '47_claim_evidence_matrix.py','41_generate_study_report.py'):
        run([sys.executable,f'scripts/{script}'], Path(script).stem)
    results = {'analysis_checks': 'PASS', 'pdf_build': 'NOT_REQUESTED',
               'submission_ready': False, 'reason': 'Author declarations require author input.'}
    if not args.no_pdf:
        for doc in ('supplementary_iop','main_iop'):
            # A stale numeric-style bibliography can make the first author-year
            # pass fail before BibTeX gets a chance to regenerate it.
            for suffix in ('.aux', '.bbl', '.blg', '.out'):
                (ROOT / 'manuscript' / f'{doc}{suffix}').unlink(missing_ok=True)
            command = ['pdflatex','-interaction=nonstopmode','-halt-on-error',f'{doc}.tex']
            run(command, f'{doc}_pass1', ROOT / 'manuscript')
            if doc == 'main_iop':
                run(['bibtex', doc], f'{doc}_bibtex', ROOT / 'manuscript')
            run(command, f'{doc}_pass2', ROOT / 'manuscript')
            run(command, f'{doc}_pass3', ROOT / 'manuscript')
            log = (ROOT / f'manuscript/{doc}.log').read_text(errors='replace')
            if 'undefined' in log or 'Fatal error' in log:
                raise RuntimeError(f'{doc}: unresolved references or compilation error')
        results['pdf_build'] = 'PASS_PENDING_VISUAL_REVIEW'
        package = ROOT / 'FINAL_PACKAGE/review_20260922'
        package.mkdir(parents=True, exist_ok=True)
        for filename in ('main_iop.pdf','supplementary_iop.pdf'):
            shutil.copy2(ROOT / 'manuscript' / filename, package / filename)
        for filename in ('study_review_20260922.md','final_study_report.md'):
            shutil.copy2(ROOT / 'reports' / filename, package / filename)
        with zipfile.ZipFile(package/'manuscript_sources.zip','w',zipfile.ZIP_DEFLATED) as z:
            manuscript=ROOT/'manuscript'
            paths=[manuscript/'main_iop.tex',manuscript/'supplementary_iop.tex',
                   manuscript/'iopjournal.cls',manuscript/'references.bib',manuscript/'orcid.pdf']
            for directory,pattern in (('sections','*.tex'),('generated','*.tex'),
                                      ('generated','*provenance.csv'),('tables','*.tex'),('figures','*.pdf')):
                paths += list((manuscript/directory).glob(pattern))
            for path in paths:
                if 'putemg' not in path.name:
                    z.write(path,path.relative_to(manuscript))
        shutil.copy2(ROOT/'reports/final_study_report.md',ROOT/'docs/FINAL_STUDY_REPORT.md')
        with zipfile.ZipFile(package/'participant_attribution_results.zip','w',zipfile.ZIP_DEFLATED) as z:
            for path in (ROOT/'artifacts/participant_attribution').iterdir():
                if path.is_file() and path.suffix in ('.csv','.json'):
                    z.write(path,path.name)
        fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in package.iterdir() if p.is_file() and p.name != 'SHA256.json'}
        (package / 'SHA256.json').write_text(json.dumps(fingerprints, indent=2), encoding='utf-8')
    (ROOT / 'reports/completion_gate.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)


if __name__ == '__main__':
    main()
