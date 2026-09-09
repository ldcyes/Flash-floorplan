#!/usr/bin/env python3
"""One-time exact-file recovery; incomplete archives never enter production."""
from pathlib import Path
import hashlib,lzma,json,shutil
ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/flash-restored'); OUT.mkdir(exist_ok=True)
chunks=[ROOT/'parts'/f'{i:02d}.bin' for i in range(21)]
assert all(p.stat().st_size==9000 for p in chunks)
packed=b''.join(p.read_bytes() for p in chunks)
raw=lzma.LZMADecompressor().decompress(packed)
html=raw[1028608:1582671]
expected='65a187941021feef7c81970b63915317e7be9192630205d8fe1511e110fa52c7'
assert len(html)==554063 and hashlib.sha256(html).hexdigest()==expected, 'Refusing to publish an incomplete or changed planner'
(OUT/'index.html').write_bytes(html);(OUT/'planner.html').write_bytes(html)
(OUT/'planner').mkdir(exist_ok=True)
(OUT/'planner'/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Flash-flooplanner</title><meta http-equiv="refresh" content="0;url=../"><script>location.replace('../'+location.search+location.hash)</script><a href="../">打开 Flash-flooplanner / Open planner</a></html>''',encoding='utf-8')
shutil.copytree(ROOT/'files'/'tools',OUT/'tools',dirs_exist_ok=True)
(OUT/'build-info.json').write_text(json.dumps({'version':'8.3.0','planner_bytes':len(html),'planner_sha256':expected,'entrypoints':['/','planner.html','planner/'],'source':'Recovered exact frozen v8.3 HTML; production serves plain static files'},indent=2)+'\n')
(OUT/'README.md').write_text('''# Flash-flooplanner Pixel Edition 8.3

The complete interactive planner is served directly at https://ldcyes.github.io/Flash-floorplan/ .
The compatibility entry https://ldcyes.github.io/Flash-floorplan/planner.html serves the same verified application.

## Deployment repair

The earlier Pages job failed with `xz: Unexpected end of input`: only a prefix of the encoded release was committed. It also stopped publishing the legacy `planner.html` entry. The exact frozen v8.3 application is now restored as ordinary HTML, with no browser decompression loader or incomplete payload in the deployment path.

- `index.html`: complete, self-contained Pixel v8.3 software, not a landing page.
- `planner.html`: identical compatibility entry.
- `planner/index.html`: compatibility redirect to the root.
- `pixel.html`: previous introduction page, retained separately.
- `build-info.json`: version, byte count and SHA-256 of the planner.
- `tools/check_site.py`: release integrity and 15 embedded JavaScript syntax checks.
- `tools/smoke_browser.py`: HTTP-served Chromium smoke test of both entries.
- `tools/verify_public.py`: post-deployment public HTTP and full-file digest checks.

## Local use

Run `python3 -m http.server 8080` in this directory, then open `http://localhost:8080/`.
The core planner also works as a standalone local HTML file. Google Drive requires separate OAuth configuration and an authorized origin.

## Validation scope

Deployment tests check software loading, UI controls and JSON export. They do not establish physical accuracy. Architecture comparison is a heuristic; previous Nangate45 results must not be presented as validation of every process node or of the new topology builder.

Author: Liangdacheng with GPT5.5. The original repository LICENSE is retained. This repair does not relicense third-party material or publish an arXiv submission.
''',encoding='utf-8')
print('Recovered',len(html),'bytes;',expected)
