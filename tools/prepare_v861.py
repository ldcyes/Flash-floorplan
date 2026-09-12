#!/usr/bin/env python3
from pathlib import Path
import re, sys
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding='utf-8')
text=text.replace('PIXEL EDITION · BUILD 8.6</span>','PIXEL EDITION · BUILD 8.6.1</span>')
text=text.replace("uiVersion:'8.6.0'","uiVersion:'8.6.1'")
text=text.replace('Flash-flooplanner Pixel Edition 8.6 |','Flash-flooplanner Pixel Edition 8.6.1 |')
text=text.replace('<button class="btn" id="driveBtn" type="button"><span aria-hidden="true">↥</span> Google Drive</button>','')
for marker in ['window.FLASH_DRIVE_CONFIG', 'FlashDriveTransport', 'User-initiated Google Drive snapshots & Picker']:
    pat=re.compile(r'<script>\s*(?:(?!</script>).)*?'+re.escape(marker)+r'(?:(?!</script>).)*?</script>', re.S)
    text,n=pat.subn('',text)
    if n!=1:
        raise SystemExit(f'expected one script containing {marker!r}, found {n}')
text=text.replace("<button class=\"btn guide-full\" id=\"guideDrive\">${J.esc(T.t('openDrive'))}</button>","")
text=text.replace("$('#guideDrive').onclick=()=>window.FlashDrive?.open();","")
text=text.replace('or explicitly upload a snapshot to Drive.','or export Draw.io/SVG/PNG locally.')
text=text.replace('或明确上传 Drive 快照。','或导出 Draw.io/SVG/PNG 到本地。')
text=text.replace('或明確上傳 Drive 快照。','或匯出 Draw.io/SVG/PNG 到本地。')
text=text.replace('または明示的に Drive にスナップショットを保存できます。','または Draw.io/SVG/PNG をローカルに書き出せます。')
for forbidden in ['tt_blackhole_tensix:', 'tt_blackhole_p150:', 'id="driveBtn"', 'window.FLASH_DRIVE_CONFIG', 'window.FlashDrive=', 'FlashDriveTransport=']:
    if forbidden in text:
        raise SystemExit(f'forbidden release marker remains: {forbidden}')
for required in ["uiVersion:'8.6.1'", 'arm_a55_core', 'tt_ocelot_medium_rvv', 'placeWireBtn85', 'connectionsBtn84', '</html>']:
    if required not in text:
        raise SystemExit(f'missing release marker: {required}')
dst.parent.mkdir(parents=True,exist_ok=True); dst.write_text(text,encoding='utf-8')
print(f'prepared {dst} ({dst.stat().st_size} bytes)')
