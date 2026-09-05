/* MIT, Liangdacheng. Post-placement adapter for Flash-flooplanner.
 * segmentsInGrid is copied verbatim (formatting excepted) from frozen v6.
 * Inputs: placed pins and grid geometry only. NO routed usage or capacity.
 * Full v6 HTML SHA256: 6ffeff3cce7d4c32c521e071f794076cdd5c46bd062bfd47effd9e366f60b27b
 */
'use strict';
const fs=require('fs'),{performance}=require('perf_hooks');
const clamp=(v,l,h)=>Math.max(l,Math.min(h,v));
function segmentsInGrid(p1,p2,w,h,cols,rows) {
    const dx=p2.x-p1.x,dy=p2.y-p1.y;
    if(Math.abs(dx)+Math.abs(dy)<1e-12)return [];
    if(Math.abs(dx)>1e-9 && Math.abs(dy)>1e-9) throw new Error('Routing segments must be Manhattan.');
    const horizontal=Math.abs(dx)>1e-9, unit=horizontal?w/cols:h/rows;
    const fixed=horizontal?p1.y:p1.x, fixedUnit=horizontal?h/rows:w/cols;
    if(fixed<0 || fixed>(horizontal?h:w))return [];
    const rowOrCol=clamp(Math.floor(fixed/fixedUnit),0,(horizontal?rows:cols)-1);
    const lo=Math.max(0,Math.min(horizontal?p1.x:p1.y,horizontal?p2.x:p2.y));
    const hi=Math.min(horizontal?w:h,Math.max(horizontal?p1.x:p1.y,horizontal?p2.x:p2.y));
    if(hi<=lo)return [];
    const res=[];
    for(let i=Math.floor(lo/unit);i<=Math.min((horizontal?cols:rows)-1,Math.ceil(hi/unit)-1);i++) {
      const fraction=(Math.min(hi,(i+1)*unit)-Math.max(lo,i*unit))/unit;
      if(fraction>1e-12)res.push({r:horizontal?rowOrCol:i,c:horizontal?i:rowOrCol,horizontal,fraction});
    }
    return res;
}
const a=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const nx=a.grid_x.length,ny=a.grid_y.length;
function coord(v,axis,end){
 let i=0;while(i+1<axis.length && axis[i+1]<=v)i++;
 return clamp(i+(v-axis[i])/((axis[i+1]??end)-axis[i]),0,axis.length-1e-9);
}
function point(p){return {x:coord(p[0],a.grid_x,a.die[2]),y:coord(p[1],a.grid_y,a.die[3])};}
const data=a.nets.map(n=>({driver:point(n.driver),pins:n.pins.map(point)}));
function matrix(){return Array.from({length:ny},()=>Array(nx).fill(0));}
function legacy(){
 const H=matrix(),V=matrix();
 for(const net of data)for(const p of net.pins){
  const d=net.driver;
  const mid=Math.abs(d.x-p.x)>=Math.abs(d.y-p.y)?{x:p.x,y:d.y}:{x:d.x,y:p.y};
  for(const [u,v] of [[d,mid],[mid,p]])for(const h of segmentsInGrid(u,v,nx,ny,nx,ny))
   (h.horizontal?H:V)[h.r][h.c]+=h.fraction;
 }
 return {H,V};
}
function mstUnion(){
 const H=matrix(),V=matrix();
 for(const net of data){
  const pts=[...new Map(net.pins.map(p=>{const q={x:Math.floor(p.x),y:Math.floor(p.y)};return [q.x+','+q.y,q]})).values()];
  if(pts.length<2)continue;
  const used=new Set([0]),best=pts.map(p=>Math.abs(p.x-pts[0].x)+Math.abs(p.y-pts[0].y)),parent=pts.map(()=>0);
  const edgeSet=new Set();
  function segment(p,q){
   if(p.y===q.y)for(let x=Math.min(p.x,q.x);x<Math.max(p.x,q.x);x++)edgeSet.add('H,'+p.y+','+x);
   else for(let y=Math.min(p.y,q.y);y<Math.max(p.y,q.y);y++)edgeSet.add('V,'+y+','+p.x);
  }
  while(used.size<pts.length){
   let j=-1;for(let i=0;i<pts.length;i++)if(!used.has(i)&&(j<0||best[i]<best[j]))j=i;
   const p=pts[parent[j]],q=pts[j],mid=Math.abs(p.x-q.x)>=Math.abs(p.y-q.y)?{x:q.x,y:p.y}:{x:p.x,y:q.y};
   segment(p,mid);segment(mid,q);used.add(j);
   for(let i=0;i<pts.length;i++)if(!used.has(i)){
    const dist=Math.abs(q.x-pts[i].x)+Math.abs(q.y-pts[i].y);
    if(dist<best[i]){best[i]=dist;parent[i]=j;}
   }
  }
  for(const key of edgeSet){const [dir,y,x]=key.split(',');(dir==='H'?H:V)[+y][+x]++;}
 }
 return {H,V};
}
function bench(fn){fn();const ms=[];let result;for(let i=0;i<7;i++){const t=performance.now();result=fn();ms.push(performance.now()-t);}ms.sort((x,y)=>x-y);return {...result,kernel_ms:ms[3],timings_ms:ms};}
console.log(JSON.stringify({legacy_star_tile:bench(legacy),mst_union_edge:bench(mstUnion),scope:'actual post-placement pins; no routed demand given to predictor'}));
