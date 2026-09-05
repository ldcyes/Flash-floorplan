#!/usr/bin/env python3
"""Real EDA pilot, not mocked. Every command/log and failure is retained."""
import os,json,re,time,subprocess,hashlib,math,traceback
from pathlib import Path
from rtl import fabric,router,testbench,benes_reference
ROOT=Path.cwd(); OUT=ROOT/'benchmark-results';OUT.mkdir(exist_ok=True)
PLAT=ROOT/'platform';LIB=PLAT/'NangateOpenCellLibrary_typical.lib'
TECH=PLAT/'NangateOpenCellLibrary.tech.lef';MACRO=PLAT/'NangateOpenCellLibrary.macro.mod.lef'
cell_area={m.group(1):float(m.group(2)) for m in re.finditer(r'cell\s*\(\s*(\w+)\s*\).*?area\s*:\s*([\d.eE+-]+)',LIB.read_text(),re.S)}
assert len(cell_area)>50
MODE=os.environ.get('BENCH_MODE','smoke')
CONFIGS=[(4,8)] if MODE=='smoke' else [(4,8),(8,8),(4,16),(8,16),(16,8),(16,16)]
BUDGETS=[('nominal','metal2-metal6',.30),('constrained','metal2-metal4',.80)]
plan={'suite_version':2,'mode':MODE,'families':['crossbar','benes','router'],'configs':CONFIGS,'calibration':[[4,8],[8,8]],'routing_budgets':BUDGETS,'threads':1,'clock_period_ns':5,'timing_scope':'pre-CTS; no signoff timing or power','area_scope':'mapped standard-cell area, not die area','hotspot_threshold':.8,'reference':'Nangate45 typical; not foundry silicon','resource_baseline':'incremental start/end without dirty nets; no routed signals; subtract baseline occupancy from capacity and routed usage'}
(OUT/'protocol.json').write_text(json.dumps(plan,indent=2))

def run(cmd,cwd,log,timeout=300,env=None):
    start=time.perf_counter()
    with open(cwd/log,'w') as f:
        f.write('COMMAND '+repr(cmd)+'\n');f.flush()
        result=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
    elapsed=time.perf_counter()-start
    if result.returncode:
        print((cwd/log).read_text()[-5500:],flush=True)
        raise RuntimeError(f'{log}: exit {result.returncode}')
    return elapsed

def extract(d,stem):
    env={**os.environ,'INPUT_DB':str(d/f'{stem}.odb'),'OUTPUT_JSON':str(d/f'{stem}.physical.json')}
    elapsed=run(['openroad','-python','-exit',str(ROOT/'benchmarks/extract.py')],d,f'{stem}.extract.log',env=env)
    return json.loads((d/f'{stem}.physical.json').read_text()),elapsed

