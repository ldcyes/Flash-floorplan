#!/usr/bin/env python3
"""Fail closed on truncated/loader-only releases; run before publishing Pages."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, json, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '65a187941021feef7c81970b63915317e7be9192630205d8fe1511e110fa52c7'
class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False); self.parts=[]; self.active=False
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            a = dict(attrs)
            self.active = not a.get('src') and a.get('type','') in ('', 'text/javascript', 'application/javascript', 'module')
            if self.active: self.parts.append('')
    def handle_endtag(self, tag):
        if tag == 'script': self.active=False
    def handle_data(self, data):
        if self.active: self.parts[-1] += data

data=(ROOT/'index.html').read_bytes()
assert len(data)==554063, f'Unexpected release length: {len(data)}'
assert hashlib.sha256(data).hexdigest()==EXPECTED, 'Release SHA-256 mismatch'
assert (ROOT/'planner.html').read_bytes()==data, 'Legacy planner entry differs'
text=data.decode('utf-8')
for marker in ['window.FlashPlanner=', "uiVersion:'8.3.0'", 'compareArchitectureBtn', 'window.FlashFabricLab=', 'pixel-theme', '</html>']:
    assert marker in text, f'Missing release marker: {marker}'
p=Scripts(); p.feed(text)
assert len(p.parts)==15, f'Expected 15 inline JS scripts, got {len(p.parts)}'
with tempfile.TemporaryDirectory() as d:
    for i, script in enumerate(p.parts):
        f=Path(d)/f'script-{i:02d}.js'; f.write_text(script, encoding='utf-8')
        subprocess.run(['node','--check',str(f)],check=True)
print(json.dumps({'release':'8.3.0','bytes':len(data),'sha256':EXPECTED,'inline_scripts_checked':len(p.parts),'legacy_entry':'identical'},indent=2))
