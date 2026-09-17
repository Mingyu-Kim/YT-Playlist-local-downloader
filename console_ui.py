"""Visible console controls and bounded persistent application logs."""
import logging
from logging.handlers import RotatingFileHandler
import sys
import threading
import webbrowser


class Console:
    def __init__(self, controller, server, url, data):
        self.controller, self.server, self.url = controller, server, url
        self.stopped = threading.Event()
        self.quitting = threading.Event()
        self.log = logging.getLogger('ytpl')
        self.log.setLevel(logging.INFO)
        self.log.propagate = False
        self.handlers = [logging.StreamHandler(sys.stdout),
                         RotatingFileHandler(data / 'application.log', maxBytes=2_000_000,
                                             backupCount=2, encoding='utf-8')]
        for handler in self.handlers:
            handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s  %(message)s', '%H:%M:%S'))
            self.log.addHandler(handler)
        self.monitor = threading.Thread(target=self.watch, daemon=True)

    def status(self):
        with self.controller.lock:
            s = self.controller.state
            return f"{s['phase']} | {s.get('progress', 0)}% | {len(s['tracks'])} songs | {s.get('message', '')}"

    def start(self):
        self.log.info('YT-PL-Downloader is running: %s', self.url)
        self.log.info('Close/reopen your browser freely. Keep this terminal open while using the app.')
        self.log.info('Commands (press Enter after typing): o = open browser, s = status, q = quit. Ctrl+C also quits.')
        self.log.info('명령: o + Enter = 브라우저 열기, s = 상태, q = 종료. Ctrl+C = 종료.')
        self.log.info('Log file: %s', self.handlers[1].baseFilename)
        self.monitor.start()
        threading.Thread(target=self.read_commands, daemon=True).start()

    def command(self, command):
        command = command.strip().lower()
        if command in ('o', 'open'):
            self.log.info('Opening %s', self.url)
            webbrowser.open(self.url)
        elif command in ('s', 'status'):
            self.log.info('%s | URL: %s', self.status(), self.url)
        elif command in ('q', 'quit', 'exit'):
            if not self.quitting.is_set():
                self.quitting.set()
                self.log.info('Shutdown requested; cancelling active work...')
                self.controller.cancel.set()
                self.server.shutdown()
        elif command:
            self.log.info('Use o (open browser), s (status), or q (quit), then Enter.')

    def read_commands(self):
        while not self.stopped.is_set():
            try:
                line = sys.stdin.readline()
                if not line:return
                self.command(line)
            except (OSError, ValueError, AttributeError):return

    def watch(self):
        previous = None
        tracks = {}
        while not self.stopped.is_set():
            with self.controller.lock:
                s = self.controller.state
                key = (s['phase'], s['busy'], int(s.get('progress', 0)) // 10, s.get('message', ''))
                current = [(t['id'], t.get('status'), ', '.join(t.get('tags', {}).get('TITLE', [t['id']])),
                            t.get('error', ''), tuple(t.get('warnings', []))) for t in s['tracks']]
            if key != previous:
                self.log.info(self.status())
                previous = key
            for tid, status, title, error, warnings in current:
                value = (status, error, warnings)
                if tracks.get(tid) != value:
                    self.log.log(logging.ERROR if error else logging.INFO, '%s: %s%s', status, title, ' | '+error if error else '')
                    old_warnings = tracks.get(tid, (None, None, ()))[2]
                    for warning in warnings:
                        if warning not in old_warnings:self.log.warning('%s: %s', title, warning)
                    tracks[tid] = value
            self.stopped.wait(.5)

    def close(self):
        self.stopped.set()
        self.monitor.join(timeout=2)
        self.log.info('Server stopped. You can close this terminal.')
        for handler in self.handlers:
            self.log.removeHandler(handler)
            handler.close()
