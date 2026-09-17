"""Fetch checksum-pinned Node and audio-tool sources; no system installation."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / '.vendor'
LOCK = json.loads((ROOT / 'scripts/tools.lock.json').read_text())


def fetch(url, target, sha256):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == sha256:
        return target
    temp = target.with_suffix(target.suffix + '.tmp')
    try:
        with urllib.request.urlopen(url, timeout=180) as response, temp.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        if hashlib.sha256(temp.read_bytes()).hexdigest() != sha256:
            raise RuntimeError(f'Checksum mismatch: {target.name}')
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def pinned(name):
    info = LOCK['files'][name]
    return fetch(info['url'], VENDOR / name, info['sha256'])


def target_name():
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('arm64', 'aarch64') else 'x64'
    if os.name == 'nt':
        if arch != 'x64':raise RuntimeError('Windows ARM release is not supported')
        return 'windows-x64'
    if platform.system() == 'Darwin':return 'macos-' + arch
    raise RuntimeError('Build on Windows x64 or macOS arm64/x64')


def main():
    target = target_name()
    node_target = {'windows-x64':'win-x64.zip', 'macos-arm64':'darwin-arm64.tar.gz', 'macos-x64':'darwin-x64.tar.gz'}[target]
    name = 'node-v' + LOCK['node_version'] + '-' + node_target
    archive = pinned(name)
    tools = ROOT / 'tools'; tools.mkdir(exist_ok=True)
    notices = ROOT / 'build/licenses/node'; notices.mkdir(parents=True, exist_ok=True)
    if name.endswith('.zip'):
        with zipfile.ZipFile(archive) as z:
            prefix = name.removesuffix('.zip') + '/'
            (tools / 'node.exe').write_bytes(z.read(prefix + 'node.exe'))
            (notices / 'LICENSE').write_bytes(z.read(prefix + 'LICENSE'))
    else:
        with tarfile.open(archive) as z:
            prefix = name.removesuffix('.tar.gz') + '/'
            (tools / 'node').write_bytes(z.extractfile(prefix + 'bin/node').read())
            (notices / 'LICENSE').write_bytes(z.extractfile(prefix + 'LICENSE').read())
        (tools / 'node').chmod(0o755)
    for name in ('ffmpeg-7.1.2.tar.xz', 'lame-3.100.tar.gz'):
        archive = pinned(name)
        destination = VENDOR / name.split('.tar')[0]
        if not destination.exists():
            with tarfile.open(archive) as z:z.extractall(VENDOR, filter='data')
    print('Verified native Node and FFmpeg/LAME sources for ' + target)


if __name__ == '__main__':main()