perms={tuple(benes_reference(list(range(4)),[(x>>i)&1 for i in range(6)])) for x in range(64)}
assert len(perms)==24
rows=[]
for kind in plan['families']:
 for n,w in CONFIGS:
    name=f'{kind}_n{n}_w{w}';d=OUT/name;d.mkdir(exist_ok=True)
    rec={'case':name,'family':kind,'n':n,'w':w,'split':'calibration' if (n,w) in [(4,8),(8,8)] else 'test','routes':[],'status':'started'};rows.append(rec)
    try:
        rtl=router(n,w) if kind=='router' else fabric(kind,n,w)[0]
        (d/'design.v').write_text(rtl);(d/'tb.v').write_text(testbench(kind,n,w))
        rec['compile_sim_s']=run(['iverilog','-g2012','-s','tb','-o','sim.out','design.v','tb.v'],d,'iverilog.log')
        rec['simulation_s']=run(['vvp','sim.out'],d,'simulation.log')
        assert 'PASS' in (d/'simulation.log').read_text()
        ys=f'''read_verilog -sv design.v
synth -top top -flatten -noabc
dfflibmap -liberty {LIB}
abc -liberty {LIB}
clean
setundef -zero
hilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z
clean
stat -liberty {LIB}
write_verilog -noattr -noexpr mapped.v
write_json mapped.json
'''
        (d/'synth.ys').write_text(ys)
        rec['synthesis_s']=run(['yosys','-s','synth.ys'],d,'synthesis.log')
        mapped=json.loads((d/'mapped.json').read_text())['modules']['top']
        names=[x['type'] for x in mapped['cells'].values()]
        assert all(x in cell_area for x in names),set(names)-set(cell_area)
        assert not any('LATCH' in x.upper() or 'DLH' in x or 'DLL' in x for x in names)
        rec['synthesis_area_um2']=sum(cell_area[x] for x in names);rec['cells']=len(names)
        pins=sum(len(p['bits']) for p in mapped['ports'].values())
        side=math.ceil(max(math.sqrt(rec['synthesis_area_um2']/.45)+10,pins*.28/4+12))
        rec['die_side_um']=side;rec['port_bits']=pins
        prefix=f'''set_thread_count 1
read_liberty {LIB}
read_lef {TECH}
read_lef {MACRO}
'''
        place=prefix+f'''read_verilog mapped.v
link_design top
initialize_floorplan -die_area {{0 0 {side} {side}}} -core_area {{5 5 {side-5} {side-5}}} -site FreePDK45_38x28_10R_NP_162NW_34O
make_tracks
source {PLAT/'setRC.tcl'}
create_clock -name clk -period 5 [get_ports clk]
place_pins -hor_layers metal3 -ver_layers metal2 -min_distance 0.28
set t0 [clock milliseconds]
global_placement -density 0.60
detailed_placement
check_placement -verbose
puts "PLACEMENT_MS [expr {{[clock milliseconds]-$t0}}]"
write_def placed.def
write_db placed.odb
'''
        (d/'place.tcl').write_text(place)
        rec['placement_s']=run(['openroad','-exit','place.tcl'],d,'placement.log')
        for budget,layers,adjust in BUDGETS:
            rr={'budget':budget,'layers':layers,'adjustment':adjust,'status':'started'};rec['routes'].append(rr)
            route=f'''set_thread_count 1
read_liberty {LIB}
read_db placed.odb
source {PLAT/'setRC.tcl'}
create_clock -name clk -period 5 [get_ports clk]
set_routing_layers -signal {layers} -clock {layers}
set_global_routing_layer_adjustment {layers} {adjust}
set selected {{}}
foreach net [get_nets *] {{set nm [get_full_name $net];if {{$nm ne "clk"}} {{lappend selected $nm}}}}
set_nets_to_route $selected
global_route -start_incremental
global_route -end_incremental -allow_congestion
write_db {budget}.resources.odb
set t0 [clock milliseconds]
global_route -verbose -guide_file {budget}.guide -congestion_iterations 50 -allow_congestion -congestion_report_file {budget}.congestion.rpt
puts "GLOBAL_ROUTE_MS [expr {{[clock milliseconds]-$t0}}]"
write_db {budget}.odb
'''
            (d/f'{budget}.tcl').write_text(route)
            try:
                rr['openroad_wall_s']=run(['openroad','-exit',f'{budget}.tcl'],d,f'{budget}.log')
                txt=(d/f'{budget}.log').read_text();rr['global_route_s']=float(re.search(r'GLOBAL_ROUTE_MS (\d+)',txt).group(1))/1000
                phy,rr['extraction_s']=extract(d,budget)
                baseline,rr['resource_extraction_s']=extract(d,budget+'.resources')
                assert phy['grid_x']==baseline['grid_x'] and phy['grid_y']==baseline['grid_y']
                rec['placed_area_um2']=phy['cell_area_um2'];rr['grid']=[len(phy['grid_x']),len(phy['grid_y'])]
                wire=0
                for layer,b in zip(phy['layers'],baseline['layers']):
                    assert layer['name']==b['name'] and layer['capacity']==b['capacity']
                    for ur,br,cr in zip(layer['usage'],b['usage'],layer['capacity']):
                        for u,bv,c in zip(ur,br,cr):
                            assert 0<=bv<=c<=255 and 0<=u<=255
                            assert u>=bv,'Negative wire usage after resource subtraction'
                            wire+=u-bv
                assert wire>0,'No signal usage extracted'
                rr['signal_edge_usage']=wire;rr['status']='ok'
            except Exception as e:
                rr['status']='failed';rr['error']=str(e);(d/f'{budget}.error.txt').write_text(traceback.format_exc())
        rec['status']='ok' if all(r['status']=='ok' for r in rec['routes']) else 'partial'
    except Exception as e:
        rec['status']='failed';rec['error']=str(e);(d/'error.txt').write_text(traceback.format_exc())
    print(json.dumps(rec),flush=True)
    (OUT/'cases.json').write_text(json.dumps(rows,indent=2))
if (ROOT/'benchmarks/metrics.py').exists():
    run(['/usr/bin/python3',str(ROOT/'benchmarks/metrics.py')],OUT,'metrics.log',timeout=300)
(OUT/'files.sha256').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='files.sha256')+'\n')
print('COMPLETE',len(rows),'cases;',sum(r['status']=='ok' for r in rows),'fully successful',flush=True)
if any(r['status']!='ok' for r in rows):raise SystemExit(1)
