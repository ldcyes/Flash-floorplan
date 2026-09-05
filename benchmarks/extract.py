"""Executed by OpenROAD's embedded Python. Extract unmodified physical evidence."""
import os,json,odb,inspect
from pathlib import Path
path=os.environ['INPUT_DB'];out=os.environ['OUTPUT_JSON']
db=odb.dbDatabase.create();odb.read_db(db,path)
block=db.getChip().getBlock(); tech=db.getTech(); units=block.getDbUnitsPerMicron()
def box(b):return [b.xMin()/units,b.yMin()/units,b.xMax()/units,b.yMax()/units]
def center(b):return [(b.xMin()+b.xMax())/(2*units),(b.yMin()+b.yMax())/(2*units)]
r={'units_per_um':units,'die':box(block.getDieArea()),'instances':len(block.getInsts()),'cell_area_um2':sum(i.getMaster().getWidth()*i.getMaster().getHeight()/units**2 for i in block.getInsts()),'nets':[]}
for net in block.getNets():
    if str(net.getSigType()) in ('POWER','GROUND') or net.getName()=='clk':continue
    pts=[];driver=None
    for it in net.getITerms():
        xy=it.getAvgXY()
        if isinstance(xy,tuple) and len(xy)==3:
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
    print('getUsage doc:',odb.dbGCellGrid.getUsage.__doc__)
    print('getCapacity doc:',odb.dbGCellGrid.getCapacity.__doc__)
    xs=list(grid.getGridX());ys=list(grid.getGridY())
    r['grid_x']=[x/units for x in xs];r['grid_y']=[y/units for y in ys];r['layers']=[]
    for layer in tech.getLayers():
        if layer.getRoutingLevel()<=0:continue
        u=[];c=[]
        for yi in range(len(ys)):
            ur=[];cr=[]
            for xi in range(len(xs)):
                ur.append(int(grid.getUsage(layer,xi,yi)))
                cr.append(int(grid.getCapacity(layer,xi,yi)))
            u.append(ur);c.append(cr)
        r['layers'].append({'name':layer.getName(),'level':layer.getRoutingLevel(),'direction':str(layer.getDirection()),'usage':u,'capacity':c})
Path(out).write_text(json.dumps(r,separators=(',',':')))
print('EXTRACT',out,'instances',r['instances'],'nets',len(r['nets']),'grid',len(r.get('grid_x',[])),len(r.get('grid_y',[])))
