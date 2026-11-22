"""Optional Playwright smoke test of the real clickable HERMES interface.

Requires: pip install playwright + a Chromium browser. Not run by the default
stdlib unittest suite, so the Windows installer has no extra dependency.
"""
from __future__ import annotations

import tempfile
import threading
import shutil
import os
from pathlib import Path

from funnel.common import init_data
from funnel.hub import FunnelServer


def run():
    from playwright.sync_api import sync_playwright, expect

    with tempfile.TemporaryDirectory(prefix='hermes-ui-smoke-') as folder:
        member, other, _third, _fourth, _bot, admin = init_data(Path(folder))
        server = FunnelServer('127.0.0.1', 0, folder)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with sync_playwright() as playwright:
                browser_options = {'headless': True}
                installed = (shutil.which('chromium') or shutil.which('chromium-browser')
                             or shutil.which('google-chrome'))
                if installed:
                    browser_options['executable_path'] = installed
                if os.name != 'nt':
                    browser_options['args'] = ['--no-sandbox']
                browser = playwright.chromium.launch(**browser_options)
                try:
                    url = f'http://127.0.0.1:{server.server_port}/'

                    def connected(token):
                        context = browser.new_context()
                        page = context.new_page()
                        page.goto(url)
                        page.locator('#token').fill(token)
                        page.locator('#connect').click()
                        expect(page.locator('#who')).to_contain_text('Authenticated:', timeout=10000)
                        page.on('dialog', lambda dialog: dialog.accept())
                        return context, page

                    owner_ctx, owner = connected(member[2])
                    owner.set_input_files('#file-select', {
                        'name': 'test_simulation.md', 'mimeType': 'text/markdown',
                        'buffer': b'# Demo\nAuthorized synthetic input only.\n',
                    })
                    owner.locator('#file-project').fill('ixo')
                    owner.locator('#file-upload').click()
                    expect(owner.locator('#file-progress')).to_contain_text(
                        'PRIVATE upload verified', timeout=15000)
                    expect(owner.locator('#items')).to_contain_text('private')

                    other_ctx, peer = connected(other[2])
                    expect(peer.locator('#items')).not_to_contain_text('test_simulation.md')
                    owner.locator('#items button').filter(has_text='Share').click()
                    expect(owner.locator('#items')).to_contain_text('team')
                    peer.locator('#refresh').click()
                    expect(peer.locator('#items')).to_contain_text('test_simulation.md')

                    owner.locator('#note-title').fill('Synthetic finding')
                    owner.locator('#note-body').fill('For review only.')
                    owner.locator('#add-note').click()
                    expect(owner.locator('#note-list')).to_contain_text('Synthetic finding')
                    owner.locator('#note-list button').filter(has_text='Submit').click()
                    expect(owner.locator('#note-list')).to_contain_text('submitted')
                    peer.locator('#refresh').click()
                    expect(peer.locator('#note-list')).not_to_contain_text('Synthetic finding')

                    admin_ctx, operator = connected(admin[2])
                    expect(operator.locator('#note-list')).to_contain_text('Synthetic finding')
                    operator.locator('#note-list button').filter(has_text='approve').click()
                    expect(operator.locator('#note-list')).to_contain_text('approved')
                    peer.locator('#refresh').click()
                    expect(peer.locator('#note-list')).to_contain_text('Synthetic finding')
                    print('BROWSER SMOKE PASS: private upload -> share -> note -> review -> team visibility')
                    admin_ctx.close()
                    other_ctx.close()
                    owner_ctx.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == '__main__':
    run()
