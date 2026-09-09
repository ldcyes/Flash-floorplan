#!/usr/bin/env python3
"""Browser smoke test of the served site, not a design-accuracy benchmark."""
import json, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for path in ['/', '/planner.html']:
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[]; page.on('pageerror',lambda err:errors.append(str(err)))
            response=page.goto(base+path,wait_until='load')
            assert response.status==200
            page.wait_for_function('window.FlashPlanner && window.FlashFabricLab && window.FlashPlanner.uiVersion === "8.3.0"',timeout=30000)
            assert page.locator('body').evaluate('(e)=>e.classList.contains("pixel-theme")')
            assert page.locator('#floorplanSvg').is_visible()
            count=page.locator('.component-card').count()
            assert count>20, f'Missing template library: {count}'
            page.select_option('#languageSelect','en')
            page.locator('#compareArchitectureBtn').click()
            page.wait_for_selector('#a83_close',state='visible')
            page.locator('#a83_close').click()
            page.select_option('#languageSelect','zh-CN')
            with page.expect_download() as download:
                page.locator('#saveJsonBtn').click()
            project=json.loads(Path(download.value.path()).read_text())
            assert 'modules' in project and 'nets' in project
            assert not errors, errors
            checks.append({'path':path,'status':200,'version':'8.3.0','templates':count,'pixel':True,'architecture_dialog':True,'language_switch':True,'save_json':True,'page_errors':errors})
            page.close()
        browser.close()
finally:
    server.shutdown()
print(json.dumps({'browser_smoke':checks},ensure_ascii=False,indent=2))
