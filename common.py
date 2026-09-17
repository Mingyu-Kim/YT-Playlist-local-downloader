"""Shared paths and atomic state writes. No dependency on MusicManager."""
import json, os, sys, tempfile
from pathlib import Path

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
def default_data_dir():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'YT-PL-Downloader'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'YT-PL-Downloader'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'YT-PL-Downloader'


DATA = Path(os.environ.get('YT_PL_DATA', default_data_dir()))
DATA.mkdir(parents=True, exist_ok=True)


def atomic_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)


def binary(name):return str(ROOT/'tools'/(name+'.exe' if os.name=='nt' else name))
