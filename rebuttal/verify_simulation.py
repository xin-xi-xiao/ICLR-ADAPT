#!/usr/bin/env python3
"""Recalculate measurements from the extracted evidence directory or its original ZIP.
Usage: python verify_simulation.py . --output /tmp/evidence-verification
Requires Python 3 and NumPy. No project imports, simulator, netlist, or network.
This verifies numerical consistency and recorded probes, not circuit signoff.
The optional fourth PT waveform is not needed for the 84/56 tables: those
compare new-layout unit_collapse, RC, RCC only; it is reported separately.
"""
import argparse, collections, csv, io, json, math, re, zipfile
from pathlib import Path, PurePosixPath
import numpy as np
CASES=['CLK-CMP','CT-CMP','DC-Switch','PT-CMP','REF-BUF']
CONDS=['unit_collapse','RC','RCC']
WORDS=['00000000','10000000','11111111','11101111','11001100','11000100','00111100','00111110']

class DirectoryEvidence:
    """Read-only adapter; preserves the numerical verifier unchanged."""
    def __init__(self, path):
        self.root = Path(path).resolve()
        if not (self.root / 'Evidence').is_dir():
            raise ValueError('Expected a directory containing Evidence/')
    def namelist(self):
        return sorted(p.relative_to(self.root).as_posix()
                      for p in (self.root / 'Evidence').rglob('*') if p.is_file())
    def read(self, name):
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe evidence path')
        target = self.root.joinpath(*relative.parts).resolve()
        if not target.is_relative_to(self.root / 'Evidence'):
            raise ValueError('Evidence path escapes archive root')
        return target.read_bytes()


def psf(text):
    data=collections.defaultdict(list)
    for k,v in re.findall(r'^"([^\"]+)"\s+([-+0-9.eE]+)$',text.split('\nVALUE\n',1)[1],re.M): data[k].append(float(v))
    return {k:np.asarray(v) for k,v in data.items()}

def crossing(t,v,level,direction,start,stop):
    mask=(t[:-1]>=start)&(t[1:]<=stop)
    mask &= ((v[:-1]<level)&(v[1:]>=level)) if direction>0 else ((v[:-1]>level)&(v[1:]<=level))
    ids=np.flatnonzero(mask)
    if not len(ids): return None
    i=ids[0]
    return float(t[i]+(level-v[i])*(t[i+1]-t[i])/(v[i+1]-v[i]))

def settled(t,v,start,end): return float(np.mean(v[(t>=start*1e-9)&(t<end*1e-9)]))
def settling(t,v,edge,stop,initial,final):
    m=(t>=edge*1e-9)&(t<=stop*1e-9);tt=t[m];bad=np.flatnonzero(abs(v[m]-final)>abs(final-initial)*.01)
    if not len(bad):return 0.
    return None if bad[-1]+1==len(tt) else float((tt[bad[-1]+1]-edge*1e-9)*1e9)
