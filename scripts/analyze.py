"""Cookie Cats experiment: ITT retention effects, CIs, SRM, and launch decision."""
import argparse
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, chisquare, mannwhitneyu
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from dashboard_utils import dashboard
BASE=Path(__file__).resolve().parents[1]

def validate(data):
    required={'userid','version','sum_gamerounds','retention_1','retention_7'}
    if not required.issubset(data):raise ValueError('Missing columns: '+str(required-set(data)))
    d=data.copy()
    if d.userid.isna().any() or d.userid.duplicated().any():raise ValueError('One row per unique userid required')
    if set(d.version.dropna().unique())!={'gate_30','gate_40'} or d.version.isna().any():
        raise ValueError('Expected both gate_30 and gate_40 with no missing assignments')
    d['sum_gamerounds']=pd.to_numeric(d.sum_gamerounds,errors='coerce')
    if d.sum_gamerounds.isna().any() or (d.sum_gamerounds<0).any():raise ValueError('Game rounds must be nonnegative numbers')
    for c in ('retention_1','retention_7'):
        d[c]=d[c].astype(str).str.lower().map({'true':1,'false':0,'1':1,'0':0})
        if d[c].isna().any():raise ValueError(f'Invalid binary retention values in {c}')
        d[c]=d[c].astype(int)
    return d

def z_test(control_success,control_n,treatment_success,treatment_n):
    """Two-sided pooled two-proportion z-test and unpooled 95% Wald CI for treatment-control."""
    p0=control_success/control_n;p1=treatment_success/treatment_n
    pooled=(control_success+treatment_success)/(control_n+treatment_n)
    se_null=np.sqrt(pooled*(1-pooled)*(1/control_n+1/treatment_n))
    pvalue=float(2*norm.sf(abs((p1-p0)/se_null))) if se_null>0 else 1.
    se_ci=np.sqrt(p0*(1-p0)/control_n+p1*(1-p1)/treatment_n)
    z=norm.ppf(.975)
    return {'control_rate':float(p0),'treatment_rate':float(p1),
            'difference_pp':float((p1-p0)*100),'p_value':pvalue,
            'ci_low_pp':float(100*(p1-p0-z*se_ci)),
            'ci_high_pp':float(100*(p1-p0+z*se_ci))}

def analyze(data):
    d=validate(data)
    groups={name:d[d.version==name] for name in ['gate_30','gate_40']}
    n0=len(groups['gate_30']);n1=len(groups['gate_40'])
    srm_p=float(chisquare([n0,n1],f_exp=[(n0+n1)/2]*2).pvalue)
    results={}
    for col,name in [('retention_1','day_1'),('retention_7','day_7')]:
        r=z_test(int(groups['gate_30'][col].sum()),n0,int(groups['gate_40'][col].sum()),n1)
        results[name]=r
    medians={g:float(df.sum_gamerounds.median()) for g,df in groups.items()}
    results['engagement']={'median_rounds':medians,'mean_rounds':{g:float(df.sum_gamerounds.mean()) for g,df in groups.items()},
         'mann_whitney_p_value':float(mannwhitneyu(groups['gate_30'].sum_gamerounds,groups['gate_40'].sum_gamerounds,alternative='two-sided').pvalue)}
    significant=results['day_7']['p_value']<.05
    if srm_p<.01: decision='INVESTIGATE ASSIGNMENT QUALITY — sample ratio mismatch detected; do not launch based on this analysis.'
    elif significant and results['day_7']['difference_pp']<0:decision='KEEP GATE AT LEVEL 30 — treatment significantly reduces 7-day retention.'
    elif significant and results['day_7']['difference_pp']>0:decision='CONSIDER GATE AT LEVEL 40 — positive primary effect; first review missing business guardrails.'
    else:decision='NO CONCLUSIVE 7-DAY LIFT — do not roll out the treatment based on these data alone.'
    return {'users':n0+n1,'group_sizes':{'gate_30':n0,'gate_40':n1},
            'sample_ratio_mismatch_p_value':srm_p,'day_1':results['day_1'],'day_7':results['day_7'],
            'engagement':results['engagement'],'decision':decision}

