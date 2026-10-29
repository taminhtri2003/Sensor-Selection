"""Six real-data main figures and supplementary diagnostics, vector PDF/SVG + 300dpi PNG."""
from pathlib import Path
import hashlib,json,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse,Rectangle,FancyArrowPatch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';STAT=REV/'experiments/statistics';FIG=REV/'figures';sys.path.insert(0,str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics
plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.labelsize':12,'legend.fontsize':11,'figure.facecolor':'white'})
BLUE='#0072B2';ORANGE='#D55E00';GREEN='#009E73';PURPLE='#CC79A7';GREY='#666666';provenance=[]
def read(path,name):
 p=ROOT/path;d=pd.read_csv(p);out=FIG/'source_data'/(name+'_'+p.stem+'.csv');d.to_csv(out,index=False);provenance.append({'figure':name,'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'export':str(out.relative_to(REV))});return d
def stat(file,name):
 if file=='noninferiority_audit.csv' and '--completed-preview' in sys.argv:file='completed_ni_audit.csv'
 return read(str((STAT/file).relative_to(ROOT)),name)
def save(fig,name):
 for ext,folder in [('pdf','vector'),('svg','vector'),('png','preview')]:fig.savefig(FIG/folder/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)
def panel(ax,title):ax.set_title(title,loc='left',fontweight='bold',fontsize=12,pad=10)
def forest(ax,d,y=None,color=BLUE):
 y=np.arange(len(d)) if y is None else np.asarray(y);ax.errorbar(d.mean_diff,y,xerr=np.vstack([d.mean_diff-d.lcb95,d.ucb95-d.mean_diff]),fmt='o',color=color,capsize=3,lw=1.3);ax.axvline(0,color=GREY,lw=.7);ax.set_xlabel('Mean Macro-F1 difference')
def ni_curve(ax,d,label):
 ax.plot(d.k,d.mean_diff,'o-',ms=3,color=BLUE);ax.fill_between(d.k.to_numpy(),d.lcb95.to_numpy(),d.ucb95.to_numpy(),alpha=.18,color=BLUE);ax.axhline(-.02,ls='--',color=ORANGE,lw=1);ax.axhline(0,color=GREY,lw=.6);ax.set_xlabel('Retained selection units');ax.set_ylabel('Difference to full array');panel(ax,label)
def main():
 for sub in ('source_data','vector','preview'): (FIG/sub).mkdir(parents=True,exist_ok=True)
 # 1: verified topology; schematic coordinates are illustrative, not anatomical registration.
 meta=json.loads((ROOT/'artifacts/completion_analyses/cache_build.json').read_text());qc=read('data/features/grabmyo_extraction_qc.csv','fig1');ok=qc[qc.status=='OK'];npeople=ok.participant_id.nunique();nsessions=ok.session_id.nunique();nactive=ok.gesture_id.nunique()-1;fig,ax=plt.subplots(1,2,figsize=(7.5,3.7));a=ax[0];a.set_xlim(0,10);a.set_ylim(0,10);a.axis('off');panel(a,'A   Recording sites')
 a.add_patch(Rectangle((3.3,1.5),3.3,6.8,facecolor='#eee8df',edgecolor=GREY));a.add_patch(Ellipse((4.95,8.3),3.3,.9,facecolor='#eee8df',edgecolor=GREY));a.text(4.95,9.4,'Elbow / proximal',ha='center');a.text(4.95,.5,'Wrist / distal',ha='center')
 for yy,label in [(5.7,'F1-F8: proximal ring'),(3.4,'F9-F16: distal ring')]:a.add_patch(Ellipse((4.95,yy),3.3,.65,fill=False,edgecolor=BLUE,lw=2));a.text(6.9,yy,label,fontsize=10,va='center')
 a.annotate('',xy=(2.5,5.7),xytext=(2.5,3.4),arrowprops={'arrowstyle':'<->','color':GREY});a.text(1.7,4.55,'2 cm',rotation=90,va='center');a.text(0,1.1,'Schematic only; no muscle registration',fontsize=10)
 a=ax[1];panel(a,'B   Topology and task');a.set_xlim(-.7,7.7);a.set_ylim(-2.7,2);a.axis('off')
 for row in range(2):
  for c in range(8):a.scatter(c,1-row,s=300,color=BLUE);a.text(c,1-row,str(1+c+8*row),ha='center',va='center',color='white',fontsize=10.5)
 a.text(3.5,1.8,'Circumferential position (arbitrary origin)',ha='center');a.text(3.5,-.8,'Aligned pairs: F1/F9, ..., F8/F16',ha='center');a.text(3.5,-1.25,f'{npeople} participants | {nsessions} sessions\n{nactive} active gestures | 250 ms windows\n10 features per electrode',ha='center',va='top',fontsize=11.5,linespacing=1.5)
 pd.DataFrame({'channel':range(1,17),'ring':['proximal']*8+['distal']*8,'position':list(range(1,9))*2,'source':['Electrodelocation.pdf']*16}).to_csv(FIG/'source_data/fig1_topology.csv',index=False);save(fig,'fig1_montage')
 # 2: participant access diagram; exact historical caveats appear in the caption.
 inner=read('artifacts/rankings/cross_fitted_importance_long.csv','fig2');ninner=inner[inner.outer_participant==1].inner_fold.nunique()
 fig=plt.figure(figsize=(7.5,5.2));a=fig.add_axes([.04,.48,.92,.47]);a.axis('off');boxes=[(.01,.40,.2,.48,'Participant p\nOuter test only'),(.29,.40,.28,.48,f'Other {npeople-1} participants\n{ninner} inner grouped folds\nTraining-only scaling\nTrain inner XGBoost'),(.66,.40,.32,.48,'Inner-held-out attributions\nNormalize electrode scores\nMedian / MAD ranking')]
 for x,y,w,h,text in boxes:a.add_patch(Rectangle((x,y),w,h,facecolor='#eef6fa',edgecolor=BLUE));a.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10.5,linespacing=1.6)
 for start,end in [(.58,.65)]:a.annotate('',xy=(end,.64),xytext=(start,.64),arrowprops={'arrowstyle':'->','color':GREY})
 a.text(.5,.17,'Select top k -> retrain reduced model on outer training participants -> test only on p',ha='center',fontsize=10.5)
 a=fig.add_axes([.08,.09,.43,.28]);matrix=np.ones((ninner,ninner));np.fill_diagonal(matrix,0);a.imshow(matrix,cmap=matplotlib.colors.ListedColormap([ORANGE,BLUE]),vmin=0,vmax=1);a.set_xticks(range(ninner),range(1,ninner+1));a.set_yticks(range(ninner),range(1,ninner+1));a.set_xlabel('Inner participant group');a.set_ylabel('Attributing model');a.set_title('Orange: attribution only; blue: training',fontsize=10)
 a=fig.add_axes([.56,.12,.39,.27]);a.axis('off');a.text(0,.9,'Electrode magnitude: mean |TreeSHAP|\nFold score: normalize across electrodes\nA = median normalized magnitude\nU = median absolute deviation\nQ(lambda) = A - lambda U\n\nReport every fixed lambda; do not tune on p',fontsize=10.5,va='top',linespacing=1.6);save(fig,'fig2_crossfit')
 # 3: count decisions and individual limitations.
 curve=read('artifacts/metrics/sparse_curve_subject_metrics.csv','fig3');ni=stat('initial_primary_ni_audit.csv' if '--core-only' in sys.argv else 'noninferiority_audit.csv','fig3');individual=stat('participant_degradation.csv','fig3');fig=plt.figure(figsize=(8.1,6.0));gs=fig.add_gridspec(2,2,height_ratios=[1.1,1]);ax=[fig.add_subplot(gs[0,0]),fig.add_subplot(gs[0,1]),fig.add_subplot(gs[1,:])]
 for lam,col in zip([0,.25,.5,1],[BLUE,ORANGE,GREEN,PURPLE]):
  g=curve[curve['lambda']==lam];summary=g.groupby('channels_k').macro_f1.mean();ax[0].plot(summary.index,summary.values,label=f'lambda={lam:g}',color=col,lw=1)
 g=curve[curve['lambda']==0];bounds=[bootstrap_participant_metrics(g[g.channels_k==k].macro_f1.to_numpy(),n_resamples=10000,seed=20260728) for k in range(1,17)];ax[0].fill_between(range(1,17),np.array(bounds)[:,1],np.array(bounds)[:,2],color=BLUE,alpha=.12);ax[0].set_xticks([1,4,8,12,16]);ax[0].set_xlabel('Retained electrodes');ax[0].set_ylabel('Participant mean Macro-F1');ax[0].legend(frameon=False,fontsize=11.5);panel(ax[0],'A   Mean reduction curve')
 g=ni[(ni.condition=='primary_lambda0')&(ni.margin==.02)];ni_curve(ax[1],g,'B   Mean non-inferiority');ax[1].set_xlim(9.5,15.5);ax[1].set_ylim(-.04,.005);ax[1].set_xticks([10,11,12,13,14,15])
 d=individual.sort_values('delta_shap12');colors=np.where(d.delta_shap12<-.02,ORANGE,BLUE);ax[2].bar(range(1,len(d)+1),d.delta_shap12,color=colors,width=.8);ax[2].axhline(-.02,color=ORANGE,ls='--');ax[2].axhline(0,color=GREY,lw=.6);ax[2].set_xticks([1,10,20,30,43]);ax[2].set_xlabel('Participants ordered by change');ax[2].set_ylabel('SHAP12 minus full16');panel(ax[2],'C   Individual losses at twelve electrodes');fig.tight_layout(w_pad=2);save(fig,'fig3_noninferiority')
 if '--core-only' in sys.argv:
  pd.DataFrame(provenance).to_csv(FIG/'core_preview_provenance.csv',index=False);print('PASS: three completed primary figures generated');return
 # 4: separate comparative budgets explicitly.
 base=read('artifacts/selection_baselines/selection_baseline_metrics.csv','fig4');geo=stat('primary_selection_comparison.csv','fig4');matched=stat('matched_budget_comparisons.csv','fig4');fig=plt.figure(figsize=(8.1,6.2));gs=fig.add_gridspec(2,2,height_ratios=[1.2,1]);ax=[fig.add_subplot(gs[0,:]),fig.add_subplot(gs[1,0]),fig.add_subplot(gs[1,1])]
 for method,col in zip(['SHAP_lam0','SRCFA','PERM','MI','GEOM','RANDOM'],[BLUE,PURPLE,GREEN,'#E69F00',ORANGE,GREY]):
  g=base[base.method==method].groupby('channels_k').macro_f1.mean();ax[0].plot(g.index,g.values,'o-',ms=3,lw=1,label={'SHAP_lam0':'SHAP','SRCFA':'Penalized SHAP','PERM':'Permutation','MI':'Mutual information','GEOM':'Geometry','RANDOM':'Random'}[method],color=col)
 ax[0].set_xticks([4,6,8,12]);ax[0].set_xlabel('Retained electrodes');ax[0].set_ylabel('Mean Macro-F1');ax[0].legend(fontsize=11,frameon=False,ncol=3);panel(ax[0],'A   Lighter-model curves')
 forest(ax[1],geo);ax[1].set_yticks([]);ax[1].set_ylim(-1,1);panel(ax[1],'B   SHAP12 - geometry12');forest(ax[2],matched);ax[2].set_ylim(-.6,1.6);ax[2].set_yticks(range(2),[f'k={int(k)}' for k in matched.k]);panel(ax[2],'C   Shared inner models');ax[2].set_ylabel('SHAP - grouped permutation');fig.tight_layout(w_pad=2);save(fig,'fig4_selection_utility')
 # 5: predictive spatial importance and task-specific consequences.
 scores=read('artifacts/rankings/cross_fitted_scores.csv','fig5');gesture=stat('gesture_degradation.csv','fig5');names=read(str((REV/'reproducibility/gesture_dictionary.csv').relative_to(ROOT)),'fig5');deletion=read('artifacts/faithfulness/deletion_curves.csv','fig5');penalty=stat('extension_penalty.csv','fig5');fig=plt.figure(figsize=(8.4,10.0));gs=fig.add_gridspec(3,2,height_ratios=[.8,1.8,1.2]);a_top=fig.add_subplot(gs[0,:]);a_gesture=fig.add_subplot(gs[1,:]);a_delete=fig.add_subplot(gs[2,0]);a_penalty=fig.add_subplot(gs[2,1]);ax=np.array([[a_top,a_gesture],[a_delete,a_penalty]],dtype=object)
 a=ax[0,0];heat=scores.groupby('channel').A_central.mean().to_numpy().reshape(2,8)*100;im=a.imshow(heat,cmap='Blues');a.set_yticks([0,1],['Proximal','Distal']);a.set_xticks(range(8),range(1,9));a.set_xlabel('Circumferential position');panel(a,'A   Predictive electrode attribution')
 for i in range(2):
  for j in range(8):a.text(j,i,f'F{1+j+8*i}',ha='center',va='center',fontsize=12,color=('white' if heat[i,j]>(heat.max()+heat.min())/2 else 'black'))
 fig.colorbar(im,ax=a,fraction=.06,pad=.03,label='Magnitude (%)')
 a=ax[0,1];g=gesture.merge(names[['gesture_id','name']],on='gesture_id').sort_values('mean_diff');a.errorbar(g.mean_diff,range(16),xerr=np.vstack([g.mean_diff-g.lcb95,g.ucb95-g.mean_diff]),fmt='none',color=GREY,capsize=2);a.scatter(g.mean_diff,range(16),c=np.where(g.p_holm<.05,ORANGE,BLUE),s=18,zorder=3);a.set_yticks(range(16),[f'G{r.gesture_id}: '+r['name'].replace('Thumb and Little Finger','Thumb-little').replace('Thumb and Index Finger','Thumb-index').replace('Index and Middle Finger','Index-middle') for _,r in g.iterrows()],fontsize=12);a.axvline(0,color=GREY,lw=.7);a.set_xlabel('SHAP12 - full16 gesture F1');panel(a,'B   Which gestures lose performance?')
 a=ax[1,0]
 for arm,col in [('remove_top',ORANGE),('remove_random',GREY),('remove_bottom',BLUE)]:
  g=deletion[deletion.arm==arm].groupby('n_kept').macro_f1.mean();a.plot(g.index,g.values,'o-',color=col,label=arm.replace('_',' '),lw=1.3,ms=4)
 a.set_xticks([2,6,10,14]);a.set_xlabel('Electrodes remaining after deletion');a.set_ylabel('Mean Macro-F1 (lighter model)');a.legend(frameon=False,fontsize=11);panel(a,'C   Deletion with retraining')
 a=ax[1,1]
 for lam,col in zip([.25,.5,1],[ORANGE,GREEN,PURPLE]):
  g=penalty[penalty['lambda']==lam];a.errorbar(g.k,g.mean_diff,yerr=np.vstack([g.mean_diff-g.lcb95,g.ucb95-g.mean_diff]),fmt='o-',lw=1,color=col,label=f'lambda={lam:g}',capsize=2,ms=3)
 a.axhline(0,color=GREY,lw=.7);a.set_xticks([4,6,8,12]);a.set_xlabel('Retained electrodes');a.set_ylabel('Penalized - unpenalized F1');a.legend(frameon=False);panel(a,'D   Participant-level penalty');fig.tight_layout(w_pad=3,h_pad=3);save(fig,'fig5_task_and_attribution')
 # 6: limits, each comparison has its own full-array reference.
 ni=stat('noninferiority_audit.csv','fig6')
 fixed=read('artifacts/completion_analyses/fixed_layout/summary.csv','fig6');rf=stat('alternative_classifier_noninferiority.csv','fig6');fig,ax=plt.subplots(2,2,figsize=(8.7,6.8));g=fixed[fixed['lambda']==0];forest(ax[0,0],g);ax[0,0].set_ylim(-.8,1.8);ax[0,0].set_yticks(range(2),['Odd dev / even test','Even dev / odd test']);ax[0,0].axvline(-.02,color=ORANGE,ls='--');panel(ax[0,0],'A   Two different fixed layouts')
 g=ni[(ni.condition.isin(['primary_lambda0','rest17','w150','w500']))&(ni.margin==.02)&(ni.k==12)];g=pd.concat([g,rf[rf.margin==.02]],ignore_index=True);forest(ax[0,1],g);ax[0,1].set_yticks(range(len(g)),g.condition.replace({'primary_lambda0':'250 ms','rest17':'Rest included','w150':'150 ms','w500':'500 ms','RF_fixed_counts':'Random forest'}));ax[0,1].axvline(-.02,color=ORANGE,ls='--');panel(ax[0,1],'B   Twelve-electrode sensitivities')
 ni_curve(ax[1,0],ni[(ni.condition=='db5')&(ni.margin==.02)],'C   DB5: ten participants');ni_curve(ax[1,1],ni[(ni.condition=='bipolar')&(ni.margin==.02)],'D   Derived bipolar pairs');fig.tight_layout(h_pad=3,w_pad=3);save(fig,'fig6_generalization_limits')
 # Supplement: all sensitivity curves, gesture confusion, original classifier context.
 ni=stat('noninferiority_audit.csv','figS1')
 fig,ax=plt.subplots(1,3,figsize=(8.1,3.5))
 for a,name in zip(ax,['rest17','w150','w500']):ni_curve(a,ni[(ni.condition==name)&(ni.margin==.02)],{'rest17':'Rest included','w150':'150 ms','w500':'500 ms'}[name]);a.set_xticks([1,8,16])
 fig.tight_layout();save(fig,'figS1_sensitivity_curves')
 confusion=stat('confusion_change.csv','figS2');fig,a=plt.subplots(figsize=(6,5));matrix_pp=confusion.pivot(index='true_gesture',columns='predicted_gesture',values='delta_shap12').to_numpy()*100;limit_pp=max(float(np.ceil(abs(matrix_pp).max())),1.);im=a.imshow(matrix_pp,cmap='RdBu_r',vmin=-limit_pp,vmax=limit_pp);a.set_xticks(range(16),range(1,17));a.set_yticks(range(16),range(1,17));a.set_xlabel('Predicted gesture ID');a.set_ylabel('True gesture ID');fig.colorbar(im,ax=a,label='Mean conditional confusion change (percentage points)');panel(a,'SHAP12 minus full16, within participant');save(fig,'figS2_confusion_change')
 classifiers=read('artifacts/metrics/loso_full_channel_subject_metrics_svmrf.csv','figS3');xgb=read('artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv','figS3');fig,a=plt.subplots(figsize=(5,3.5));allc=pd.concat([classifiers,xgb]);allc['model']=allc.model.replace({'M_XGBoost':'XGBoost','M_RandomForest':'Random forest','M_SVM':'RBF-SVM'});allc.boxplot(column='macro_f1',by='model',ax=a,grid=False);fig.suptitle('');a.set_title('Full-array classifier context: different training budgets');a.set_xlabel('Classifier');a.set_ylabel('Participant Macro-F1');save(fig,'figS3_classifier_context')
 # Extended checks retain all fixed candidates and all participant observations.
 ext=read(str((REV/'experiments/attribution_extension/paired_comparisons.csv').relative_to(ROOT)),'figS4');grid=ext.pivot(index='lambda',columns='k',values='mean_diff').sort_index();fig,a=plt.subplots(figsize=(8,3.2));limit=max(abs(grid.to_numpy()).max(),1e-4);im=a.imshow(grid.to_numpy(),aspect='auto',cmap='RdBu',vmin=-limit,vmax=limit);a.set_xticks(range(len(grid.columns)),grid.columns.astype(int));a.set_yticks(range(len(grid.index)),[f'{x:g}' for x in grid.index]);a.set_xlabel('Retained electrodes');a.set_ylabel('Fixed penalty lambda');panel(a,'Participant aggregation minus fold aggregation')
 for _,r in ext[ext.p_holm<.05].iterrows():a.text(list(grid.columns).index(r.k),list(grid.index).index(r['lambda']),'*',ha='center',va='center')
 fig.colorbar(im,ax=a,label='Mean paired Macro-F1 difference');save(fig,'figS4_participant_aggregation')
 sessions=read('artifacts/cross_session/cross_session_metrics.csv','figS5');fig,a=plt.subplots(figsize=(6.8,4));columns=[];labels=[]
 for design,test in [('CS1',1),('CS1',2),('CS1',3),('CS2',3)]:
  columns.append(sessions[(sessions.design==design)&(sessions.test_session==test)].set_index('participant_id').macro_f1.sort_index());labels.append(('Train1 / test'+str(test)) if design=='CS1' else 'Train1+2 / test3')
 values=np.column_stack(columns)
 for row in values:a.plot(range(4),row,color='#aaaaaa',lw=.5,alpha=.35)
 for j,col in enumerate([BLUE,ORANGE,GREEN,PURPLE]):a.scatter(np.full(len(values),j),values[:,j],color=col,s=12,alpha=.55,zorder=3);a.plot([j-.17,j+.17],[np.median(values[:,j])]*2,color='black',lw=2,zorder=4)
 a.set_xticks(range(4),labels,fontsize=10.5);a.set_ylabel('Held-out participant Macro-F1');panel(a,'Full-array session transfer: paired participants');save(fig,'figS5_cross_session')
 people=read('artifacts/rankings/per_subject_attribution.csv','figS6');fold=read('artifacts/rankings/cross_fitted_scores.csv','figS6');person=read(str((REV/'experiments/attribution_extension/scores.csv').relative_to(ROOT)),'figS6');profile=people.groupby(['attributed_subject','channel']).importance_norm.mean().unstack('channel').sort_index();fig,ax=plt.subplots(1,2,figsize=(8.5,5.5));im=ax[0].imshow(profile.to_numpy()*100,aspect='auto',cmap='Blues');ax[0].set_xticks([0,3,7,11,15],[1,4,8,12,16]);ax[0].set_yticks([0,9,19,29,42],[1,10,20,30,43]);ax[0].set_xlabel('Electrode');ax[0].set_ylabel('Attributed participant');panel(ax[0],'A   Individual importance profiles');fig.colorbar(im,ax=ax[0],fraction=.05,pad=.02,label='Mean normalized magnitude (%)')
 x=np.arange(1,17);ax[1].bar(x-.2,fold.groupby('channel').U_instability.mean()*100,width=.4,color=BLUE,label='Five fold vectors');ax[1].bar(x+.2,person.groupby('channel').U_instability.mean()*100,width=.4,color=ORANGE,label='Individual vectors');ax[1].set_xlabel('Electrode');ax[1].set_ylabel('Mean normalized MAD (percentage points)');ax[1].set_xticks([1,4,8,12,16]);ax[1].set_ylim(0,1.28*max(fold.groupby('channel').U_instability.mean().max(),person.groupby('channel').U_instability.mean().max())*100);ax[1].legend(frameon=False);panel(ax[1],'B   Pooling changes dispersion');fig.tight_layout(w_pad=2);save(fig,'figS6_attribution_heterogeneity')
 if '--completed-preview' in sys.argv:
  pd.DataFrame(provenance).to_csv(FIG/'completed_preview_provenance.csv',index=False);print('PREVIEW: six main and six supplementary figures from complete analyses; geometric curve remains pending');return
 gni=stat('noninferiority_audit.csv','figS7');fig,ax=plt.subplots(1,2,figsize=(8,3.8))
 for name,label,color in [('primary_lambda0','Cross-fitted SHAP',BLUE),('geometric_primary','Fixed geometry',ORANGE)]:
  g=gni[(gni.condition==name)&(gni.margin==.02)];ax[0].plot(np.append(g.k.to_numpy(),16),np.append(g.mean_k.to_numpy(),g.mean_reference.iloc[0]),'o-',color=color,ms=3,label=label);ax[1].plot(g.k,g.mean_diff,'o-',color=color,ms=3,label=label);ax[1].fill_between(g.k.to_numpy(),g.lcb95.to_numpy(),g.ucb95.to_numpy(),color=color,alpha=.12)
 ax[0].set_xlabel('Retained electrodes');ax[0].set_ylabel('Participant mean Macro-F1');ax[0].set_xticks([1,4,8,12,16]);ax[0].legend(frameon=False,fontsize=10);panel(ax[0],'A   Complete reduced-count comparison');visible=gni[(gni.condition.isin(['primary_lambda0','geometric_primary']))&(gni.margin==.02)&(gni.k>=10)];vlow=min(visible.lcb95.min(),-.02);vhigh=max(visible.ucb95.max(),0);vpad=.08*(vhigh-vlow);ax[1].set_ylim(vlow-vpad,vhigh+vpad);ax[1].set_xlim(9.5,15.5);ax[1].set_xticks([10,11,12,13,14,15]);ax[1].axhline(-.02,color=GREY,ls='--');ax[1].axhline(0,color=GREY,lw=.6);ax[1].set_xlabel('Retained electrodes');ax[1].set_ylabel('Mean difference to full16');panel(ax[1],'B   Mean-preservation boundary');fig.tight_layout(w_pad=2);save(fig,'figS7_geometric_count_curve')
 pd.DataFrame(provenance).to_csv(FIG/'figure_provenance.csv',index=False);print('PASS: six main figures and seven supplementary figures generated')


if __name__=='__main__':main()
