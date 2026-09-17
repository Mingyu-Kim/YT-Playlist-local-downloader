import os,tempfile
from pathlib import Path
os.environ['YT_PL_DATA']=tempfile.mkdtemp(prefix='ytpl-tests-')
import pytest
from text_rules import romanize,english,display_tags,HANGUL,filename
from controller import playlist_id


def test_revised_romanization():
    assert romanize('안녕')=='Annyeong'
    assert romanize('안녕하세요')=='Annyeonghaseyo'
    assert not HANGUL.search(romanize('아이유 (IU) - 좋은 날 ㄱ'))
    assert romanize('IU - Hello')=='IU - Hello'


def test_english_preference():
    assert english('아이유 (IU)')=='IU'
    assert english('좋은 날')=='좋은 날'
    tags=display_tags({'TITLE':['안녕'],'LYRICS':['안녕하세요'],'COMPOSER':['김필']},True)
    assert not HANGUL.search(str(tags))
    assert filename({'TITLE':['A/B?'],'ARTIST':['Artist']})=='Artist - A_B_.mp3'


def test_url_validation():
    assert playlist_id('https://music.youtube.com/playlist?list=PLMTDok-Dtp0Q')=='PLMTDok-Dtp0Q'
    with pytest.raises(ValueError):playlist_id('http://127.0.0.1/playlist?list=PLMTDok-Dtp0Q')
    with pytest.raises(ValueError):playlist_id('https://youtube.com.attacker.test/playlist?list=PLMTDok-Dtp0Q')


def test_server_auth_and_security():
    import threading,requests
    from app import make_server
    from controller import Controller
    from common import ROOT
    server=make_server(Controller(),ROOT,'secret')
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    url=f'http://127.0.0.1:{server.server_port}'
    try:
        assert requests.get(url).status_code==200
        assert requests.get(url+'/api/state').status_code==403
        assert requests.get(url+'/api/state',headers={'X-App-Token':'secret'}).status_code==200
        assert requests.post(url+'/api/cancel',json={},headers={'X-App-Token':'secret','Origin':'https://evil.test'}).status_code==403
        assert requests.get(url,headers={'Host':'evil.test'}).status_code==403
        assert requests.get(url+'/../requirements.txt').status_code==404
    finally:server.shutdown();server.server_close()


def test_mp3_tags_and_romanization(tmp_path):
    import subprocess
    from downloads import write_tags
    from common import binary
    from mutagen.mp3 import MP3
    p=tmp_path/'test.mp3'
    subprocess.run([binary('ffmpeg'),'-v','error','-f','lavfi','-i','sine=duration=0.1','-c:a','libmp3lame','-b:a','320k',str(p)],check=True)
    tags=display_tags({'TITLE':['안녕'],'ARTIST':['아이유'],'LYRICS':['안녕하세요'],'DATE':['2020'],'TRACKNUMBER':['2'],'TRACKTOTAL':['5']},True)
    write_tags(p,tags)
    audio=MP3(p)
    assert audio.tags.version==(2,3,0)
    assert audio.tags['TIT2'].text==['Annyeong']
    assert not HANGUL.search(str(audio.tags))
    assert audio.tags['TRCK'].text==['2/5']


def test_inventory_detects_modified_files(tmp_path):
    from downloads import Inventory
    inventory=Inventory(tmp_path/'files.sqlite');p=tmp_path/'song.mp3';p.write_bytes(b'abc')
    inventory.save(tmp_path,'id',p,'profile');assert inventory.find(tmp_path,'id')
    p.write_bytes(b'changed');assert inventory.find(tmp_path,'id') is None


def test_version_mismatch_needs_review(monkeypatch):
    from metadata import Metadata
    m=Metadata()
    monkeypatch.setattr(m,'mb',lambda *a,**k:{'recordings':[{'id':'a','title':'Song (inst.)','length':200000,'artist-credit':[{'name':'Artist'}]}]})
    candidates=m.search({'raw_title':'Song','raw_artists':['Artist'],'duration':200})
    assert not candidates or candidates[0]['notes']


def test_repeated_download_reuses_audio(tmp_path,monkeypatch):
    import threading,subprocess
    import downloads
    from common import binary
    from text_rules import display_tags
    item={'id':'abcdefghijk','tags':{'TITLE':['Song'],'ARTIST':['Artist']},'warnings':[]}
    def fake_extract(self,url,download):
        p=Path(self.params['outtmpl']['default'].replace('%(ext)s','mp3'))
        subprocess.run([binary('ffmpeg'),'-v','error','-f','lavfi','-i','sine=duration=0.1','-c:a','libmp3lame','-b:a','320k',str(p)],check=True)
        return {'id':item['id'],'ext':'mp3'}
    monkeypatch.setattr(downloads.YoutubeDL,'extract_info',fake_extract)
    monkeypatch.setattr(downloads.YoutubeDL,'prepare_filename',lambda self,info:self.params['outtmpl']['default'].replace('%(ext)s','mp3'))
    inventory=downloads.Inventory(tmp_path/'inventory.sqlite')
    first=downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,inventory)
    def forbidden(*a,**k):raise AssertionError('Should not fetch audio again')
    monkeypatch.setattr(downloads.YoutubeDL,'extract_info',forbidden)
    second=downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,inventory)
    assert second['status']=='reused' and second['file']==first['file']
    assert len(list(tmp_path.glob('*.mp3')))==1


