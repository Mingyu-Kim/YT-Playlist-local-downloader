"""Offline native executable self-test, HTTP lifecycle and shutdown."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    exe = ROOT / 'dist' / ('YT-PL-Downloader.exe' if os.name == 'nt' else 'YT-PL-Downloader')
    with tempfile.TemporaryDirectory(prefix='ytpl-release-') as temp:
        data = Path(temp); report = data / 'self-test.json'
        subprocess.run([str(exe),'--data-dir',str(data),'--self-test',str(report)],check=True,timeout=60)
        results = json.loads(report.read_text(encoding='utf-8'))
        assert results['romanization']=='Annyeong' and results['web_assets'] and results['ejs']
        proc = subprocess.Popen([str(exe),'--no-browser','--data-dir',str(data)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+60
            while not (data/'server.json').exists():
                if proc.poll() is not None:raise RuntimeError('Server exited during startup')
                if time.monotonic()>deadline:raise TimeoutError('Startup timed out')
                time.sleep(.1)
            url = json.loads((data/'server.json').read_text())['url']
            with urllib.request.urlopen(url,timeout=5) as response:assert response.status==200
            output,_ = proc.communicate(b's\nq\n',timeout=30)
            assert proc.returncode==0 and b'Server stopped' in output
            assert not (data/'server.json').exists()
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
    print('Native executable smoke test passed')


if __name__ == '__main__':main()
