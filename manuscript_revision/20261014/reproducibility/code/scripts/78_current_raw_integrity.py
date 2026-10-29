"""Current complete downloaded-data audit, with isolated outputs and official archive identities."""
from pathlib import Path
import importlib.util,hashlib,json,zipfile,sys
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';DOC=REV/'reproducibility/dataset_documents'
def digest_stream(stream,algorithm):
 h=hashlib.new(algorithm)
 for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def digest_file(path,algorithm):
 with path.open('rb') as f:return digest_stream(f,algorithm)
def main():
 spec=importlib.util.spec_from_file_location('raw_audit',ROOT/'scripts/audit_grabmyo_integrity.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT_CSV=REV/'reproducibility/grabmyo_current_integrity.csv';m.OUT_MD=REV/'reports/current_grabmyo_integrity.md'
 if m.main()!=0:raise RuntimeError('GRABMyo checksum audit failed')
 zenodo=json.loads((DOC/'zenodo_1000116.json').read_text(encoding='utf-8'));assert 'dataset 5' in zenodo['metadata']['title'].lower();files={f['key']:f['checksum'].split(':')[-1] for f in zenodo['files']};raw=ROOT/'data/raw/ninapro_db5';manifest=pd.read_csv(ROOT/'data/manifests/db5_manifest.csv');rows=[];extracted=[]
 for row in manifest.to_dict('records'):
  archive=raw/row['file'];expected=files[archive.name];md5=digest_file(archive,'md5');sha=digest_file(archive,'sha256');ok=md5==expected and sha==row['sha256'];rows.append({'archive':archive.name,'official_record':1000116,'official_md5':expected,'actual_md5':md5,'sha256':sha,'matches_official_and_saved':ok})
  with zipfile.ZipFile(archive) as z:
   mats=[name for name in z.namelist() if name.lower().endswith('.mat')]
   if len(mats)!=3:raise ValueError('DB5 archive does not have three exercise files')
   for name in mats:
    path=raw/name
    if not path.is_file():path=raw/archive.stem/Path(name).name
    if not path.is_file():raise FileNotFoundError(str(path))
    with z.open(name) as f:expected_sha=digest_stream(f,'sha256')
    actual_sha=digest_file(path,'sha256');extracted.append({'archive':archive.name,'member':name,'local_path':str(path.relative_to(ROOT)),'archive_member_sha256':expected_sha,'local_sha256':actual_sha,'matches':expected_sha==actual_sha})
  print('DB5 verified '+archive.name,flush=True)
 pd.DataFrame(rows).to_csv(REV/'reproducibility/db5_current_archive_integrity.csv',index=False);pd.DataFrame(extracted).to_csv(REV/'reproducibility/db5_current_extracted_integrity.csv',index=False)
 if not all(r['matches_official_and_saved'] for r in rows) or not all(r['matches'] for r in extracted):raise ValueError('DB5 archive/extracted integrity failed')
 (REV/'reports/current_raw_integrity.json').write_text(json.dumps({'status':'PASS','GRABMyo':'all published SHA256 entries checked','DB5_archives':len(rows),'DB5_extracted_exercises':len(extracted),'DB5_record':1000116,'DB4_record_not_used':1000138,'source_link_correction':'the PLOS article data-availability prose reverses the two archive IDs; official Zenodo titles/sensors and checksums resolve identity'},indent=2),encoding='utf-8');print('PASS: current complete downloaded-data integrity verified',flush=True)
if __name__=='__main__':main()
