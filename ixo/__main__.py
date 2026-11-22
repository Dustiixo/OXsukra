import argparse
from pathlib import Path
from .server import serve

def main():
    p=argparse.ArgumentParser(description='IXO local application runtime')
    p.add_argument('--data',default=str(Path.home()/'.ixo'/'ixo.sqlite3'))
    p.add_argument('--port',type=int,default=0)
    p.add_argument('--no-browser',action='store_true')
    args=p.parse_args()
    serve(args.data,args.port,not args.no_browser)
if __name__=='__main__':main()
