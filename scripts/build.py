"""Build a native console executable. Run on each target OS/architecture."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from prepare_tools import ROOT, target_name


def main():
    target_name()
    os.chdir(ROOT)
    suffix = '.exe' if os.name == 'nt' else ''
    for tool in ('ffmpeg','node'):
        if not (ROOT / 'tools' / (tool + suffix)).is_file():raise SystemExit('Prepare tools first; see docs/RELEASING.md')
    subprocess.run([sys.executable, 'scripts/collect_licenses.py'], check=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--console', '--name', 'YT-PL-Downloader', '--distpath', 'dist', '--workpath', 'build/pyinstaller']
    for source,dest in [('web','web'),('build/licenses','licenses'),('LICENSE','.'),('README.md','.'),('README.ko.md','.'),('THIRD_PARTY_NOTICES.md','.'),('VERSION','.')]:
        command += ['--add-data', source + os.pathsep + dest]
    for tool in ('ffmpeg','node'):
        command += ['--add-binary', 'tools/' + tool + suffix + os.pathsep + 'tools']
    for package in ('ytmusicapi','korean_romanizer','yt_dlp_ejs','yt_dlp'):
        command += ['--collect-all',package]
    command += ['--copy-metadata','requests','--copy-metadata','certifi','app.py']
    subprocess.run(command, check=True)
    if os.name == 'nt':shutil.copy2(ROOT/'dist/YT-PL-Downloader.exe', ROOT/'YT-PL-Downloader.exe')


if __name__ == '__main__':main()
