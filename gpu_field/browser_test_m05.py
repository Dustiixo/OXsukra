from playwright.sync_api import sync_playwright
from pathlib import Path
base=Path(__file__).resolve().parent.parent;root=base/'gpu_field'
html=(root/'index.html').read_text('utf-8').replace('<link rel="stylesheet" href="field.css">','<style>'+ (root/'field.css').read_text('utf-8')+'</style>')
for script,p in [('../spatial_lab/trace_data.js',base/'spatial_lab'/'trace_data.js'),('render_gl.js',root/'render_gl.js'),('field.js',root/'field.js')]: html=html.replace('<script src="'+script+'"></script>','<script>'+p.read_text('utf-8')+'</script>')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--enable-webgl','--use-angle=gl','--ignore-gpu-blocklist','--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1600,'height':900},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append('js error: '+str(e)))
 page.on('console',lambda m: errors.append('console: '+m.text) if m.type=='error' else None)
 print('set content...',flush=True)
 page.set_content(html,wait_until='domcontentloaded',timeout=15000)
 print('DOM ready',flush=True)
 page.wait_for_timeout(800)
 initial=page.evaluate('window.__IXO_GPU_TEST__?.getState()')
 print('FIELD',initial,flush=True)
 assert initial['mode']=='field' and initial['renderer'].startswith('webgl'),initial
 # prevent expensive screenshot until animation settles
 page.locator('#deck-mode').click(timeout=10000);page.wait_for_timeout(400)
 deck=page.evaluate('window.__IXO_GPU_TEST__?.getState()')
 shape=page.evaluate('''() => {const d=document.querySelector('#deck').getBoundingClientRect();return {x:d.x,y:d.y,width:d.width,height:d.height}}''')
 print('DECK',deck,'LAYOUT',shape,flush=True)
 assert deck['mode']=='deck' and deck['cursor']==initial['cursor']
 assert shape['x']==0 and shape['width']>=1599 and shape['height']>=899
 assert page.locator('[data-panel="paths"]').is_visible()
 assert page.locator('.path-item').count()>=4
 page.locator('[data-section="events"]').click()
 assert page.locator('[data-panel="events"]').is_visible()
 assert not page.locator('[data-panel="paths"]').is_visible()
 page.locator('[data-section="timeline"]').click()
 assert page.locator('[data-panel="timeline"]').is_visible()
 page.locator('#history-begin').click()
 assert page.evaluate('window.__IXO_GPU_TEST__.getState().cursor')==0
 page.locator('[data-section="system"]').click()
 assert page.locator('[data-panel="system"]').is_visible()
 page.locator('[data-quality="high"]').click()
 assert page.evaluate('window.__IXO_GPU_TEST__.getState().quality')=='high'
 page.locator('[data-quality="medium"]').click()
 page.locator('#deck-close').click()
 assert page.evaluate('window.__IXO_GPU_TEST__.getState().mode')=='field'
 page.locator('#deck-mode').click()
 page.keyboard.press('Escape')
 assert page.evaluate('window.__IXO_GPU_TEST__.getState().mode')=='field'
 page.keyboard.press('Tab')
 assert page.evaluate('window.__IXO_GPU_TEST__.getState().mode')=='deck'
 page.locator('[data-section="paths"]').click()
 page.evaluate('window.__IXO_GPU_TEST__.go(72)')
 page.wait_for_timeout(300)
 print('screen...',flush=True)
 page.screenshot(path=str(base/'evidence/M0_5_FULL_OVERLAY_DESKTOP.png'),timeout=20000)
 print('Screenshot complete',flush=True)
 page.set_viewport_size({'width':450,'height':850});page.wait_for_timeout(380)
 mobile=page.evaluate('''() => {const d=document.querySelector('#deck').getBoundingClientRect();return {width:d.width,height:d.height,viewWidth:innerWidth,overflowX:document.documentElement.scrollWidth>innerWidth}}''')
 assert mobile['width']>=450 and not mobile['overflowX'],mobile
 page.screenshot(path=str(base/'evidence/M0_5_FULL_OVERLAY_TOUCH.png'),timeout=20000)
 assert not errors,errors
 print('PASS GPU full screen / section navigation / state preserved / escape tab / timeline / quality / mobile / no js errors',flush=True)
 print('MOBILE',mobile,flush=True)
 b.close()
