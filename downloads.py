"""Download/tag MP3 files with a small reusable inventory; no backups/history."""
from contextlib import closing
import hashlib,io,json,os,shutil,sqlite3,subprocess,tempfile,re,logging
from urllib.parse import urlparse,parse_qs
from pathlib import Path
import requests
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3,TIT2,TPE1,TPE2,TALB,TDRC,TCOM,TCON,TSRC,TCOP,TRCK,TPOS,TXXX,USLT,APIC,WOAS
from yt_dlp import YoutubeDL
from common import DATA,binary
from text_rules import display_tags,relative_path,DEFAULT_FORMAT,romanize


class Cancelled(Exception):pass

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def artwork(url):
    r=requests.get(url,timeout=(8,20));r.raise_for_status()
    with Image.open(io.BytesIO(r.content)) as image:
        image=image.convert('RGB');image.thumbnail((1000,1000));out=io.BytesIO();image.save(out,'JPEG',quality=92);return out.getvalue()


def write_tags(path,tags,cover=None,preserve=False,latin=False):
    audio=MP3(path)
    if not preserve or audio.tags is None:audio.tags=ID3()
    else:
        if latin:
            for frame in audio.tags.values():
                if hasattr(frame,'text') and not (frame.FrameID=='TXXX' and frame.desc in ('YOUTUBE_ID','SOURCE','YOUTUBE_MUSIC_URL','YTPL_PROFILE')):
                    frame.text=romanize(frame.text) if isinstance(frame.text,str) else [romanize(v) for v in frame.text]
        for key in ('TIT2','TPE1','TPE2','TALB','TDRC','TCOM','TCON','TRCK','TPOS'):audio.tags.delall(key)
    frames={'TITLE':TIT2,'ARTIST':TPE1,'ALBUMARTIST':TPE2,'ALBUM':TALB,'DATE':TDRC,'COMPOSER':TCOM,'GENRE':TCON,'ISRC':TSRC,'COPYRIGHT':TCOP}
    for k,v in tags.items():
        if not v:continue
        if k in frames:audio.tags.add(frames[k](encoding=1,text=v))
        elif k=='LYRICS':audio.tags.add(USLT(encoding=1,lang='und',desc='',text=v[0]))
        elif k not in ('TRACKNUMBER','TRACKTOTAL','DISCNUMBER','DISCTOTAL'):audio.tags.add(TXXX(encoding=1,desc=k,text=v))
    for key,total,frame in [('TRACKNUMBER','TRACKTOTAL',TRCK),('DISCNUMBER','DISCTOTAL',TPOS)]:
        if tags.get(key):audio.tags.add(frame(encoding=1,text=[tags[key][0]+('/'+tags[total][0] if tags.get(total) else '')]))
    if tags.get('SOURCE'):audio.tags.add(WOAS(url=tags['SOURCE'][0]))
    if cover and (not preserve or not audio.tags.getall('APIC')):audio.tags.add(APIC(encoding=1,mime='image/jpeg',type=3,desc='Cover',data=cover))
    audio.save(v2_version=3)
    return {'duration':audio.info.length,'bitrate':audio.info.bitrate,'sample_rate':audio.info.sample_rate}


def youtube_id(tags):
    """Recognize explicit IDs and older source-URL tags; never guess from filenames."""
    if not tags:return None
    ids=set()
    for frame in tags.getall('TXXX'):
        if frame.desc.upper() in ('YOUTUBE_ID','YOUTUBE_VIDEO_ID'):
            ids.update(str(v) for v in frame.text if re.fullmatch(r'[A-Za-z0-9_-]{11}',str(v)))
        elif frame.desc.upper() in ('SOURCE','YOUTUBE_URL','YOUTUBE_MUSIC_URL'):
            for value in frame.text:
                found=id_from_url(str(value))
                if found:ids.add(found)
    for frame in tags.getall('WOAS'):
        found=id_from_url(frame.url)
        if found:ids.add(found)
    return next(iter(ids)) if len(ids)==1 else None