def test_metadata_search_must_finish_before_download():
    from controller import Controller
    controller=Controller()
    controller.state['tracks']=[{'id':'abcdefghijk','status':'review','tags':{'TITLE':['Song'],'ARTIST':['Artist']}}]
    with pytest.raises(ValueError,match='Resolve'):controller.download({})


def test_english_alias_used_for_recording_and_artists(monkeypatch):
    from metadata import Metadata
    m=Metadata()
    recording={'id':'r','title':'안녕','aliases':[{'name':'Hello','locale':'en'}],'artist-credit':[{'artist':{'id':'a','name':'아이유','aliases':[{'locale':'en','name':'IU'}]}}],'releases':[]}
    monkeypatch.setattr(m,'mb',lambda *a,**k:recording)
    item={'tags':{'TITLE':['안녕'],'ARTIST':['아이유']},'warnings':[]}
    result=m.resolve(item,'r')
    assert result['tags']['TITLE']==['Hello'] and result['tags']['ARTIST']==['IU']


def test_console_commands(tmp_path,monkeypatch):
    import threading
    from types import SimpleNamespace
    from console_ui import Console
    opened=[];stopped=[]
    monkeypatch.setattr('console_ui.webbrowser.open',opened.append)
    controller=SimpleNamespace(lock=threading.RLock(),cancel=threading.Event(),state={'phase':'idle','busy':False,'progress':0,'tracks':[],'message':''})
    server=SimpleNamespace(shutdown=lambda:stopped.append(True))
    console=Console(controller,server,'http://127.0.0.1:1234/',tmp_path)
    console.monitor.start()
    try:
        console.command('o');console.command('s');console.command('q');console.command('q')
        assert opened==['http://127.0.0.1:1234/']
        assert stopped==[True] and controller.cancel.is_set()
    finally:console.close()
    assert 'Server stopped' in (tmp_path/'application.log').read_text(encoding='utf-8')


