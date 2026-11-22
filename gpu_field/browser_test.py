"""Browser integration test. Uses Chromium with WebGL via a virtual display.
Test run evidence must report actual renderer and GPU context; never claim device acceptance.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=Path(__file__).resolve().parent.parent
HERE=BASE/'gpu_field';EVIDENCE=BASE/'evidence';EVIDENCE.mkdir(exist_ok=True)

def html_bundle():
    html=(HERE/'index.html').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="field.css">','<style>'+(HERE/'field.css').read_text(encoding='utf-8')+'</style>')
    for name,path in [('../spatial_lab/trace_data.js',BASE/'spatial_lab'/'trace_data.js'),('render_gl.js',HERE/'render_gl.js'),('field.js',HERE/'field.js')]:
        html=html.replace(f'<script src="{name}"></script>','<script>'+path.read_text(encoding='utf-8')+'</script>')
    return html

def run():
  with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--enable-webgl','--use-angle=gl','--ignore-gpu-blocklist','--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':1600,'height':900},device_scale_factor=1,has_touch=True)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append('page error '+str(e)))
    page.on('console',lambda m:errors.append('console '+m.text) if m.type=='error' else None)
    page.set_content(html_bundle(),wait_until='load');page.wait_for_timeout(700)
    s=page.evaluate('window.__IXO_GPU_TEST__?.getState()')
    assert s and s['renderer']=='webgl2' and s['frames']>=2,s
    assert (s['cursor'],s['total'],s['branches'])==(72,72,4),s
    assert s['links']>0,s
    print('GPU',s['renderer'],'FRAMES',s['frames'],'BRANCHES',s['branches'],'SHARED_SOURCE_EDGES',s['links'])
    page.screenshot(path=str(EVIDENCE/'DUAL_SURFACE_FIELD_WEBGL.png'))

    # Two modes operate on the exact same research state.
    page.locator('#deck-mode').click();t=page.evaluate('window.__IXO_GPU_TEST__.getState()');assert t['mode']=='deck' and t['cursor']==s['cursor'] and t['branches']==s['branches']
    assert page.locator('.path-item').count()==4
    page.screenshot(path=str(EVIDENCE/'DUAL_SURFACE_DECK_WEBGL.png'))
    page.locator('#field-mode').click();assert page.evaluate('window.__IXO_GPU_TEST__.getState().mode')=='field'

    # Rewind the source trace and inspect a recorded event.
    page.evaluate('window.__IXO_GPU_TEST__.go(0)')
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().branches')==1
    page.locator('#forward').click()
    assert 'research run' in page.locator('#event-title').text_content().lower()
    page.evaluate('window.__IXO_GPU_TEST__.go(72)')
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().branches')==4
    page.evaluate('window.__IXO_GPU_TEST__.select("p001")')
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().selected')=='p001'
    page.wait_for_timeout(320)

    # Real mouse orbit and wheel zoom.
    root=page.evaluate('window.__IXO_GPU_TEST__.projection().find(x=>x.id==="root")')
    before=page.evaluate('window.__IXO_GPU_TEST__.projection().find(x=>x.id==="p001")')
    page.mouse.move(900,600);page.mouse.down();page.mouse.move(980,650,steps=8);page.mouse.up();page.wait_for_timeout(350)
    after=page.evaluate('window.__IXO_GPU_TEST__.projection().find(x=>x.id==="p001")')
    assert abs(after['x']-before['x'])>4 or abs(after['y']-before['y'])>4,(before,after)
    page.mouse.wheel(0,-500);page.wait_for_timeout(300)
    zoom=page.evaluate('window.__IXO_GPU_TEST__.projection().find(x=>x.id==="p001")')
    assert abs(zoom['x']-after['x'])>1 or abs(zoom['y']-after['y'])>1,(after,zoom)

    # Two-finger gestures exercise actual pointer events in Chromium via CDP.
    cdp=context.new_cdp_session(page)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':660,'y':440,'id':0},{'x':760,'y':440,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':620,'y':440,'id':0},{'x':800,'y':440,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    page.wait_for_timeout(250)
    assert not errors,errors

    # Graphics quality is a renderer option, not a research mutation.
    page.locator('#deck-mode').click();page.locator('[data-quality="high"]').click()
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().quality')=='high'
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().cursor')==72
    page.locator('[data-quality="low"]').click()
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().quality')=='low'

    # Private JSON import rejects invalid provenance markers.
    bad=EVIDENCE/'_INVALID_TEMP_TRACE.json';bad.write_text('{"schema":"untrusted","events":[]}',encoding='utf-8')
    page.locator('#trace-input').set_input_files(str(bad));page.wait_for_timeout(100)
    assert page.evaluate('window.__IXO_GPU_TEST__.getState().cursor')==72
    bad.unlink()

    # Mobile mode still has access to the deck and the main field.
    page.set_viewport_size({'width':450,'height':850});page.wait_for_timeout(420)
    page.screenshot(path=str(EVIDENCE/'DUAL_SURFACE_TOUCH_VIEW.png'))
    page.locator('#field-mode').click();page.wait_for_timeout(420)
    page.screenshot(path=str(EVIDENCE/'DUAL_SURFACE_TOUCH_FIELD.png'))
    assert page.locator('#field-mode').is_visible()
    assert not errors,errors
    print('PASS WebGL2: field/deck state preservation, trace rewind, branch inspect, orbit, zoom, two-touch gesture, graphics presets, bad-trace rejection, mobile, no JS errors')

    # Force WebGL1 fallback and verify render starts in the same browser.
    legacy=context.new_page();legacy_errors=[]
    legacy.on('pageerror',lambda e:legacy_errors.append(str(e)))
    legacy_html=html_bundle().replace('</head>',"<script>const old = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext=function(kind,opts){if(kind==='webgl2')return null;return old.call(this,kind,opts)};</script></head>")
    legacy.set_content(legacy_html,wait_until='load');legacy.wait_for_timeout(450)
    ls=legacy.evaluate('window.__IXO_GPU_TEST__?.getState()')
    if ls and ls['renderer']=='webgl1' and ls['frames']>1 and not legacy_errors:
        print('PASS WebGL1 compatibility fallback',ls['frames'],'frames')
    else:
        raise AssertionError(('WEBGL1 FAILED',ls,legacy_errors))
    browser.close()

if __name__=='__main__':run()
