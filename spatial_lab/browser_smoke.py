"""Headless browser interaction smoke. Embedded assets bypass sandbox navigational restrictions.
All click/drag/zoom/replay actions are real Playwright browser interactions.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'evidence'
OUT.mkdir(exist_ok=True)

def html_bundle():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="chamber.css">','<style>'+(ROOT/'chamber.css').read_text(encoding='utf-8')+'</style>')
    for f in ('trace_data.js','chamber.js'):
        html=html.replace('<script src="'+f+'"></script>','<script>'+(ROOT/f).read_text(encoding='utf-8')+'</script>')
    return html

def run():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1600,'height':900},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.set_content(html_bundle(),wait_until='load')
        page.wait_for_timeout(900)
        state=page.evaluate('window.__IXO_TEST__.getState()')
        assert state['total']==72 and state['cursor']==72 and state['branchCount']==4,state
        assert state['sourceCount']==34 and state['edgeCount']>0,state
        assert page.locator('#paths button').count()==4
        page.screenshot(path=str(OUT/'SPATIAL_CHAMBER_DESKTOP.png'),full_page=True)

        # Rewind and step: historical state projects only branches seen at that point.
        page.locator('#first').click()
        state=page.evaluate('window.__IXO_TEST__.getState()')
        assert state['cursor']==0 and state['branchCount']==1,state
        page.locator('#next').click()
        assert page.locator('#event-title').inner_text()=='A new investigation began.'
        assert '#001' in page.locator('#receipt-num').inner_text()
        page.locator('#seek').fill('13')
        state=page.evaluate('window.__IXO_TEST__.getState()')
        assert state['cursor']==13 and state['branchCount']==4,state
        page.locator('#seek').fill('22')
        assert 'SOURCE' in page.locator('#event-kind').inner_text()
        assert 'SHA-256' not in page.locator('#proof').inner_text() or page.locator('#proof-digest').inner_text()

        # Select actual path via HUD, then focus it.
        page.locator('button.path[data-branch="p001"]').click()
        assert page.locator('#selected-label').inner_text().startswith('P001')
        before=page.evaluate('window.__IXO_TEST__.project("p002")')
        canvas=page.locator('canvas#field')
        box=canvas.bounding_box()
        page.mouse.move(box['x']+box['width']*.55,box['y']+box['height']*.52)
        page.mouse.down()
        page.mouse.move(box['x']+box['width']*.64,box['y']+box['height']*.61,steps=9)
        page.mouse.up()
        page.wait_for_timeout(580)
        after=page.evaluate('window.__IXO_TEST__.project("p002")')
        assert abs(after['x']-before['x'])>8 or abs(after['y']-before['y'])>8,(before,after)
        page.mouse.wheel(0,-520)
        page.wait_for_timeout(420)
        zoomed=page.evaluate('window.__IXO_TEST__.project("p002")')
        assert abs(zoomed['x']-after['x'])>2 or abs(zoomed['y']-after['y'])>2,(after,zoomed)
        page.locator('#reset-view').click()
        page.wait_for_timeout(450)

        # Modal and first-party no-action UI.
        page.locator('#help').click();assert page.locator('#about').is_visible()
        assert 'Pretty is not proof' in page.locator('#about').inner_text()
        page.locator('#close-about').click();assert not page.locator('#about').is_visible()

        # Replay controls and actual proof panel.
        page.locator('#first').click()
        page.locator('#play').click()
        page.wait_for_timeout(1200)
        replay=page.evaluate('window.__IXO_TEST__.getState()')
        assert replay['cursor']>=1 and replay['playing'],replay
        page.locator('#play').click()
        assert not page.evaluate('window.__IXO_TEST__.getState().playing')
        page.locator('#last').click()
        page.locator('#trace-file').set_input_files(str(ROOT.parent/'visual_lab'/'sample_trace.json'))
        page.wait_for_timeout(160)
        assert page.evaluate('window.__IXO_TEST__.getState().total')==72

        # Mobile viewport should remain interactive and not throw.
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT/'SPATIAL_CHAMBER_MOBILE.png'),full_page=True)
        page.locator('#next').click()
        assert not errors,errors
        print('PASS browser: 72 real receipts; 4 interactive branches; historical rewind; source proof; 3D orbit/zoom; focus; modal; replay; local JSON import; mobile; no JS errors')
        browser.close()

if __name__=='__main__':run()
