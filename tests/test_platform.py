import io
from pathlib import Path
import pytest


def test_mac_data_directory(monkeypatch):
    import common
    monkeypatch.setattr(common.sys, 'platform', 'darwin')
    assert common.default_data_dir() == Path.home() / 'Library' / 'Application Support' / 'YT-PL-Downloader'


def test_mac_folder_operations(monkeypatch):
    import platform_support as platform
    from types import SimpleNamespace
    calls=[]
    monkeypatch.setattr(platform.sys, 'platform', 'darwin')
    monkeypatch.setattr(platform.subprocess, 'Popen', lambda args:calls.append(args))
    platform.open_folder(Path('/tmp/Music folder'))
    assert calls == [['open',str(Path('/tmp/Music folder'))]]
    monkeypatch.setattr(platform.subprocess, 'run', lambda *a,**k:SimpleNamespace(returncode=0,stdout='/tmp/Music folder/\n'))
    assert platform.choose_folder() == '/tmp/Music folder/'
    monkeypatch.setattr(platform.subprocess, 'run', lambda *a,**k:SimpleNamespace(returncode=1,stderr='User canceled. (-128)'))
    assert platform.choose_folder() == ''


def test_checksum_failure_preserves_existing_tool(tmp_path,monkeypatch):
    from scripts import prepare_tools
    file=tmp_path/'node';file.write_bytes(b'previous binary')
    monkeypatch.setattr(prepare_tools.urllib.request,'urlopen',lambda *a,**k:io.BytesIO(b'tampered archive'))
    with pytest.raises(RuntimeError,match='Checksum mismatch'):
        prepare_tools.fetch('https://example.test/tool',file,'0'*64)
    assert file.read_bytes()==b'previous binary'
    assert not file.with_suffix('.tmp').exists()
