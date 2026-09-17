"""Thread-safe job controller for the local browser interface."""
import copy,json,re,threading
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from common import DATA,atomic_json
from metadata import Metadata
from downloads import download,Cancelled,ydl_options,Inventory
from text_rules import display_tags,romanize
from yt_dlp import YoutubeDL


def playlist_id(value):
    url=urlparse(value.strip())
    if url.scheme!='https' or url.hostname not in ('music.youtube.com','www.youtube.com','youtube.com'):raise ValueError('Enter a YouTube Music playlist URL')
    value=parse_qs(url.query).get('list',[''])[0]
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,150}',value):raise ValueError('The URL needs a valid playlist ID')
    return value


class Controller:
    def __init__(self):
        self.lock=threading.RLock();self.cancel=threading.Event();self.worker=None;self.meta=None;self.edits_done=threading.Event();self.edits_done.set()
        self.state={'phase':'idle','busy':False,'title':'','tracks':[],'message':'','progress':0,'output':str(Path.home()/'Music'/'YT-PL-Downloader'),'romanize':False}
        path=DATA/'session.json'
        if path.exists():
            try:
                self.state.update(json.loads(path.read_text(encoding='utf-8')))
                if self.state['busy']:
                    self.state.update(busy=False,phase='review',message='Previous run interrupted. Review and resume.')
                    for t in self.state['tracks']:
                        if t['status']=='downloading':t['status']='ready'
            except (ValueError,OSError):pass

        self.state['editing']=[]

    def save(self):
        with self.lock:atomic_json(DATA/'session.json',self.state)
    def snapshot(self):
        with self.lock:
            state=copy.deepcopy(self.state)
        for t in state['tracks']:
            t['tags']=display_tags({k:v for k,v in t['tags'].items() if k in ('TITLE','ARTIST','ALBUM','DATE')},state['romanize'])
            t['warnings']=t.get('warnings',[])[-4:]
        return state
    def start(self,work):
        with self.lock:
            if self.state['busy'] or self.state.get('editing'):raise ValueError('An operation is already running')
            self.state['busy']=True;self.cancel.clear()
        def run():
            try:work()
            except Cancelled:
                with self.lock:self.state.update(phase='review',message='Cancelled')
            except Exception as exc:
                with self.lock:self.state.update(phase='error',message=str(exc))
            finally:
                with self.lock:self.state['busy']=False
                self.save()
        self.worker=threading.Thread(target=run,daemon=True);self.worker.start()

    def analyze(self,data):
        pid=playlist_id(str(data.get('playlist','')))
        output=Path(str(data.get('output','')).strip()).expanduser()
        if not output.is_absolute():raise ValueError('Choose an absolute output directory')
        if output.exists() and not output.is_dir():raise ValueError('Output must be a folder')
        limit=int(data.get('limit') or 0)
        if limit<0 or limit>10000:raise ValueError('Invalid track limit')
        def work():
            self.meta=Metadata()
            with self.lock:self.state.update(phase='analyzing',title='',tracks=[],playlist=data['playlist'],output=str(output.resolve()),romanize=bool(data.get('romanize')),message='',progress=0)
            try:
                playlist=self.meta.yt.get_playlist(pid,limit=limit or None)
                tracks=playlist.get('tracks',[]);title=playlist.get('title') or pid
            except Exception:
                with YoutubeDL({**ydl_options(),'extract_flat':'in_playlist','noplaylist':False,'ignoreerrors':True}) as ydl:
                    playlist=ydl.extract_info('https://www.youtube.com/playlist?list='+pid,download=False)
                tracks=[{'videoId':t['id'],'title':t.get('title'),'artists':[{'name':t.get('uploader') or 'Unknown artist'}],'duration_seconds':t.get('duration')} for t in playlist.get('entries',[]) if t and re.fullmatch(r'[A-Za-z0-9_-]{11}',t.get('id',''))]
                title=playlist.get('title') or pid
            if limit:tracks=tracks[:limit]
            seen=set();tracks=[t for t in tracks if t.get('videoId') and not (t['videoId'] in seen or seen.add(t['videoId']))]
            if not tracks:raise ValueError('Playlist contains no accessible songs')
            with self.lock:self.state['title']=title
            for i,t in enumerate(tracks):
                if self.cancel.is_set():raise Cancelled()
                try:
                    item=self.meta.youtube(t)
                    item=self.meta.enrich(item)
                except Exception as exc:
                    item={'id':t['videoId'],'tags':{'TITLE':[t.get('title') or 'Unavailable']},'status':'error','error':str(exc),'warnings':[],'candidates':[]}
                with self.lock:
                    self.state['tracks'].append(item);self.state['progress']=round((i+1)*100/len(tracks));self.state['message']=f'{i+1} / {len(tracks)}'
                self.save()
            with self.lock:self.state.update(phase='review',message='',progress=100)
        self.start(work)

    def edit(self,data):
        # Completed scan results are immutable to the scan worker; only review edits touch them.
        with self.lock:
            if self.state['busy'] and self.state['phase']!='analyzing':
                raise ValueError('Wait until the current operation finishes')
            item=next((t for t in self.state['tracks'] if t['id']==data.get('id')),None)
            if not item:raise ValueError('Track not found')
            if item['id'] in self.state['editing']:raise ValueError('This song is already being edited')
            if data.get('skip'):
                item['status']='skipped';self.save();return
            candidate=data.get('candidate')
            if candidate and candidate not in [c['id'] for c in item.get('candidates',[])]:raise ValueError('Select a listed match')
            changes=data.get('tags') or {}
            allowed=('TITLE','ARTIST','ALBUM','ALBUMARTIST','DATE','TRACKNUMBER','DISCNUMBER','COMPOSER','GENRE')
            if not isinstance(changes,dict) or any(k not in allowed or not isinstance(v,str) or len(v)>2000 for k,v in changes.items()):raise ValueError('Invalid metadata fields')
            revised=copy.deepcopy(item)
            self.state['editing'].append(item['id']);self.edits_done.clear()
        try:
            # Separate HTTP session avoids sharing the scan worker's metadata client.
            if candidate:revised=Metadata().resolve(revised,candidate)
            for k,v in changes.items():
                values=[s.strip() for s in v.split(';') if s.strip()] if k in ('ARTIST','ALBUMARTIST','COMPOSER') else ([v.strip()] if v.strip() else [])
                if values:revised['tags'][k]=values
                else:revised['tags'].pop(k,None)
            if not revised['tags'].get('TITLE') or not revised['tags'].get('ARTIST'):raise ValueError('Title and artist are required')
            revised['status']='ready';revised.pop('error',None)
            with self.lock:item.update(revised)
        finally:
            with self.lock:
                self.state['editing'].remove(item['id'])
                if not self.state['editing']:self.edits_done.set()
                self.save()

    def download(self,data):
        with self.lock:
            if any(t['status']=='review' for t in self.state['tracks']):raise ValueError('Resolve uncertain metadata matches first')
            if not self.state['tracks']:raise ValueError('Analyze a playlist first')
            latin=bool(data.get('romanize',self.state['romanize']))
            if self.state['busy'] or self.state.get('editing'):raise ValueError('An operation is already running')
            self.state['romanize']=latin
        def work():
            with self.lock:self.state.update(phase='downloading',message='',progress=0)
            items=[t for t in self.state['tracks'] if t['status'] not in ('skipped',) and t['tags'].get('ARTIST')]
            inventory=Inventory()
            with self.lock:self.state['message']='Scanning output folder for existing YouTube MP3s…'
            inventory.scan(self.state['output'],self.cancel)
            with self.lock:self.state['message']=''
            for i,item in enumerate(items):
                if self.cancel.is_set():raise Cancelled()
                with self.lock:item['status']='downloading';item.pop('error',None)
                def progress(value):
                    with self.lock:self.state['progress']=round((i+value/100)*100/max(1,len(items)))
                try:
                    result=download(item,self.state['output'],latin,self.cancel,progress,inventory)
                    with self.lock:item.update(result)
                except Exception as exc:
                    with self.lock:item.update(status='error',error=str(exc))
                    if self.cancel.is_set():raise Cancelled()
                with self.lock:self.state['progress']=round((i+1)*100/max(1,len(items)))
                self.save()
            with self.lock:self.state.update(phase='complete',message='')
        self.start(work)
