"""Held-out metrics for one-library physical calibration; no hidden test fitting."""
import json,math,subprocess,time,statistics
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr,spearmanr
OUT=Path.cwd();BENCH=Path(__file__).parent
cases=json.loads((OUT/'cases.json').read_text());THRESHOLD=.8

def shape(c):
 n,w=c['n'],c['w']
 if c['family']=='crossbar':return n*(n-1)*w
 if c['family']=='benes':return n*(2*math.log2(n)-1)*w
 return .30*(n*4*w/20480)+.18*(n*n/100)+.06*(n*w/640)+.46*(n*(n-1)*w/2560)
coeff={}
for fam in ['crossbar','benes','router']:
 train=[c for c in cases if c['family']==fam and c['split']=='calibration' and 'synthesis_area_um2' in c]
 if len(train)==2:coeff[fam]=statistics.median(c['synthesis_area_um2']/shape(c) for c in train)
area=[]
for c in cases:
 if c['family'] not in coeff or 'synthesis_area_um2' not in c:continue
 pred=coeff[c['family']]*shape(c);actual=c['synthesis_area_um2']
 area.append({'case':c['case'],'family':c['family'],'split':c['split'],'actual_um2':actual,'predicted_um2':pred,'ape_pct':100*abs(pred-actual)/actual})

def centered(a,axis):
 b=np.zeros_like(a,dtype=float)
 if axis=='H':b[:,1:]=.5*(a[:,1:]+a[:,:-1])
 else:b[1:,:]=.5*(a[1:,:]+a[:-1,:])
 return b

def stats(pred,truth,mask):
 x=pred[mask];y=truth[mask];finite=np.isfinite(x)&np.isfinite(y);xf=x[finite];yf=y[finite]
 pear=float(pearsonr(xf,yf)[0]) if len(xf)>2 and np.std(xf)>0 and np.std(yf)>0 else None
 spear=float(spearmanr(xf,yf)[0]) if pear is not None else None
 pp=x>=THRESHOLD;tt=y>=THRESHOLD
 tp=int(np.sum(pp&tt));fp=int(np.sum(pp&~tt));fn=int(np.sum(~pp&tt));tn=int(np.sum(~pp&~tt))
 return {'pearson':pear,'spearman':spear,'hotspot_f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
 'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,
 'tp':tp,'fp':fp,'fn':fn,'tn':tn,'truth_hotspots':int(tt.sum()),'pred_hotspots':int(pp.sum()),'sites':len(x),'nonfinite_sites':int((~finite).sum()),
 'all_positive_f1':2*int(tt.sum())/(len(x)+int(tt.sum())) if len(x) else None,
 'truth_overflow':int(np.sum(y>1)),'prediction_overflow':int(np.sum(x>1))}

