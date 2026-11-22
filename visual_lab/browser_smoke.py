from pathlib import Path
import threading, functools, http.server
from playwright.sync_api import sync_playwright
WEBROOT=Path(__file__).resolve().parents[1]/'visual_lab'
out=WEBROOT.parent/'docs/visual_lab_preview'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,**({'executable_path':'/usr/bin/chromium'} if Path('/usr/bin/chromium').exists() else {}),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1536,'height':940},device_scale_factor=1)
    errs=[]
    page.on('pageerror',lambda exc:errs.append(str(exc)))
    html=(WEBROOT/"index.html").read_text(encoding="utf-8")
    html=html.replace('<link rel="stylesheet" href="styles.css" />', '<style>'+(WEBROOT/"styles.css").read_text(encoding="utf-8")+'</style>')
    for f in ("demo_trace.js","app.js"):
        html=html.replace('<script src="'+f+'"></script>','<script>'+(WEBROOT/f).read_text(encoding="utf-8")+'</script>')
    page.set_content(html,wait_until="load")
    page.wait_for_timeout(250)
    assert page.locator('#seek-label').inner_text()=='0 / 72'
    assert 'cryptic' in page.locator('#stage-title').inner_text()
    page.locator('#seek').fill('65')
    assert '65 / 72' in page.locator('#seek-label').inner_text()
    page.screenshot(path=str(out/'01_base.png'),full_page=True)
    page.locator('[data-stage="2"]').click(); assert 'What happened' in page.locator('#stage-title').inner_text()
    page.screenshot(path=str(out/'02_explain.png'),full_page=True)
    page.locator('[data-stage="3"]').click(); assert page.locator('.graph-node').count()>=3
    page.locator('[data-graph-bid="p001"]').click(); assert 'p001' in page.locator('.branch.on').inner_text()
    page.screenshot(path=str(out/'03_map.png'),full_page=True)
    page.locator('[data-stage="4"]').click()
    assert page.locator('.policy-row').count()==3
    page.locator('[data-policy="lead"]').click()
    assert 'DESIGN SIMULATION' in page.locator('#policy-output').inner_text()
    page.screenshot(path=str(out/'04_open_flow.png'),full_page=True)
    page.locator('#how-works').click()
    assert page.locator('#explainer').is_visible()
    page.locator('#close-explainer').click()
    assert not page.locator('#explainer').is_visible()
    # File input loads exported local JSON; no upload
    page.locator('#trace-input').set_input_files(str(WEBROOT/'sample_trace.json'))
    page.wait_for_timeout(200)
    assert 'LOADED LOCAL TRACE' in page.locator('#data-badge').inner_text()
    # Narrow/mobile viewport doesn't crash
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(out/'mobile.png'),full_page=True)
    assert not errs,errs
    print('PASS: offline browser, 4 stages, 72 receipts, linked graph, adaptive simulation, trace import, mobile view, no JS exceptions')
    browser.close()