def id_from_url(value):
    try:
        url=urlparse(value)
        if url.scheme not in ('http','https'):return None
        if url.hostname=='youtu.be':video=url.path.strip('/')
        elif url.hostname in ('youtube.com','www.youtube.com','music.youtube.com'):
            video=parse_qs(url.query).get('v',[''])[0]
        else:return None
        return video if re.fullmatch(r'[A-Za-z0-9_-]{11}',video) else None
    except ValueError:return None


class Inventory:
    def __init__(self,path=None):
        self.path=Path(path or DATA/'library.sqlite3');self.scanned=set()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE IF NOT EXISTS files(output TEXT,video TEXT,path TEXT,sha256 TEXT,profile TEXT,PRIMARY KEY(output,video))');db.commit()
    def scan(self,output,cancel=None):
        output=Path(output).resolve()
        if output in self.scanned:return 0
        count=0;seen=set();log=logging.getLogger('ytpl')
        if output.is_dir():
            for path in music_files(output):
                if cancel and cancel.is_set():raise Cancelled()
                if path.suffix.lower()!='.mp3' or not path.is_file():continue
                try:
                    audio=MP3(path)
                    if audio.info.length<=0 or audio.info.bitrate<=0:continue
                    video=youtube_id(audio.tags)
                    if not video or video in seen:continue
                    marker=audio.tags.get('TXXX:YTPL_PROFILE')
                    profile=str(marker.text[0]) if marker and marker.text else ''
                    if not re.fullmatch('[a-f0-9]{64}',profile):profile=''
                    self.save(output,video,path,profile)
                    seen.add(video);count+=1
                except Exception as exc:
                    # A bad/unreadable file must not prevent scanning other music.
                    log.warning('Could not inspect %s: %s',path.name,exc)
        self.scanned.add(output)
        log.info('Output scan: %s existing YouTube MP3 files recognized in %s',count,output)
        return count

    def find(self,output,video):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute('select path,sha256,profile from files where output=? and video=?',(str(output),video)).fetchone()
        return row if row and Path(row[0]).is_file() and digest(row[0])==row[1] else None
    def save(self,output,video,path,profile):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('insert or replace into files values(?,?,?,?,?)',(str(output),video,str(path),digest(path),profile));db.commit()


class Logger:
    def __init__(self,callback):self.callback=callback
    def debug(self,msg):pass
    def warning(self,msg):self.callback(str(msg))
    def error(self,msg):self.callback(str(msg))


def ydl_options(callback=lambda m:None):
    return {'quiet':True,'no_warnings':False,'noplaylist':True,'socket_timeout':20,'retries':0,'fragment_retries':0,
            'cachedir':str(DATA/'yt-cache'),'js_runtimes':{'node':{'path':binary('node')}},'logger':Logger(callback)}


