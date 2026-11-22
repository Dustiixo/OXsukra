from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
base=root.parent
html=(root/'index.html').read_text().replace('<link rel="stylesheet" href="field.css">','<style>'+ (root/'field.css').read_text()+'</style>')
for script,p in [('../spatial_lab/trace_data.js',base/'spatial_lab'/'trace_data.js'),('render_gl.js',root/'render_gl.js'),('field.js',root/'field.js')]: html=html.replace('<script src="'+script+'"></script>','<script>'+p.read_text()+'</script>')
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--use-angle=gl','--enable-unsafe-swiftshader','--enable-webgl','--ignore-gpu-blocklist','--disable-dev-shm-usage'])
 p=b.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
 errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.set_content(html,wait_until='domcontentloaded',timeout=20000)
 p.wait_for_function('window.__IXO_GPU_TEST__?.getState().frames>2',timeout=20000)
 initial=p.evaluate('window.__IXO_GPU_TEST__.getState()');print('initial',initial,flush=True)
 assert initial['renderer']=='webgl2'
 p.locator('#dismiss-intro').click();p.screenshot(path=str(base/'evidence/M0_6_ATLAS_FIELD.png'),timeout=25000)
 target=p.locator('#landmarks [data-branch="root"]');target.click(timeout=10000)
 assert p.locator('#branch-lens').is_visible();assert 'ORIGIN' in p.locator('#lens-name').inner_text();print('lens',p.locator('#lens-count').inner_text(),flush=True)
 assert p.locator('#lens-proof').is_enabled()
 p.screenshot(path=str(base/'evidence/M0_6_ATLAS_LENS.png'),timeout=25000)
 p.locator('#lens-proof').click();p.locator('[data-panel="events"]').wait_for(state='visible',timeout=8000)
 state=p.evaluate('window.__IXO_GPU_TEST__.getState()');assert state['mode']=='deck' and state['cursor']==initial['cursor']
 assert 'root' in p.locator('#proof').inner_text().lower();print('receipt',p.locator('#receipt').inner_text(),flush=True)
 p.wait_for_timeout(600);r=p.locator('#deck').bounding_box();assert r['x']==0 and r['width']==1280 and r['height']==800
 p.screenshot(path=str(base/'evidence/M0_6_ATLAS_DECK.png'),timeout=25000)
 p.locator('#deck-close').click();p.locator('#branch-lens').wait_for(state='visible',timeout=8000);p.locator('#lens-close').click();assert not p.locator('#branch-lens').is_visible()
 p.evaluate('window.__IXO_GPU_TEST__.go(0)');p.evaluate('window.__IXO_GPU_TEST__.select("root")');assert p.locator('#lens-proof').is_disabled();assert '0 recorded' in p.locator('#lens-count').inner_text()
 p.evaluate('window.__IXO_GPU_TEST__.go(72)');assert p.locator('#lens-proof').is_enabled()
 assert not errors,errors
 print('PASS: WebGL2 rendered; real branch click; contextual evidence; full overlay; same cursor; rewind removes evidence; restore; no JS errors',flush=True)
 b.close()
