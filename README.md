# Flash-flooplanner Pixel Edition 8.3

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