def run(data_path=None,output_dir=None):
    source=Path(data_path or BASE/'data/raw/cookie_cats.csv')
    out=Path(output_dir or BASE/'outputs');out.mkdir(parents=True,exist_ok=True)
    d=validate(pd.read_csv(source))
    summary=analyze(d)
    summary['source_filename']=source.name
    summary['demo_data']=bool(source.resolve()==(BASE/'data/raw/cookie_cats.csv').resolve() and (BASE/'data/raw/DEMO_DATA.txt').exists())
    with sqlite3.connect(':memory:') as con:
        d.to_sql('experiment',con,index=False)
        sql=(BASE/'sql/experiment_summary.sql').read_text()
        sql_summary=pd.read_sql_query(sql,con)
    sql_summary.to_csv(out/'experiment_summary.csv',index=False)
    (out/'metrics.json').write_text(json.dumps(summary,indent=2))

    x=['Day 1','Day 7'];c=[summary['day_1']['control_rate']*100,summary['day_7']['control_rate']*100]
    t=[summary['day_1']['treatment_rate']*100,summary['day_7']['treatment_rate']*100]
    fig1=go.Figure()
    fig1.add_trace(go.Bar(x=x,y=c,name='Gate at level 30 (control)',marker_color='#40cdb8',text=[f'{v:.2f}%' for v in c],textposition='outside'))
    fig1.add_trace(go.Bar(x=x,y=t,name='Gate at level 40 (treatment)',marker_color='#7997ee',text=[f'{v:.2f}%' for v in t],textposition='outside'))
    fig1.update_layout(barmode='group');fig1.update_yaxes(title='Retention (%)',range=[0,max(c+t)*1.25])
    fig2=go.Figure()
    for row,label in [('day_1','Day-1 retention'),('day_7','Day-7 retention (primary)')]:
        r=summary[row];delta=r['difference_pp']
        fig2.add_trace(go.Scatter(x=[delta],y=[label],mode='markers',showlegend=False,marker=dict(size=15,color='#40cdb8'),
          error_x=dict(type='data',symmetric=False,array=[r['ci_high_pp']-delta],arrayminus=[delta-r['ci_low_pp']]),
          hovertemplate=f'{label}: {delta:+.2f} percentage points<extra></extra>'))
    fig2.add_vline(x=0,line_dash='dash',line_color='#ffbd70');fig2.update_xaxes(title='Treatment − control (percentage points)')
    fig3=go.Figure(go.Bar(x=['Gate at 30','Gate at 40'],
            y=[summary['engagement']['median_rounds']['gate_30'],summary['engagement']['median_rounds']['gate_40']],
            marker_color=['#40cdb8','#7997ee']))
    fig3.update_yaxes(title='Median game rounds (14 days)')
    d7=summary['day_7'];srm=summary['sample_ratio_mismatch_p_value']
    finding=(f"<b>{summary['decision']}</b> Day-7 difference: <b>{d7['difference_pp']:+.2f} percentage points</b> "
             f"(95% CI {d7['ci_low_pp']:+.2f} to {d7['ci_high_pp']:+.2f}; p={d7['p_value']:.4f}).")
    note=('DATA: SYNTHETIC DEMO — NOT THE ACTUAL COOKIE CATS EXPERIMENT. ' if summary['demo_data'] else 'DATA: USER-SUPPLIED COOKIE CATS EXPERIMENT. ')+(
           'Analysis is intent-to-treat. Primary metric: Day-7 retention, two-sided α=0.05. '
           'Sample ratio mismatch alert threshold: p<0.01. 95% confidence intervals use normal approximation. '
           'Revenue, purchases and uninstall rates unavailable; keep those as launch guardrails.')
    dashboard(out/'dashboard.html','A/B Testing · Cookie Cats Gate Placement',
         'Should players encounter the first progression gate at level 30 or level 40?',
         [('Players',f"{summary['users']:,}"),('Day-7: control',f"{d7['control_rate']:.2%}"),
          ('Day-7: treatment',f"{d7['treatment_rate']:.2%}"),('Day-7 p-value',f"{d7['p_value']:.4f}")],
         [('Retention by treatment',fig1),('Treatment effect · 95% CI',fig2),('Typical engagement',fig3)],finding,note)
    fig,ax=plt.subplots(figsize=(9.6,5.6));fig.patch.set_facecolor('#0b1324');ax.set_facecolor('#17223a')
    xx=np.arange(2);w=.33
    ax.bar(xx-w/2,c,w,color='#40cdb8',label='Control · gate 30')
    ax.bar(xx+w/2,t,w,color='#7997ee',label='Treatment · gate 40')
    ax.set_xticks(xx,x);ax.set_ylim(0,max(c+t)*1.2);ax.tick_params(colors='white')
    ax.spines[:].set_visible(False);ax.set_ylabel('Retention (%)',color='white')
    ax.set_title('A/B EXPERIMENT — PLAYER RETENTION',color='white',weight='bold',fontsize=16,pad=20)
    leg=ax.legend(facecolor='#17223a',labelcolor='white',loc='upper right');fig.tight_layout()
    fig.savefig(out/'overview.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
    (out/'insights.md').write_text(f'''# Product decision memo — A/B Test

**Dataset:** {'Synthetic demonstration data (not actual Cookie Cats players)' if summary['demo_data'] else source.name}

**Hypothesis:** Moving the first gate from level 30 (control) to level 40 (treatment) affects Day-7 retention.

## Experiment quality

- Unique players: **{summary['users']:,}** ({summary['group_sizes']['gate_30']:,} control / {summary['group_sizes']['gate_40']:,} treatment).
- Sample ratio mismatch chi-squared p-value: **{srm:.4g}**; flag under 0.01 for assignment review.
- Unit of randomization / analysis: player ID, one row per player. This is a retrospective analysis; original randomization was not audited.

## Outcomes

| Metric | Control | Treatment | Treatment - Control | p-value | 95% CI (pp) |
|---|---:|---:|---:|---:|---:|
| Day 1 (secondary) | {summary['day_1']['control_rate']:.2%} | {summary['day_1']['treatment_rate']:.2%} | {summary['day_1']['difference_pp']:+.2f} pp | {summary['day_1']['p_value']:.4f} | [{summary['day_1']['ci_low_pp']:+.2f}, {summary['day_1']['ci_high_pp']:+.2f}] |
| Day 7 (**primary**) | {d7['control_rate']:.2%} | {d7['treatment_rate']:.2%} | {d7['difference_pp']:+.2f} pp | {d7['p_value']:.4f} | [{d7['ci_low_pp']:+.2f}, {d7['ci_high_pp']:+.2f}] |

Median 14-day game rounds: **{summary['engagement']['median_rounds']['gate_30']:.0f}** control vs **{summary['engagement']['median_rounds']['gate_40']:.0f}** treatment. Medians are used because extreme engagement outliers may exist; no users are removed from the retention ITT analysis.

## Decision

**{summary['decision']}**

## Statistical design and limitations

- Two-sided **pooled two-proportion z-tests**; report the unpooled normal-approximation 95% confidence interval for the difference in absolute percentages.
- Alpha 0.05 is applied to **Day-7 primary outcome**. Treat Day-1 as exploratory / secondary rather than making a separate launch claim.
- Sample ratio mismatch uses chi-squared goodness-of-fit against 50:50 allocation; mismatch can suggest a logging or randomization issue.
- Revenue, pay conversion, uninstall rate and user-level exposure to the gate are not available. These are important missing guardrails.
- ITT = effect of **assignment** to gate configuration, not effect among only users who reached the gate.
- Synthetic demo estimates are not evidence from a real company experiment.
''')
    print(f"A/B: N={summary['users']:,}, day-7 delta={d7['difference_pp']:+.2f}pp, p={d7['p_value']:.4f}. Dashboard: {out/'dashboard.html'}")
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--data');ap.add_argument('--out')
    args=ap.parse_args();run(args.data,args.out)
