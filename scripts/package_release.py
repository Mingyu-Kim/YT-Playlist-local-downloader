"""Create native binary/source ZIPs with per-file checksums and build provenance."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import zipfile
from prepare_tools import ROOT, VENDOR, target_name


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def zip_tree(folder,target):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():archive.write(path,path.relative_to(folder))


def main():
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise RuntimeError('Commit all source changes before packaging a release')
    version=(ROOT/'VERSION').read_text().strip();target=target_name()
    name=f'YT-PL-Downloader-{version}-{target}'
    out=ROOT/'release';out.mkdir(exist_ok=True)
    source_records=json.loads((VENDOR/'sources.json').read_text())
    # Refuse a release made with an opaque external FFmpeg binary.
    if not (ROOT/'tools/ffmpeg-build.txt').exists():raise RuntimeError('Build FFmpeg from the pinned sources before packaging')
    with tempfile.TemporaryDirectory(prefix='ytpl-package-') as temp:
        temp=Path(temp);bundle=temp/'binary';bundle.mkdir()
        exe='YT-PL-Downloader.exe' if os.name=='nt' else 'YT-PL-Downloader'
        shutil.copy2(ROOT/'dist'/exe,bundle/exe)
        for doc in ('LICENSE','README.md','README.ko.md','THIRD_PARTY_NOTICES.md','CHANGELOG.md','VERSION'):
            shutil.copy2(ROOT/doc,bundle/doc)
        shutil.copytree(ROOT/'build/licenses',bundle/'licenses')
        shutil.copy2(ROOT/'build/dependencies.json',bundle/'dependencies.json')
        shutil.copy2(ROOT/'tools/ffmpeg-build.txt',bundle/'ffmpeg-build.txt')
        if os.name!='nt':
            launcher=bundle/'Launch.command'
            launcher.write_text('#!/bin/sh\ncd "$(dirname "$0")"\n./YT-PL-Downloader\nstatus=$?\nif [ "$status" -ne 0 ]; then printf "App exited with error. Press Enter to close."; read answer; fi\nexit "$status"\n')
            launcher.chmod(0o755);(bundle/exe).chmod(0o755)
        provenance={'version':version,'target':target,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':platform.python_version(),'signed':False,'notarized':False}
        (bundle/'build-info.json').write_text(json.dumps(provenance,indent=2))
        (bundle/'SHA256SUMS.txt').write_text(''.join(f'{digest(p)}  {p.relative_to(bundle).as_posix()}\n' for p in sorted(bundle.rglob('*')) if p.is_file()))
        zip_tree(bundle,out/(name+'.zip'))
        sources=temp/'sources';sources.mkdir()
        subprocess.run(['git','archive','--format=tar','-o',str(sources/'project-source.tar'),'HEAD'],cwd=ROOT,check=True)
        shutil.copy2(VENDOR/'sources.json',sources/'sources.json')
        for record in source_records:
            file=record['file'];path=VENDOR/file
            if not path.exists():path=VENDOR/'sources'/file
            if digest(path)!=record['sha256']:raise RuntimeError('Source checksum changed: '+file)
            shutil.copy2(path,sources/path.name)
        (sources/'README.txt').write_text('Corresponding sources for '+name+'.\nExtract project-source.tar and follow docs/RELEASING.md.\nArchive checksums and upstream URLs are in sources.json. No upstream source modifications were applied.\n')
        zip_tree(sources,out/(name+'-sources.zip'))
    artifacts=[out/(name+'.zip'),out/(name+'-sources.zip')]
    (out/(name+'.sha256')).write_text(''.join(f'{digest(p)}  {p.name}\n' for p in artifacts))
    print('Created '+name+' binary, corresponding sources and checksums')


if __name__=='__main__':main()
