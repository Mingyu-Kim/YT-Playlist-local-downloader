"""Stage corresponding sources for the native release's installed dependencies."""
from concurrent.futures import ThreadPoolExecutor
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import urllib.request
from prepare_tools import ROOT, VENDOR, fetch, pinned


def main():
    out = VENDOR / 'sources'; out.mkdir(parents=True, exist_ok=True)
    records = []
    skip = {'pip','ruff','pytest','pluggy','iniconfig','pygments','imageio-ffmpeg'}
    def source(dist):
        name,version = dist.metadata['Name'],dist.version
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=60) as response:
            data = json.load(response)
        info = next((f for f in data['urls'] if f['packagetype']=='sdist'), None)
        if info is None:raise RuntimeError(f'No source distribution for {name}=={version}; review before releasing')
        file = fetch(info['url'], out / info['filename'], info['digests']['sha256'])
        return {'name':name,'version':version,'file':file.name,'url':info['url'],'sha256':info['digests']['sha256']}
    distributions = [d for d in metadata.distributions() if d.metadata['Name'].lower() not in skip]
    with ThreadPoolExecutor(max_workers=4) as pool:records.extend(pool.map(source, distributions))
    for name in ('node-v24.12.0.tar.xz','ffmpeg-7.1.2.tar.xz','lame-3.100.tar.gz','Python-3.14.0.tar.xz'):
        path = pinned(name)
        from prepare_tools import LOCK
        records.append({'name':name,'file':str(path.relative_to(VENDOR)),**LOCK['files'][name]})
    if platform.python_version() != '3.14.0':raise RuntimeError('Release Python must match pinned Python 3.14.0 source')
    (VENDOR/'sources.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(f'Staged {len(records)} corresponding source archives')


if __name__ == '__main__':main()