congestion=[]
for c in cases:
 for r in c['routes']:
  if r['status']!='ok':continue
  d=OUT/c['case'];p=json.loads((d/(r['budget']+'.physical.json')).read_text());b=json.loads((d/(r['budget']+'.resources.physical.json')).read_text())
  inputs={k:p[k] for k in ['grid_x','grid_y','die','nets']}
  ip=d/'predict-input.json';ip.write_text(json.dumps(inputs))
  t=time.perf_counter();res=subprocess.run(['node',str(BENCH/'predict.js'),str(ip)],capture_output=True,text=True,check=True)
  wall=time.perf_counter()-t;preds=json.loads(res.stdout)
  (d/(r['budget']+'.predictions.json')).write_text(json.dumps(preds))
  nx,ny=len(p['grid_x']),len(p['grid_y']);sup={k:np.zeros((ny,nx)) for k in ['H','V']};use={k:np.zeros((ny,nx)) for k in ['H','V']}
  for l,bl in zip(p['layers'],b['layers']):
   dr='H' if l['direction']=='HORIZONTAL' else 'V';cap=np.array(l['capacity'],float);bu=np.array(bl['usage'],float);u=np.array(l['usage'],float)
   assert np.max(cap)<=255 and np.min(u-bu)>=0 and np.min(cap-bu)>=0
   sup[dr]+=cap-bu;use[dr]+=u-bu
  for axis in ['H','V']:sup[axis]=centered(sup[axis],axis);use[axis]=centered(use[axis],axis)
  mask=np.ones((ny,nx),bool);mask[[0,-1],:]=False;mask[:,[0,-1]]=False
  zero_supply=int(np.sum(mask&((sup['H']<=0)|(sup['V']<=0))))
  mask&=(sup['H']>0)&(sup['V']>0)
  truth=np.maximum(np.divide(use['H'],sup['H'],out=np.zeros_like(use['H']),where=sup['H']>0),np.divide(use['V'],sup['V'],out=np.zeros_like(use['V']),where=sup['V']>0))
  fields={'truth':truth.tolist(),'mask':mask.tolist(),'supply_H':sup['H'].tolist(),'supply_V':sup['V'].tolist()}
  for method,data in preds.items():
   if not isinstance(data,dict):continue
   ph=np.array(data['H']);pv=np.array(data['V'])
   if method=='mst_union_edge':ph=centered(ph,'H');pv=centered(pv,'V')
   pred=np.maximum(np.divide(ph,sup['H'],out=np.zeros_like(ph),where=sup['H']>0),np.divide(pv,sup['V'],out=np.zeros_like(pv),where=sup['V']>0))
   fields[method]=pred.tolist();s=stats(pred,truth,mask);active=mask&((use['H']+use['V']+ph+pv)>0)
   s.update({'case':c['case'],'family':c['family'],'split':c['split'],'budget':r['budget'],'method':method,'kernel_ms':data['kernel_ms'],'node_io_wall_s_both_methods':wall,'global_route_s':r['global_route_s'],'active_pearson':stats(pred,truth,active)['pearson'],'zero_supply_excluded':zero_supply})
   congestion.append(s)
  (d/(r['budget']+'.fields.json')).write_text(json.dumps(fields))

def avg(rows,key):
 vals=[r[key] for r in rows if r.get(key) is not None];return statistics.mean(vals) if vals else None
summary={'status':'pilot-library-specific-not-signoff','calibration_coefficients':coeff,'area':{},'congestion':{},'counts':{'requested_cases':len(cases),'successful_cases':sum(c['status']=='ok' for c in cases),'successful_routes':sum(r['status']=='ok' for c in cases for r in c['routes'])},'protocol':'v6 shape + per-family scalar fit only on 4x8/8x8; held-out widths/radices; post-placement pin adapter; native resources stripped of reserved occupancy; hotspot threshold >=0.8; interior GCells, same mask for both predictors'}
for fam in ['crossbar','benes','router','all']:
 tests=[r for r in area if r['split']=='test' and (fam=='all' or r['family']==fam)]
 summary['area'][fam]={'n':len(tests),'mape_pct':avg(tests,'ape_pct'),'max_ape_pct':max((r['ape_pct'] for r in tests),default=None)}
for method in ['legacy_star_tile','mst_union_edge']:
 for budget in ['nominal','constrained','all']:
  tests=[r for r in congestion if r['split']=='test' and r['method']==method and (budget=='all' or r['budget']==budget)];pos=[r for r in tests if r['truth_hotspots']>0]
  tp=sum(r['tp'] for r in tests);fp=sum(r['fp'] for r in tests);fn=sum(r['fn'] for r in tests)
  summary['congestion'][method+'/'+budget]={'n':len(tests),'pearson_macro':avg(tests,'pearson'),'spearman_macro':avg(tests,'spearman'),'active_pearson_macro':avg(tests,'active_pearson'),'hotspot_f1_macro_positive_cases':avg(pos,'hotspot_f1'),'positive_cases':len(pos),'hotspot_f1_micro':2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else None,'all_positive_f1_macro':avg(tests,'all_positive_f1'),'median_kernel_ms':statistics.median(r['kernel_ms'] for r in tests) if tests else None}
summary['runtime']={k:{'median_s':statistics.median(c[k] for c in cases if k in c),'sum_s':sum(c.get(k,0) for c in cases)} for k in ['synthesis_s','placement_s']}
rt=[r for c in cases for r in c['routes'] if r['status']=='ok'];summary['runtime']['global_route']={'median_s':statistics.median(r['global_route_s'] for r in rt) if rt else None,'sum_s':sum(r['global_route_s'] for r in rt)}
for name,value in [('area_metrics.json',area),('congestion_metrics.json',congestion),('summary.json',summary)]:
 (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False))
print(json.dumps(summary,indent=2,allow_nan=False))
