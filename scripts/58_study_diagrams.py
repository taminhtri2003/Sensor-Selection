"""Vector study overview: documented topology, no inferred muscle assignments."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent


def main():
    columns=json.loads((ROOT/'data/cache/loso_features.json').read_text())
    n=len({c.split('_')[0] for c in columns})
    if n != 16:
        raise ValueError('diagram requires the documented GRABMyo montage')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),gridspec_kw={'width_ratios':[1.2,1]})
    navy='#25445e'; teal='#087e8b'; pale='#eef5f7'
    a,b=axes
    for ax in axes:
        ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    a.text(0, .98,'A  Electrode topology',weight='bold',color=navy,va='top',fontsize=10)
    a.text(0,.86,'Two rings shown unwrapped; ends join circumferentially.',fontsize=7)
    for ring,y in enumerate((.64,.37)):
        a.plot([.07,.95],[y,y],color='#b8c9d2',lw=1,zorder=0)
        for position in range(8):
            x=.09+.12*position
            a.add_patch(Circle((x,y),.043,fc=pale,ec=teal,lw=1))
            a.text(x,y,f'F{ring*8+position+1}',ha='center',va='center',fontsize=7)
            if ring==0:
                a.plot([x,x],[.42,.59],color='#b8c9d2',lw=.8,ls=':')
    a.text(.5,.09,r'Derived bipolar pair: $B_j=F_j-F_{j+8}$',ha='center',color=navy)
    b.text(0,.98,'B  Cross-fitted aggregation',weight='bold',color=navy,va='top',fontsize=10)
    items=[(.69,'Original: pool people within each inner fold\nMedian and MAD across fold vectors'),
           (.32,'Extension: normalise each held-out person\nMedian and MAD across person vectors')]
    for y,label in items:
        b.add_patch(FancyBboxPatch((.02,y-.12),.95,.24,boxstyle='round,pad=0.015',fc=pale,ec='#b8c9d2'))
        b.text(.49,y,label,ha='center',va='center',linespacing=1.6,fontsize=8)
    b.text(.5,.06,r'Both rank by $Q_c(\lambda)=A_c-\lambda U_c$',ha='center',color=navy)
    fig.subplots_adjust(left=.03,right=.99,top=.96,bottom=.05,wspace=.13)
    out=ROOT/'manuscript/figures/source/fig1_schematic_alternative'  # not used: Figure 1 is the authors' figure (figures/source/make_fig1_overview.py)
    fig.savefig(out.with_suffix('.pdf'),bbox_inches='tight')
    fig.savefig(out.with_suffix('.png'),dpi=200,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    main()
