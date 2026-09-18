import threading,subprocess
from pathlib import Path
import pytest
import downloads
from text_rules import relative_path,validate_layout,display_tags
from common import binary


def audio_file(path,tags):
    path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([binary('ffmpeg'),'-v','error','-f','lavfi','-i','sine=duration=0.1','-c:a','libmp3lame','-b:a','320k',str(path)],check=True)
    downloads.write_tags(path,tags)
    return path


def test_layout():
    tags={'TITLE':['Song'],'ARTIST':['Artist'],'DATE':['2017-01-02']}
    assert relative_path(tags,'{title}','artist')==Path('Artist/Song.mp3')
    for year in ('1991','2000','2019','2026'):
        tags['DATE']=[year]
        assert relative_path(tags,'{title}','decade')==Path(f'{int(year)//10*10}s/Song.mp3')
    tags['DATE']=[]
    assert str(relative_path(tags,'{title}','decade')).startswith('Unknown decade')
    tags['ARTIST']=['../CON'];tags['TITLE']=['NUL.txt']
    assert '..' not in relative_path(tags,'{title}','artist').parts
    assert relative_path(tags,'{title}').name=='_NUL.txt.mp3'
    assert not relative_path(display_tags({'TITLE':['안녕']},True),'{title}').name.startswith('안녕')
    for pattern in ('../{title}','{year}','{title!r}','{title:20}',''):
        with pytest.raises(ValueError):validate_layout(pattern)


def test_recursive_local_edit_and_database_loss(tmp_path,monkeypatch):
    monkeypatch.setattr(downloads.YoutubeDL,'extract_info',lambda *a,**k:pytest.fail('Network called'))
    old=audio_file(tmp_path/'old'/'song.mp3',{'TITLE':['Song'],'ARTIST':['Artist'],'DATE':['2003'],'YOUTUBE_ID':['abcdefghijk'],'LYRICS':['Words']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    item['tags']['TITLE']=['New title']
    result=downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,downloads.Inventory(tmp_path/'one.sqlite'),'{title}','decade')
    target=tmp_path/'2000s'/'New title.mp3'
    assert Path(result['file'])==target and not old.exists()
    assert downloads.MP3(target).tags.getall('USLT')[0].text=='Words'
    assert downloads.youtube_id(downloads.MP3(target).tags)=='abcdefghijk'
    inventory=downloads.Inventory(tmp_path/'empty.sqlite')
    assert inventory.scan(tmp_path)==1 and inventory.find(tmp_path,'abcdefghijk')
    # Repeat applying a local edit uses the new path/digest.
    item.update(result)
    downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,inventory,'{title}','none')
    assert (tmp_path/'New title.mp3').exists()


def test_untagged_source_collision_and_changed_local_file(tmp_path):
    old=audio_file(tmp_path/'input.mp3',{'TITLE':['Song'],'ARTIST':['Artist']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    occupied=tmp_path/'Artist'/'Song.mp3';occupied.parent.mkdir();occupied.write_bytes(b'unrelated')
    result=downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,downloads.Inventory(tmp_path/'db.sqlite'),'{title}','artist')
    assert occupied.read_bytes()==b'unrelated'
    assert not old.exists() and Path(result['file'])!=occupied
    assert downloads.youtube_id(downloads.MP3(result['file']).tags) is None
    item.update(result)
    with Path(result['file']).open('ab') as f:f.write(b'changed')
    with pytest.raises(ValueError,match='changed'):
        downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,pattern='{title}')


def test_retry_limit_and_cancellation():
    class Cancel:
        def is_set(self):return False
        def wait(self,n):return False
    attempts=[]
    def fail():attempts.append(1);raise RuntimeError('offline')
    with pytest.raises(RuntimeError):downloads.retry_audio(fail,Cancel())
    assert len(attempts)==6
    attempts.clear()
    def succeed():
        attempts.append(1)
        if len(attempts)<6:raise RuntimeError('transient')
        return 'ok'
    assert downloads.retry_audio(succeed,Cancel())=='ok'
    stop=threading.Event();stop.set()
    with pytest.raises(downloads.Cancelled):downloads.retry_audio(fail,stop)
    class StopInBackoff(Cancel):
        def wait(self,n):return True
    attempts.clear()
    with pytest.raises(downloads.Cancelled):downloads.retry_audio(fail,StopInBackoff())
    assert len(attempts)==1