def test_console_server_lifecycle(tmp_path):
    import subprocess,sys,time,json
    root=Path(__file__).resolve().parents[1]
    proc=subprocess.Popen([sys.executable,str(root/'app.py'),'--no-browser','--data-dir',str(tmp_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    try:
        deadline=time.monotonic()+30
        while not (tmp_path/'server.json').exists():
            if proc.poll() is not None:raise AssertionError(proc.stdout.read())
            if time.monotonic()>deadline:raise AssertionError('Server startup timed out')
            time.sleep(.1)
        url=json.loads((tmp_path/'server.json').read_text())['url']
        output,_=proc.communicate('s\nq\n',timeout=30)
        assert proc.returncode==0,output
        assert url in output and 'Server stopped' in output and 'idle' in output
        assert not (tmp_path/'server.json').exists()
    finally:
        if proc.poll() is None:proc.kill();proc.wait()


def test_review_during_scan_preserves_edits(tmp_path,monkeypatch):
    import threading
    import controller as module
    entered=threading.Event();release=threading.Event()
    class FakeMetadata:
        def __init__(self):self.yt=self
        def get_playlist(self,*a,**k):return {'title':'Test','tracks':[{'videoId':'abcdefghijk'},{'videoId':'lmnopqrstuv'}]}
        def youtube(self,t):
            if t['videoId']=='lmnopqrstuv':
                entered.set();assert release.wait(5)
            return {'id':t['videoId'],'tags':{'TITLE':['Original'],'ARTIST':['Artist']},'status':'review','warnings':[],'candidates':[]}
        def enrich(self,item):return item
    monkeypatch.setattr(module,'Metadata',FakeMetadata)
    c=module.Controller()
    c.analyze({'playlist':'https://music.youtube.com/playlist?list=PLMTDok-Dtp0Q','output':str(tmp_path)})
    try:
        assert entered.wait(5)
        assert c.state['busy'] and len(c.state['tracks'])==1
        c.edit({'id':'abcdefghijk','tags':{'TITLE':'Reviewed'}})
        assert c.state['busy'] and c.state['phase']=='analyzing'
        with pytest.raises(ValueError):c.download({})
    finally:release.set();c.worker.join(5)
    assert c.state['tracks'][0]['tags']['TITLE']==['Reviewed']
    assert c.state['tracks'][0]['status']=='ready' and len(c.state['tracks'])==2


def test_candidate_edit_blocks_download_and_commits_atomically(monkeypatch):
    import threading
    import controller as module
    entered=threading.Event();release=threading.Event();errors=[]
    class FakeMetadata:
        def resolve(self,item,candidate):
            entered.set();assert release.wait(5)
            item['tags']['TITLE']=['Matched'];return item
    monkeypatch.setattr(module,'Metadata',FakeMetadata)
    c=module.Controller();c.state.update(busy=False,phase='review',tracks=[{'id':'abcdefghijk','tags':{'TITLE':['Original'],'ARTIST':['Artist']},'status':'ready','candidates':[{'id':'match'}]}])
    def edit():
        try:c.edit({'id':'abcdefghijk','candidate':'match'})
        except Exception as e:errors.append(e)
    worker=threading.Thread(target=edit);worker.start()
    try:
        assert entered.wait(5)
        assert c.state['tracks'][0]['tags']['TITLE']==['Original']
        with pytest.raises(ValueError):c.download({})
        with pytest.raises(ValueError):c.edit({'id':'abcdefghijk','skip':True})
    finally:release.set();worker.join(5)
    assert not errors and c.edits_done.is_set() and not c.state['editing']
    assert c.state['tracks'][0]['tags']['TITLE']==['Matched']
    with pytest.raises(ValueError):c.edit({'id':'abcdefghijk','tags':{'TITLE':''}})
    assert c.state['tracks'][0]['tags']['TITLE']==['Matched']


def test_portable_tags_reuse_with_empty_database_and_renamed_file(tmp_path,monkeypatch):
    import threading,subprocess,shutil
    import downloads
    from common import binary
    from mutagen.mp3 import MP3
    def no_network(*a,**k):raise AssertionError('Existing tagged audio must not be downloaded')
    output=tmp_path/'music';output.mkdir()
    old=output/'renamed by user.mp3'
    subprocess.run([binary('ffmpeg'),'-v','error','-f','lavfi','-i','sine=duration=0.1','-c:a','libmp3lame','-b:a','320k',str(old)],check=True)
    # Older app files already contain YOUTUBE_ID but no portable profile marker.
    downloads.write_tags(old,{'TITLE':['Old title'],'ARTIST':['Artist'],'YOUTUBE_ID':['abcdefghijk']})
    monkeypatch.setattr(downloads.YoutubeDL,'extract_info',no_network)
    item={'id':'abcdefghijk','tags':{'TITLE':['Song'],'ARTIST':['Artist']},'warnings':[]}
    first=downloads.download(item,output,False,threading.Event(),lambda n:None,downloads.Inventory(tmp_path/'fresh.sqlite'))
    assert first['status']=='reused'
    tags=MP3(first['file']).tags
    assert tags['TXXX:YOUTUBE_ID'].text==['abcdefghijk']
    assert tags['WOAS'].url=='https://www.youtube.com/watch?v=abcdefghijk'
    assert tags['TXXX:YOUTUBE_MUSIC_URL'].text==['https://music.youtube.com/watch?v=abcdefghijk']
    assert len(tags['TXXX:YTPL_PROFILE'].text[0])==64
    moved=tmp_path/'moved';moved.mkdir();renamed=moved/'custom filename.mp3'
    shutil.copy2(first['file'],renamed)
    original_digest=downloads.digest(renamed)
    # A different directory/database (e.g. another computer) recovers directly from tags.
    second=downloads.download(item,moved,False,threading.Event(),lambda n:None,downloads.Inventory(tmp_path/'another.sqlite'))
    assert second['status']=='reused' and Path(second['file'])==renamed
    assert downloads.digest(renamed)==original_digest and len(list(moved.glob('*.mp3')))==1


def test_scan_legacy_source_urls_and_invalid_files(tmp_path):
    import subprocess,threading
    import downloads
    from common import binary
    from mutagen.id3 import ID3,TXXX
    output=tmp_path/'music';output.mkdir();song=output/'legacy.mp3'
    subprocess.run([binary('ffmpeg'),'-v','error','-f','lavfi','-i','sine=duration=0.1','-c:a','libmp3lame','-b:a','320k',str(song)],check=True)
    downloads.write_tags(song,{'SOURCE':['https://music.youtube.com/watch?v=abcdefghijk'],'TITLE':['Song']})
    (output/'broken.mp3').write_bytes(b'not audio')
    inventory=downloads.Inventory(tmp_path/'scan.sqlite')
    assert inventory.scan(output)==1
    assert inventory.find(output,'abcdefghijk')
    assert inventory.find(output,'lmnopqrstuv') is None
    tags=ID3();tags.add(TXXX(desc='SOURCE',text=['https://youtube.com.attacker.test/watch?v=abcdefghijk']))
    assert downloads.youtube_id(tags) is None
    tags.add(TXXX(desc='YOUTUBE_ID',text=['abcdefghijk','lmnopqrstuv']))
    assert downloads.youtube_id(tags) is None
    stop=threading.Event();stop.set()
    with pytest.raises(downloads.Cancelled):downloads.Inventory(tmp_path/'cancel.sqlite').scan(output,stop)
