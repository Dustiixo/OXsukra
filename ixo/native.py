"""Optional native desktop host. Requires PySide6 with QtWebEngineWidgets.
This wrapper runs the exact same local IXO/AIXO Python backend as browser mode.
No Qt requirement is imposed on the portable default.
"""
from __future__ import annotations
import sys,threading
from pathlib import Path
from .runtime import IXORuntime
from .server import IXOServer
from aixo.engine import AIXOEngine

def main():
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QApplication,QMainWindow
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        raise SystemExit('Native window needs optional PySide6 QtWebEngine: pip install PySide6. Default launch: python -m ixo')
    db=Path.home()/'.ixo'/'ixo.sqlite3'
    ixo=IXORuntime(db);aixo=AIXOEngine(db.with_name('aixo.sqlite3'))
    server=IXOServer(('127.0.0.1',0),ixo,aixo)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    app=QApplication(sys.argv)
    window=QMainWindow();window.setWindowTitle('IXO · Spatial Application')
    view=QWebEngineView();window.setCentralWidget(view)
    view.load(QUrl(f'http://127.0.0.1:{server.server_port}/?token={server.token}'))
    window.resize(1600,950);window.show()
    try:return app.exec()
    finally:
        server.shutdown();server.server_close();worker.join(timeout=3);ixo.close();aixo.close()
if __name__=='__main__':sys.exit(main())