def test_prefetch_overlaps_review_and_uses_final_metadata(tmp_path,monkeypatch):
    import controller as module
    monkeypatch.setattr(module,'DATA',tmp_path)
    started=threading.Event();release=threading.Event()
    class Meta:
        def __init__(self):self.yt=self
        def get_playlist(self,*a,**k):return {'tracks':[{'videoId':'abcdefghijk'}]}
        def youtube(self,t):
            assert started.wait(5)
            return {'id':t['videoId'],'tags':{'TITLE':['Original'],'ARTIST':['Artist']},'status':'review','warnings':[],'candidates':[]}
        def enrich(self,item):return item
    def fetch(item,temp,audio,cancel,progress):
        started.set();assert release.wait(5)
        audio_file(audio,{'TITLE':['Staged']})
    monkeypatch.setattr(module,'Metadata',Meta);monkeypatch.setattr(module,'fetch_audio',fetch)
    c=module.Controller();output=tmp_path/'output'
    c.analyze({'playlist':'https://music.youtube.com/playlist?list=PLMTDok-Dtp0Q','output':str(output)})
    try:
        assert started.wait(5)
        import time
        end=time.monotonic()+5
        while not c.state['tracks'] and time.monotonic()<end:time.sleep(.01)
        c.edit({'id':'abcdefghijk','tags':{'TITLE':'Reviewed'}})
        assert not list(output.rglob('*.mp3'))
    finally:release.set();c.worker.join(5)
    assert not c.state['busy'] and c.state['audio']['abcdefghijk']=='staged'
    monkeypatch.setattr(downloads,'fetch_audio',lambda *a:pytest.fail('Staged audio must be reused'))
    c.download({'pattern':'{title}','folders':'artist'});c.worker.join(5)
    target=output/'Artist'/'Reviewed.mp3'
    assert target.exists() and downloads.MP3(target).tags['TIT2'].text==['Reviewed']


def test_cancel_does_not_publish(tmp_path):
    audio_file(tmp_path/'song.mp3',{'TITLE':['Song'],'ARTIST':['Artist']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    before=downloads.digest(item['local_file']);stop=threading.Event();stop.set()
    with pytest.raises(downloads.Cancelled):downloads.download(item,tmp_path,False,stop,lambda n:None)
    assert downloads.digest(item['local_file'])==before


def test_source_changed_during_retag_is_not_published(tmp_path,monkeypatch):
    old=audio_file(tmp_path/'source.mp3',{'TITLE':['Song'],'ARTIST':['Artist']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    original=downloads.write_tags
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        with old.open('ab') as f:f.write(b'external change')
        return result
    monkeypatch.setattr(downloads,'write_tags',changed)
    with pytest.raises(ValueError,match='Source file changed'):
        downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,pattern='{title}',folders='artist')
    assert old.exists() and not (tmp_path/'Artist'/'Song.mp3').exists()


def test_collision_created_at_publication_is_protected(tmp_path,monkeypatch):
    old=audio_file(tmp_path/'source.mp3',{'TITLE':['Song'],'ARTIST':['Artist']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    original=downloads.publish_new
    def claim(audio,target):
        target.write_bytes(b'other writer')
        original(audio,target)
    monkeypatch.setattr(downloads,'publish_new',claim)
    with pytest.raises(FileExistsError):
        downloads.download(item,tmp_path,False,threading.Event(),lambda n:None,pattern='{title}',folders='artist')
    assert old.exists() and (tmp_path/'Artist'/'Song.mp3').read_bytes()==b'other writer'


def test_local_retag_preserves_audio_and_romanizes_lyrics(tmp_path,monkeypatch):
    old=audio_file(tmp_path/'source.mp3',{'TITLE':['안녕'],'ARTIST':['아이유'],'LYRICS':['안녕하세요']})
    item=downloads.load_local(tmp_path,threading.Event())[0]
    monkeypatch.setattr(downloads.subprocess,'Popen',lambda *a,**k:pytest.fail('Must not re-encode'))
    result=downloads.download(item,tmp_path,True,threading.Event(),lambda n:None,pattern='{title}')
    assert Path(result['file']).name=='Annyeong.mp3'
    assert downloads.MP3(result['file']).tags.getall('USLT')[0].text=='Annyeonghaseyo'
