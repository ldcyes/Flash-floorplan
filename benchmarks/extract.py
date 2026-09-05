"""OpenROAD embedded Python: extract physical data, never SWIG pointer addresses."""
import os,json,odb,openroad,ctypes
from pathlib import Path
path=os.environ['INPUT_DB'];out=os.environ['OUTPUT_JSON']
owner=openroad.Tech();design=openroad.Design(owner);design.readDb(path)
block=design.getBlock();tech=owner.getTech();units=block.getDbUnitsPerMicron()
def box(b):return [b.xMin()/units,b.yMin()/units,b.xMax()/units,b.yMax()/units]
def center(b):return [(b.xMin()+b.xMax())/(2*units),(b.yMin()+b.yMax())/(2*units)]
def scalar(value):
    # This pinned binary exposes uint8_t return values as owned SWIG pointers.
    # The int(pointer) is an ADDRESS, not usage. Dereference only this known type.
    if isinstance(value,int):result=value
    elif 'uint8_t' in str(value):result=ctypes.c_uint8.from_address(int(value)).value
    else:raise TypeError('Unsupported GCell scalar binding: '+str(type(value)))
    assert 0<=result<=255
    return result
r={'units_per_um':units,'die':box(block.getDieArea()),'instances':len(block.getInsts()),'cell_area_um2':sum(i.getMaster().getWidth()*i.getMaster().getHeight()/units**2 for i in block.getInsts()),'nets':[]}
for net in block.getNets():
    if str(net.getSigType()) in ('POWER','GROUND') or net.getName()=='clk':continue
    pts=[];driver=None
    for it in net.getITerms():
        xy=it.getAvgXY()
        if len(xy)==3:
            if not xy[0]:continue
            pt=[xy[1]/units,xy[2]/units]
        elif len(xy)==2:pt=[xy[0]/units,xy[1]/units]
        else:pt=center(it.getBBox())
        pts.append(pt)
        if str(it.getIoType())=='OUTPUT':driver=pt
    for bt in net.getBTerms():
        pt=center(bt.getBBox());pts.append(pt)
        if str(bt.getIoType())=='INPUT':driver=pt
    pts=list(dict.fromkeys(tuple(x) for x in pts))
    if len(pts)>=2:r['nets'].append({'name':net.getName(),'driver':driver or list(pts[0]),'pins':pts})
grid=block.getGCellGrid()
if grid:
    xs=list(grid.getGridX());ys=list(grid.getGridY())
    r['grid_x']=[x/units for x in xs];r['grid_y']=[y/units for y in ys];r['layers']=[]
    for layer in tech.getLayers():
        if layer.getRoutingLevel()<=0:continue
        u=[];c=[]
        for yi in range(len(ys)):
            ur=[];cr=[]
            for xi in range(len(xs)):
                ur.append(scalar(grid.getUsage(layer,xi,yi)))
                cr.append(scalar(grid.getCapacity(layer,xi,yi)))
            u.append(ur);c.append(cr)
        r['layers'].append({'name':layer.getName(),'level':layer.getRoutingLevel(),'direction':str(layer.getDirection()),'usage':u,'capacity':c})
Path(out).write_text(json.dumps(r,separators=(',',':')))
print('EXTRACT',out,'instances',r['instances'],'nets',len(r['nets']),'grid',len(r.get('grid_x',[])),len(r.get('grid_y',[])))
