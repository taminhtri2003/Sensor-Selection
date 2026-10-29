import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
import xgboost as xgb
import json

# Load cache
X = np.load('data/cache/loso_X.npy', mmap_mode='r')
y = np.load('data/cache/loso_y.npy', mmap_mode='r')
subj = np.load('data/cache/loso_subj.npy', mmap_mode='r')
with open('data/cache/loso_features.json') as f:
    fcols = json.load(f)

# Identify indices of IEMG
iemg_indices = [i for i, name in enumerate(fcols) if 'IEMG' in name]
non_iemg_indices = [i for i in range(len(fcols)) if i not in iemg_indices]

print(f"Total features: {len(fcols)}, IEMG features: {len(iemg_indices)}, Remaining: {len(non_iemg_indices)}")

# Test on 3 representative participants (e.g. 1, 10, 20) with fast subsampled model
SEED = 20260728
XGB_PARAMS = dict(n_estimators=50, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", device="cuda", random_state=SEED, verbosity=0)

results = []
for pid in [1, 10, 20]:
    te = subj == pid
    tr = ~te
    
    # Subsample training to 50k for fast sensitivity verification
    idx_tr = np.where(tr)[0]
    rng = np.random.default_rng(SEED + pid)
    sub_tr = rng.choice(idx_tr, size=50000, replace=False)
    
    Xtr_full = X[sub_tr]
    ytr = y[sub_tr]
    Xte_full = X[te]
    yte = y[te]
    
    # 1. Full 10 features (160)
    mu = Xtr_full.mean(axis=0)
    sd = Xtr_full.std(axis=0) + 1e-8
    m1 = xgb.XGBClassifier(**XGB_PARAMS)
    m1.fit((Xtr_full - mu)/sd, ytr)
    pred1 = m1.predict((Xte_full - mu)/sd)
    f1_full = f1_score(yte, pred1, average='macro')
    
    # 2. 9 features (144, IEMG removed)
    Xtr_no_iemg = Xtr_full[:, non_iemg_indices]
    Xte_no_iemg = Xte_full[:, non_iemg_indices]
    mu9 = Xtr_no_iemg.mean(axis=0)
    sd9 = Xtr_no_iemg.std(axis=0) + 1e-8
    m2 = xgb.XGBClassifier(**XGB_PARAMS)
    m2.fit((Xtr_no_iemg - mu9)/sd9, ytr)
    pred2 = m2.predict((Xte_no_iemg - mu9)/sd9)
    f1_no_iemg = f1_score(yte, pred2, average='macro')
    
    results.append({
        'participant': pid,
        'f1_10feats': f1_full,
        'f1_no_iemg': f1_no_iemg,
        'diff': f1_no_iemg - f1_full
    })
    print(f"Participant {pid}: 10 feats = {f1_full:.4f}, 9 feats (no IEMG) = {f1_no_iemg:.4f}, diff = {f1_no_iemg - f1_full:+.4f}")

df_res = pd.DataFrame(results)
print("\nMean diff:", df_res['diff'].mean())
df_res.to_csv('results/feature_sensitivity.csv', index=False)
