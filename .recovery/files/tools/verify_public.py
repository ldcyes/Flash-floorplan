#!/usr/bin/env python3
"""Verify the public CDN serves this exact HTML at both supported URLs."""
import hashlib, json, os, time, urllib.request
BASE='https://ldcyes.github.io/Flash-floorplan/'
EXPECTED='65a187941021feef7c81970b63915317e7be9192630205d8fe1511e110fa52c7'
for path in ['', 'planner.html']:
    ok=False
    for attempt in range(18):
        url=BASE+path+'?release='+os.environ.get('GITHUB_SHA','8.3.0')+'&probe='+str(attempt)
        try:
            req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'Flash-floorplan-Pages-check'})
            with urllib.request.urlopen(req,timeout=20) as r:
                data=r.read(); status=r.status
            digest=hashlib.sha256(data).hexdigest()
            if status==200 and digest==EXPECTED:
                print(json.dumps({'url':BASE+path,'http':status,'bytes':len(data),'sha256':digest,'verified':True}),flush=True)
                ok=True; break
            print('Waiting for exact deployed release:',path,status,digest,flush=True)
        except Exception as e:
            print('CDN check retry:',path,str(e),flush=True)
        time.sleep(5)
    if not ok: raise SystemExit('Public URL did not serve the expected release: '+BASE+path)
