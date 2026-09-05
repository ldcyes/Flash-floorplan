#!/usr/bin/env bash
# Flash-flooplanner benchmark bootstrap; public synthetic RTL only.
set -euo pipefail
mkdir -p benchmark-results tool-cache platform
DEB=openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
URL=https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/$DEB
if [ ! -s tool-cache/$DEB ]; then curl -fL --retry 3 "$URL" -o tool-cache/$DEB; fi
sudo apt-get update -qq
sudo apt-get install -y yosys iverilog python3-numpy python3-scipy "$(pwd)/tool-cache/$DEB"
openroad -version | tee benchmark-results/openroad-version.txt
yosys -V | tee benchmark-results/yosys-version.txt
iverilog -V > benchmark-results/iverilog-version.txt 2>&1
sha256sum tool-cache/$DEB > benchmark-results/tool-package.sha256
# Resolve and record the exact ORFS library snapshot; reruns may supply ORFS_REF.
REF=${ORFS_REF:-$(curl -fsSL https://api.github.com/repos/The-OpenROAD-Project/OpenROAD-flow-scripts/commits/master | python3 -c 'import json,sys;print(json.load(sys.stdin)["sha"])')}
echo "$REF" > benchmark-results/orfs-commit.txt
BASE=https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/$REF/flow/platforms/nangate45
for f in lef/NangateOpenCellLibrary.tech.lef lef/NangateOpenCellLibrary.macro.mod.lef lib/NangateOpenCellLibrary_typical.lib setRC.tcl; do
  curl -fL --retry 3 "$BASE/$f" -o platform/$(basename "$f")
done
sha256sum platform/* > benchmark-results/platform.sha256
{ uname -a; lscpu; free -h; python3 --version; node --version; } > benchmark-results/host.txt
cat > benchmark-results/probe.py <<'PY'
import odb, openroad, sys
print('Python',sys.version)
for typ in ('dbGCellGrid','dbITerm','dbBTerm','dbBlock','dbTechLayer'):
    print(typ,[n for n in dir(getattr(odb,typ)) if any(s in n.lower() for s in ('usage','capacity','grid','point','avg','congestion','bbox'))])
PY
openroad -python -exit benchmark-results/probe.py > benchmark-results/api-probe.log 2>&1 || true
cat benchmark-results/api-probe.log
