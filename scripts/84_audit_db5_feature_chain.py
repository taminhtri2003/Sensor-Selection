"""Reconstruct every saved DB5 E1 feature using the actual historical filter implementation."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import pandas as pd
from scipy.signal import butter,filtfilt
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
REV=ROOT/'manuscript_revision/20261014'
spec=importlib.util.spec_from_file_location('db5_extraction',ROOT/'scripts/33_db5_features.py');db=importlib.util.module_from_spec(spec);spec.loader.exec_module(db)

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def main():
 saved=pd.read_parquet(ROOT/'data/features/db5_features.parquet')
 files=sorted(db.RAW.rglob('*_E1_*.mat'))
 if len(files)!=10 or set(saved.participant_id)!=set(range(1,11)):raise ValueError('DB5 cohort is not complete')
 high=min(db.BAND_HIGH,.45*db.FS-1.)
 b,a=butter(db.BAND_ORDER,[db.BAND_LOW/(db.FS/2),high/(db.FS/2)],btype='bandpass')
 rows=[]
 for path in files:
  d=db.sio.loadmat(str(path));emg=np.asarray(d['emg'],dtype=np.float64)[:,:16]
  labels=np.asarray(d['restimulus']).ravel().astype(int);reps=np.asarray(d.get('rerepetition',d['repetition'])).ravel().astype(int)
  filtered=db.bandpass_filter(emg,fs=db.FS,lowcut=db.BAND_LOW,highcut=db.BAND_HIGH,order=db.BAND_ORDER)
  direct=filtfilt(b,a,emg,axis=0)
  if not np.array_equal(filtered,direct):raise ValueError('filter implementation differs from documented effective cutoff')
  values=[];metadata=[]
  for gesture,rep,start,stop in db.contiguous_blocks(labels,reps):
   if gesture==0 or rep==0:continue
   windows,_=db.create_sliding_windows(filtered[start:stop],fs=db.FS,window_ms=db.WINDOW_MS,overlap_pct=db.OVERLAP_PCT)
   for i,window in enumerate(windows):
    values.append(db.extract_window_features(window,fs=db.FS,zc_thresh=db.THRESH,ssc_thresh=db.THRESH,wamp_thresh=db.THRESH).astype(np.float32));metadata.append((gesture,rep,i))
  pid=int(path.parent.name[1:]);stored=saved[saved.participant_id==pid]
  computed=np.asarray(values,dtype=np.float32);meta=np.asarray(metadata)
  labels_match=np.array_equal(stored[['gesture_id','trial_id','window_idx']].to_numpy(),meta)
  features_match=np.array_equal(stored[db.FEAT_NAMES].to_numpy(),computed)
  if not labels_match or not features_match:raise ValueError('DB5 raw reconstruction differs for participant'+str(pid))
  rows.append({'participant_id':pid,'n_windows':len(computed),'n_gestures':len(set(meta[:,0])),'n_repetitions':len(set(meta[:,1])),'all_features_exact':features_match,'labels_exact':labels_match,'max_absolute_feature_difference':float(abs(stored[db.FEAT_NAMES].to_numpy()-computed).max()),'raw_file':str(path.relative_to(ROOT)).replace('\\','/'),'raw_sha256':sha(path)})
  print('DB5 participant'+str(pid)+': all'+str(len(computed))+' raw-derived feature rows match',flush=True)
 out=REV/'reproducibility/db5_feature_reconstruction.csv';pd.DataFrame(rows).sort_values('participant_id').to_csv(out,index=False)
 report={'status':'PASS','participants':len(rows),'windows':sum(row['n_windows'] for row in rows),'requested_low_hz':db.BAND_LOW,'requested_high_hz':db.BAND_HIGH,'effective_low_hz':db.BAND_LOW,'effective_high_hz':high,'fs_hz':db.FS,'filter_order_argument':db.BAND_ORDER,'interpretation':'reported requested95Hz was clipped to89Hz by min(highcut,0.45*fs-1); saved features exactly reproduce actual implementation, so no result metric is changed','source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),ROOT/'scripts/33_db5_features.py',ROOT/'src/semg_sparse/preprocessing/filters.py',ROOT/'src/semg_sparse/features/handcrafted.py',ROOT/'data/features/db5_features.parquet']}}
 (REV/'reports/db5_feature_chain.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('PASS: complete DB5 feature reconstruction and actual89Hz upper cutoff verified',flush=True)
if __name__=='__main__':main()