def download(item,output,latin,cancel,progress,inventory=None,pattern=None,folders='none',staged=None):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    inventory=inventory or Inventory();inventory.scan(output,cancel)
    cached=inventory.find(output,item['id'])
    if item.get('local_file'):
        local=Path(item['local_file'])
        if not local.is_file() or not local.resolve().is_relative_to(output) or digest(local)!=item['local_digest']:
            raise ValueError('Local file changed since loading; reload the folder')
        cached=(str(local),item['local_digest'],'')
    tags=display_tags(item['tags'],latin)
    if not item.get('local_file') or re.fullmatch(r'[A-Za-z0-9_-]{11}',item['id']):tags.update(YOUTUBE_ID=[item['id']],SOURCE=['https://www.youtube.com/watch?v='+item['id']],YOUTUBE_MUSIC_URL=['https://music.youtube.com/watch?v='+item['id']],SOURCE_SERVICE=['YouTube'])
    tags.pop('YTPL_PROFILE',None)
    bitrate=round(MP3(cached[0]).info.bitrate/1000) if cached else 320
    if not item.get('local_file'):tags['ENCODING']=[f'MP3 {bitrate} kbps; YouTube lossy source']
    profile=hashlib.sha256(json.dumps([tags,item.get('cover_url'),item.get('mb_cover_url')],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    tags['YTPL_PROFILE']=[profile]
    target=output/relative_path(tags,pattern or DEFAULT_FORMAT,folders)
    if not target.resolve().is_relative_to(output):raise ValueError('Output path escapes the selected folder')
    if cached and cached[2]==profile and (pattern is None or Path(cached[0])==target):return {'file':cached[0],'status':'reused'}
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and (not cached or Path(cached[0])!=target):
        target=target.with_stem(target.stem+' ['+item['id']+']')
        if target.exists() and (not cached or Path(cached[0])!=target):raise ValueError('Output filename is occupied by another file: '+target.name)
    with tempfile.TemporaryDirectory(prefix='.yt-pl-',dir=output) as temp:
        temp=Path(temp);audio=temp/'tagged.mp3';cover=None
        if cancel.is_set():raise Cancelled()
        if cached:
            old=MP3(cached[0]);pictures=old.tags.getall('APIC') if old.tags else []
            if pictures:cover=pictures[0].data
            shutil.copy2(cached[0],audio)
        else:
            if staged is not None:
                if not Path(staged).is_file():raise ValueError('Staged audio is missing; start a new scan to fetch it again')
                shutil.copy2(staged,audio)
            else:retry_audio(lambda:fetch_audio(item,temp,audio,cancel,progress),cancel)
        for url in dict.fromkeys(filter(None,[item.get('mb_cover_url'),item.get('cover_url')])):
            if cancel.is_set():raise Cancelled()
            try:cover=artwork(url);break
            except Exception:item['warnings'].append('Album artwork unavailable from one source')
        quality=write_tags(audio,tags,cover,preserve=bool(item.get('local_file')),latin=latin)
        if quality['duration']<=0 or (not cached and quality['bitrate']<319000):raise RuntimeError('Output audio validation failed')
        if cancel.is_set():raise Cancelled()
        # Refuse to replace any file changed while the download was running.
        if target.exists() and (not cached or Path(cached[0])!=target or digest(target)!=cached[1]):raise ValueError('Output file changed; not overwritten')
        if cached and (not Path(cached[0]).is_file() or digest(cached[0])!=cached[1]):raise ValueError('Source file changed; not overwritten')
        if cached and Path(cached[0])==target:os.replace(audio,target)
        else:
            # Hard-link publication fails atomically if another file claims the name.
            publish_new(audio,target)
        inventory.save(output,item['id'],target,profile)
        if cached and Path(cached[0])!=target and Path(cached[0]).is_file() and digest(cached[0])==cached[1]:
            Path(cached[0]).unlink()
            clean_empty_parents(Path(cached[0]).parent,output)
    result={'file':str(target),'status':'reused' if cached else 'downloaded','quality':quality}
    if item.get('local_file'):result.update(local_file=str(target),local_digest=digest(target))
    return result


def clean_empty_parents(directory,output):
    """Prune only emptied source ancestors, never the root or linked directories."""
    output=Path(output).resolve();directory=Path(directory).absolute()
    while directory!=output and directory.is_relative_to(output):
        # Resolving must not redirect cleanup through a symlink/junction, even inside root.
        if directory.is_symlink() or os.path.isjunction(directory) or directory.resolve()!=directory:return
        try:directory.rmdir()
        except OSError:return  # Nonempty, inaccessible, or changed concurrently: leave it.
        directory=directory.parent


def fetch_audio(item,temp,audio,cancel,progress):
    def hook(data):
        if cancel.is_set():raise Cancelled()
        if data['status']=='downloading':
            total=data.get('total_bytes') or data.get('total_bytes_estimate')
            if total:progress(round(min(99,100*data.get('downloaded_bytes',0)/total)))
    options={**ydl_options(lambda m:item['warnings'].append(m)), 'format':'bestaudio/best','outtmpl':str(temp/'source.%(ext)s'),'progress_hooks':[hook]}
    with YoutubeDL(options) as ydl:
        info=ydl.extract_info('https://www.youtube.com/watch?v='+item['id'],download=True)
        original=Path(ydl.prepare_filename(info))
    if cancel.is_set():raise Cancelled()
    command=[binary('ffmpeg'),'-nostdin','-v','error','-y','-i',str(original),'-map','0:a:0','-vn','-map_metadata','-1','-c:a','libmp3lame','-b:a','320k','-ar','48000',str(audio)]
    with (temp/'ffmpeg.log').open('wb') as log:
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            import time
            started=time.monotonic()
            while process.poll() is None:
                if cancel.wait(.1):process.terminate();raise Cancelled()
                if time.monotonic()-started>900:process.terminate();raise RuntimeError('Audio conversion timed out')
            if process.returncode:raise RuntimeError('Audio conversion failed: '+(temp/'ffmpeg.log').read_text(errors='replace')[-1500:])
        finally:
            if process.poll() is None:process.kill()
            process.wait()


def retry_audio(work,cancel):
    """Initial attempt plus at most five cancellable retries."""
    for attempt in range(6):
        if cancel.is_set():raise Cancelled()
        try:return work()
        except Cancelled:raise
        except Exception:
            if cancel.is_set():raise Cancelled()
            if attempt==5:raise
            if cancel.wait(min(2**attempt,16)):raise Cancelled()


def music_files(output):
    for root,dirs,files in os.walk(output,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not d.startswith('.yt-pl-') and not Path(root,d).is_symlink() and not os.path.isjunction(Path(root,d)))
        for name in sorted(files):
            path=Path(root,name)
            if path.suffix.lower()=='.mp3' and not path.is_symlink() and path.resolve().is_relative_to(Path(output).resolve()):yield path


def load_local(output,cancel):
    items=[]
    frames={'TIT2':'TITLE','TPE1':'ARTIST','TPE2':'ALBUMARTIST','TALB':'ALBUM','TDRC':'DATE','TCOM':'COMPOSER','TCON':'GENRE','TRCK':'TRACKNUMBER','TPOS':'DISCNUMBER','TSRC':'ISRC','TCOP':'COPYRIGHT'}
    for path in music_files(output):
        if cancel.is_set():raise Cancelled()
        try:
            before=digest(path);audio=MP3(path)
            if audio.info.length<=0:continue
            tags={}
            for frame in (audio.tags or {}).values():
                if frame.FrameID in frames:tags[frames[frame.FrameID]]=[str(v) for v in frame.text]
                elif frame.FrameID=='TXXX':tags[frame.desc]=[str(v) for v in frame.text]
            if digest(path)!=before:continue
            video=youtube_id(audio.tags)
            identity='local-'+hashlib.sha256(str(path).encode()).hexdigest()[:20]
            items.append({'id':identity,'source_id':video,'tags':tags,'local_file':str(path),'local_digest':before,'status':'ready' if tags.get('TITLE') and tags.get('ARTIST') else 'review','warnings':[],'candidates':[]})
        except Exception as exc:logging.getLogger('ytpl').warning('Could not load %s: %s',path.name,exc)
    return items


def publish_new(audio,target):
    if os.name=='nt':
        # Windows rename refuses an existing destination, including on FAT/exFAT.
        os.rename(audio,target)
        return
    try:os.link(audio,target)
    except FileExistsError:raise
    except OSError:
        # Some removable-drive filesystems do not support hard links.
        with open(target,'xb') as dest:
            try:
                with open(audio,'rb') as source:shutil.copyfileobj(source,dest)
                dest.flush();os.fsync(dest.fileno())
            except BaseException:
                dest.close();Path(target).unlink();raise
    Path(audio).unlink()