def close(a,b): return a is None and b is None or a is not None and b is not None and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
def scalar(s): return None if s=='' else float(s)
def writecsv(path,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

def calculate(case,a,dc=None):
    t=a['time'];trap=getattr(np,'trapezoid',np.trapz)
    metrics={'VSUP_mean_current_mA':-1e3*float(trap(a['VSUP:p'],t)/(t[-1]-t[0]))}
    metrics['VSUP_mean_power_mW']=.8*metrics['VSUP_mean_current_mA'];checks=[]
    sample=lambda v,ns:float(np.interp(ns*1e-9,t,v))
    if case=='CLK-CMP':
        delays=[]
        for ns,expected in zip([9,19,29,39,49,59],[1,1,0,0,1,1]):
            x=sample(a['out'],ns);y=sample(a['outb'],ns)
            checks.append(x>=.64 and y<=.16 if expected else x<=.16 and y>=.64)
            edge=(ns-3.95)*1e-9;m=(t>=edge)&(t<(ns+.5)*1e-9)
            good=(a['out']>=.64)&(a['outb']<=.16) if expected else (a['out']<=.16)&(a['outb']>=.64)
            tt=t[m];bad=np.flatnonzero(~good[m]);k=bad[-1]+1 if len(bad)else 0
            delays.append(float((tt[k]-edge)*1e12)if k<len(tt)else None)
        metrics['decision_mean_ps']=float(np.mean(delays))if all(x is not None for x in delays)else None
    elif case=='CT-CMP':
        lo=settled(t,a['out'],18,24);hi=settled(t,a['out'],8,14)
        metrics.update(output_low_V=lo,output_high_V=hi);checks=[lo<.16 and hi>.64]
        for name,direction,start,stop in [('rise',1,4,10),('fall',-1,14,20)]:
            ti=crossing(t,a['vip']-a['vim'],0,direction,start*1e-9,stop*1e-9);to=crossing(t,a['out'],.4,direction,start*1e-9,stop*1e-9)
            metrics[name+'_signed_lag_ps']=(to-ti)*1e12 if ti is not None and to is not None else None
        key=next(k for k in dc if k not in ['out','vip','vim','VSUP:p']);trip=crossing(dc[key],dc['out'],.4,1,-.05,.05)
        metrics['DC_trip_mV']=trip*1000 if trip is not None else None
    elif case=='DC-Switch':
        errors=[]
        for ns,targets in [(39,[.8,.4,.4,0]),(44,[.4,.8,0,.4]),(49,[.8,.4,.4,0]),(54,[.4,.8,0,.4]),(59,[.8,.4,.4,0])]:
            for node,target in zip(['y0t','y1t','y0b','y1b'],targets):
                err=abs(sample(a[node],ns)-target);errors.append(err*1000);checks.append(err<.1)
        metrics['rail_max_error_mV']=max(errors)
        metrics['upper_overshoot_mV']=1e3*max(float(a['y0t'].max())-.8,float(a['y1t'].max())-.8,float(a['y0b'].max())-.4,float(a['y1b'].max())-.4)
        for rail,voltage in [('VHIGH',.8),('VMID',.4)]:metrics[rail+'_mean_power_uW']=-1e6*voltage*float(trap(a[rail+':p'],t)/(t[-1]-t[0]))
    elif case=='PT-CMP':
        delays={'rise':[],'fall':[]}
        for i,w in enumerate(WORDS):
            expected=int(all(w[k]==w[k+1]for k in range(0,8,2)));v=sample(a['out'],i*10+9);checks.append(v>=.64 if expected else v<=.16)
            if i:
                edge=i*10e-9+50e-12;to=crossing(t,a['out'],.4,1 if expected else-1,i*10e-9,(i*10+9)*1e-9)
                delays['rise' if expected else 'fall'].append((to-edge)*1e12 if to is not None else None)
        for k,vals in delays.items():metrics[k+'_mean_signed_lag_ps']=float(np.mean(vals))if all(x is not None for x in vals)else None
    elif case=='REF-BUF':
        lo=settled(t,a['out'],150,190);hi=settled(t,a['out'],350,390);checks=[hi>lo]
        metrics.update(step_gain=(hi-lo)/.02,settling_rise_ns=settling(t,a['out'],200,399,lo,hi),settling_fall_ns=settling(t,a['out'],400,599,hi,lo))
        vv=dc['vin'];assert len(vv)==2*len(dc['out']) and np.allclose(vv[::2],vv[1::2],rtol=0,atol=1e-14)
        vv=vv[::2];err=dc['out']-vv
        metrics.update(DC_max_error_mV=float(max(abs(err)))*1000,DC_mean_error_mV=float(np.mean(abs(err)))*1000,DC_secant_gain=float((dc['out'][-1]-dc['out'][0])/(vv[-1]-vv[0])))
    return metrics,checks

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input', help='Directory containing Evidence/, or original ZIP');ap.add_argument('--output',default='simulation_verification');args=ap.parse_args()
    input_path=Path(args.input);out=Path(args.output)
    if input_path.is_dir() and out.resolve().is_relative_to((input_path/'Evidence').resolve()):
        raise ValueError('Verification output must be outside Evidence/')
    out.mkdir(parents=True,exist_ok=False)
    z=DirectoryEvidence(input_path) if input_path.is_dir() else zipfile.ZipFile(input_path)
    root=next(n[:-len('Simulation/CLK-CMP/metrics.csv')]for n in z.namelist()if n.endswith('Simulation/CLK-CMP/metrics.csv'))
    text=lambda n:z.read(root+n).decode('utf-8')
    table=lambda n:list(csv.DictReader(io.StringIO(text(n))))
    metricrows=[];comparisons=[];runrows=[];logs=[];observations=[];margins=[];failures=[];values={}
    for case in CASES:
        expectedmetric=table('Simulation/'+case+'/metrics.csv');expectedchecks=table('Simulation/'+case+'/functional_observations.csv')
        for cond in CONDS:
            base='Simulation/'+case+'/'+cond+'/';a=psf(text(base+'transient.txt'));t=a['time'];dc=psf(text(base+'dc_sweep.txt'))if case in ['CT-CMP','REF-BUF']else None
            m,c=calculate(case,a,dc);values[(case,cond)]=m
            end=600e-9 if case=='REF-BUF'else 80e-9 if case=='PT-CMP'else 60e-9
            complete=abs(t[-1]-end)<1e-12 and all(np.isfinite(v).all()for v in a.values())
            receipt=json.loads(text(base+'execution_summary.json'))
            runrows.append(dict(case=case,condition=cond,transient_samples=len(t),last_time_ns=t[-1]*1e9,expected_end_ns=end*1e9,finite_and_full_duration=complete,receipt_returncode=receipt.get('returncode'),recorded_functional_probes_pass=int(sum(c)),recorded_functional_probes_total=len(c),scope='positive_response_only_not_precision_spec'if case=='REF-BUF'else'fixed_selected_probes_not_all_specification'))
            if not complete or receipt.get('returncode')!=0:failures.append(base+'completion')
            expected=[r for r in expectedchecks if r['condition']==cond]
            for i,(check,r)in enumerate(zip(c,expected),1):
                ok=bool(check)==(r['pass'].lower()=='true');observations.append(dict(case=case,condition=cond,check_index=i,recomputed_pass=bool(check),recorded_pass=r['pass'],consistent=ok))
                if not ok:failures.append(base+'probe'+str(i))
            if len(c)!=len(expected):failures.append(base+'probe_count')
            for r in expectedmetric:
                if r['condition']!=cond:continue
                v=m[r['metric']];e=scalar(r['value']);ok=close(v,e)
                metricrows.append(dict(case=case,condition=cond,metric=r['metric'],recorded_value=e,recomputed_value=v,absolute_difference=None if e is None or v is None else abs(v-e),consistent=ok))
                if not ok:failures.append(base+r['metric'])
        for r in table('Simulation/'+case+'/pre_post_comparison.csv'):
            pre=values[(case,'unit_collapse')][r['metric']];post=values[(case,r['condition'])][r['metric']]
            delta=None if pre is None or post is None else post-pre;pct=None if delta is None or pre==0 else 100*delta/abs(pre)
            ok=all(close(v,scalar(r[k]))for k,v in [('pre_value',pre),('post_value',post),('signed_change',delta),('signed_change_percent',pct)])
            comparisons.append(dict(case=case,condition=r['condition'],metric=r['metric'],pre_value=pre,post_value=post,signed_change=delta,signed_change_percent=pct,consistent=ok))
            if not ok:failures.append(case+'/'+r['condition']+'/'+r['metric']+'/change')
    optional_prior=[]
    prior_name=root+'Simulation/PT-CMP/prior_sizing_control/transient.txt'
    if prior_name in z.namelist():
        a=psf(z.read(prior_name).decode());m,c=calculate('PT-CMP',a)
        complete=abs(a['time'][-1]-80e-9)<1e-12 and all(np.isfinite(v).all()for v in a.values())
        for k,v in m.items():optional_prior.append(dict(case='PT-CMP',condition='prior_sizing_control',metric=k,recomputed_value=v,finite_and_full_duration=complete,functional_probes_pass=int(sum(c)),functional_probes_total=len(c),scope='53-MOS sizing control; not original long-L source; not part of 84/56 tables'))
        if not complete:failures.append(prior_name+'/completion')
        writecsv(out/'PT_prior_sizing_control_recomputed.csv',optional_prior)
    for n in z.namelist():
        if not n.startswith(root+'Simulation/') or not n.endswith('/spectre.log'):continue
        raw=z.read(n).decode();matches=list(re.finditer(r'spectre completes with (\d+) errors, (\d+) warnings, and (\d+) notices?',raw));m=matches[-1]if matches else None
        row=dict(file=n,errors=int(m[1])if m else None,warnings=int(m[2])if m else None,notices=int(m[3])if m else None,completion_line=raw[:m.start()].count('\n')+1 if m else None,trapezoidal_ringing_occurrences=raw.count('Found trapezoidal ringing'));logs.append(row)
        if not m or row['errors']!=0:failures.append(n+'/native_log')
    for r in table('Simulation/REF-BUF/Stability/margins.csv'):
        raw=text('Simulation/REF-BUF/Stability/'+r['condition']+'/loop_margins.txt')
        for k in ['gainMargin','gainMarginFrequency','phaseMargin','phaseMarginFrequency']:
            match=re.search(r'^"'+k+r'" "([-+0-9.eE]+) ',raw,re.M);v=float(match[1])if match else None;e=float(r[k]);ok=close(v,e)
            margins.append(dict(condition=r['condition'],metric=k,recorded_value=e,native_header_value=v,consistent=ok))
            if not ok:failures.append('REF-BUF/STB/'+r['condition']+'/'+k)
    for name,rows in [('all_metrics84.csv',metricrows),('all_changes56.csv',comparisons),('run_completion15.csv',runrows),('native_log_completion.csv',logs),('functional_probe_recheck.csv',observations),('local_stability_header_recheck.csv',margins)]:writecsv(out/name,rows)
    summary={'scope':'Numerical recheck of the five-design research-model package; not foundry signoff or all-specification equivalence.','metric_count':len(metricrows),'change_count':len(comparisons),'transient_runs':len(runrows),'native_logs':len(logs),'functional_probe_count':len(observations),'stability_header_values':len(margins),'failures':failures,'consistent':not failures,'PT_extra_source_curve_in_84_56_tables':False,'PT_prior_sizing_control_raw_present':bool(optional_prior),'PT_prior_sizing_control_metrics_recomputed':len(optional_prior),'REF_raw_DC_required_and_present':True,'precision_tolerance':{'relative':1e-10,'absolute':1e-10},'all_waveforms_complete':all(r['finite_and_full_duration']for r in runrows),'all_native_logs_zero_errors':all(r['errors']==0 for r in logs),'full_precision_or_all_design_specs_pass':None}
    (out/'verification_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
    raise SystemExit(0 if not failures else 1)
if __name__=='__main__':main()
