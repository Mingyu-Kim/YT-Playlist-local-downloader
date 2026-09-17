"""Loopback-only local web app, packaged as a native executable."""
import argparse,json,os,secrets,sys,threading,webbrowser
from console_ui import Console
from platform_support import lock_instance,open_folder,choose_folder
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from socketserver import TCPServer
from pathlib import Path
from urllib.parse import urlparse


class LoopbackServer(ThreadingHTTPServer):
    def server_bind(self):
        # HTTPServer performs reverse DNS here, which can stall macOS startup.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def make_server(controller,root,token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,data,kind='application/json'):
            body=json.dumps(data,ensure_ascii=False).encode() if kind=='application/json' else data
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src https://www.youtube.com; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers();self.wfile.write(body)
        def allowed(self,api=False):
            expected=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=expected:return False
            origin=self.headers.get('Origin')
            if origin and origin!='http://'+expected:return False
            return not api or secrets.compare_digest(self.headers.get('X-App-Token',''),token)
        def do_GET(self):
            path=urlparse(self.path).path
            if not self.allowed(path.startswith('/api/')):self.reply(403,{'error':'Forbidden'});return
            try:
                if path=='/api/state':self.reply(200,controller.snapshot());return
                if path.startswith('/api/track/'):
                    import copy
                    with controller.lock:item=copy.deepcopy(next(t for t in controller.state['tracks'] if t['id']==path.rsplit('/',1)[-1]))
                    self.reply(200,item);return
                names={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
                if path not in names:self.reply(404,{'error':'Not found'});return
                name,kind=names[path];body=(root/'web'/name).read_bytes()
                if path=='/':body=body.replace(b'__APP_TOKEN__',token.encode())
                self.reply(200,body,kind)
            except Exception as exc:self.reply(400,{'error':str(exc)})
        def do_POST(self):
            if not self.allowed(True):self.reply(403,{'error':'Forbidden'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<0 or length>100000:raise ValueError('Request too large')
                data=json.loads(self.rfile.read(length) or b'{}')
                if not isinstance(data,dict):raise ValueError('Expected a JSON object')
                path=urlparse(self.path).path
                if path=='/api/analyze':controller.analyze(data)
                elif path=='/api/download':controller.download(data)
                elif path=='/api/edit':controller.edit(data)
                elif path=='/api/cancel':controller.cancel.set()
                elif path=='/api/options':
                    with controller.lock:
                        if controller.state['busy']:raise ValueError('An operation is running')
                        if 'romanize' in data:controller.state['romanize']=bool(data['romanize'])
                        if data.get('language') in ('en','ko'):controller.state['language']=data['language']
                        controller.save()
                elif path=='/api/folder':
                    if controller.state['busy']:raise ValueError('An operation is running')
                    folder=choose_folder()
                    self.reply(200,{'folder':folder});return
                elif path=='/api/open-output':
                    folder=Path(controller.state['output'])
                    if folder.is_dir():open_folder(folder)
                elif path=='/api/quit':
                    if controller.state['busy'] or controller.state.get('editing'):raise ValueError('Cancel the operation and wait before quitting')
                    controller.save();threading.Thread(target=self.server.shutdown,daemon=True).start()
                else:self.reply(404,{'error':'Not found'});return
                self.reply(200,{'ok':True})
            except Exception as exc:self.reply(400,{'error':str(exc)})
    server=LoopbackServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    return server


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-browser',action='store_true');parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--self-test',type=Path)
    args=parser.parse_args()
    if args.data_dir:os.environ['YT_PL_DATA']=str(args.data_dir.resolve())
    from common import DATA,ROOT,binary,atomic_json
    if sys.stdout is None:sys.stdout=(DATA/'application.log').open('a',encoding='utf-8')
    if sys.stderr is None:sys.stderr=sys.stdout
    from controller import Controller
    if args.self_test:
        import subprocess
        from text_rules import romanize
        from yt_dlp.extractor.youtube.jsc._builtin import ejs
        output={'romanization':romanize('안녕'),'node':subprocess.check_output([binary('node'),'--version'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).decode().strip(),
                'ffmpeg':subprocess.check_output([binary('ffmpeg'),'-version'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).decode().splitlines()[0],
                'web_assets':all((ROOT/'web'/n).is_file() for n in ('index.html','style.css','app.js')),'ejs':bool(ejs)}
        atomic_json(args.self_test,output);return
    # Keep one server per app-data directory, including when the EXE is double-clicked twice.
    lock=(DATA/'instance.lock').open('a+b')
    try:
        lock.seek(0,2)
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0)
        try:lock_instance(lock)
        except OSError:
            ready=DATA/'server.json'
            if ready.exists():
                existing=json.loads(ready.read_text(encoding='utf-8'))['url']
                print('Already running: '+existing,flush=True)
                if not args.no_browser:webbrowser.open(existing)
            return
        controller=Controller();token=secrets.token_urlsafe(32);server=make_server(controller,ROOT,token)
        url=f'http://127.0.0.1:{server.server_port}/'
        atomic_json(DATA/'server.json',{'url':url,'pid':os.getpid()})
        console=Console(controller,server,url,DATA)
        console.start()
        if not args.no_browser:webbrowser.open(url)
        try:server.serve_forever(poll_interval=.3)
        except KeyboardInterrupt:console.log.info('Ctrl+C received; stopping.')
        finally:
            controller.cancel.set()
            worker=controller.worker
            if worker and worker.is_alive():
                console.log.info('Cancelling active work. Waiting for the current network operation to finish...')
                try:
                    while worker.is_alive():worker.join(.3)
                except KeyboardInterrupt:
                    console.log.warning('Forced exit requested. The interrupted session can be resumed next time.')
            if not controller.edits_done.is_set():
                console.log.info('Waiting for the metadata edit to finish...')
                try:
                    while not controller.edits_done.wait(.3):pass
                except KeyboardInterrupt:console.log.warning('Forced exit during metadata edit.')
            server.server_close();(DATA/'server.json').unlink(missing_ok=True);controller.save()
            console.close()
    finally:lock.close()


if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    try:main()
    except Exception:
        import traceback
        text=traceback.format_exc()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0,text,'YT-PL-Downloader',16)
        except Exception:pass
        raise
