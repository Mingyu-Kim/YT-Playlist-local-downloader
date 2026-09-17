"""YouTube Music and MusicBrainz metadata; audio always comes from YouTube."""
import hashlib,json,re,time,threading
import requests
from rapidfuzz.fuzz import ratio
from ytmusicapi import YTMusic
from common import DATA,atomic_json
from text_rules import english,HANGUL


def names(credits):return [c.get('name') or c.get('artist',{}).get('name') for c in credits if isinstance(c,dict) and (c.get('name') or c.get('artist',{}).get('name'))]
def similar(a,b):
    clean=lambda x:re.sub(r'[^\w]','',str(x).casefold())
    return ratio(clean(a),clean(b))/100

def alternatives(title):
    return list(dict.fromkeys([title,re.sub(r'\s*\((?:feat\.?|with|featuring)\s+[^)]+\)','',title,flags=re.I),english(title)]))


_mb_lock=threading.Lock()
_mb_last=0.0


class Metadata:
    def __init__(self):
        self.yt=YTMusic(language='en');self.albums={};self.http=requests.Session()
        self.http.headers['User-Agent']='YT-PL-Downloader/1.0 (personal local music metadata client)'
        self.last=0

    def mb(self,endpoint,**params):
        global _mb_last
        params['fmt']='json'
        key=hashlib.sha256(json.dumps([endpoint,params],sort_keys=True).encode()).hexdigest()
        cache=DATA/'metadata-cache'/(key+'.json')
        if cache.exists() and time.time()-cache.stat().st_mtime<30*86400:return json.loads(cache.read_text(encoding='utf-8'))
        for attempt in range(3):
            with _mb_lock:
                time.sleep(max(0,1.1-(time.monotonic()-_mb_last)))
                _mb_last=time.monotonic()
            r=self.http.get('https://musicbrainz.org/ws/2/'+endpoint,params=params,timeout=(10,20))
            if r.status_code in (429,503) and attempt<2:time.sleep(2**attempt);continue
            r.raise_for_status();data=r.json();atomic_json(cache,data);return data

    def youtube(self,track):
        track=dict(track);warnings=[];video=track['videoId'];lyrics=None
        try:
            watch=self.yt.get_watch_playlist(videoId=video,limit=1)
            same=next((t for t in watch.get('tracks',[]) if t.get('videoId')==video),None)
            if same:
                for key in ('title','artists','album','thumbnails','duration_seconds'):
                    if not track.get(key) and same.get(key):track[key]=same[key]
            if watch.get('lyrics'):
                lyrics=self.yt.get_lyrics(watch['lyrics']).get('lyrics')
        except Exception as exc:warnings.append('YouTube Music song details: '+type(exc).__name__)
        album={};album_id=(track.get('album') or {}).get('id');position=None
        if album_id:
            try:
                if album_id not in self.albums:self.albums[album_id]=self.yt.get_album(album_id)
                album=self.albums[album_id]
                same=next((t for t in album.get('tracks',[]) if t.get('videoId')==video),None)
                if same:position=same.get('trackNumber')
            except Exception as exc:warnings.append('YouTube Music album details: '+type(exc).__name__)
        title=track.get('title') or 'Untitled';artists=[a['name'] for a in track.get('artists',[]) if a.get('name')]
        if not artists:artists=[track.get('author') or 'Unknown artist']
        tags={'TITLE':[english(title)],'ARTIST':[english(a) for a in artists], 'SOURCE':['https://www.youtube.com/watch?v='+video], 'YOUTUBE_ID':[video], 'METADATA_SOURCE':['YouTube Music']}
        album_name=album.get('title') or (track.get('album') or {}).get('name')
        if album_name:tags['ALBUM']=[english(album_name)]
        if album.get('artists'):tags['ALBUMARTIST']=[english(a['name']) for a in album['artists'] if a.get('name')]
        if album.get('year'):tags['DATE']=[str(album['year'])]
        if position:tags['TRACKNUMBER']=[str(position)]
        if album.get('trackCount'):tags['TRACKTOTAL']=[str(album['trackCount'])]
        if lyrics:tags['LYRICS']=[lyrics]
        if track.get('isExplicit') is not None:tags['EXPLICIT']=[str(bool(track['isExplicit'])).lower()]
        thumbs=album.get('thumbnails') or track.get('thumbnails') or []
        thumbs=sorted(thumbs,key=lambda t:(t.get('width',0) or 0)*(t.get('height',0) or 0),reverse=True)
        duration=track.get('duration_seconds')
        if not duration and track.get('duration'):
            try:
                duration=0
                for part in str(track['duration']).split(':'):duration=duration*60+int(part)
            except ValueError:duration=None
        return {'id':video,'tags':tags,'raw_title':title,'raw_artists':artists,'duration':duration,
                'cover_url':thumbs[0]['url'] if thumbs else None,'warnings':warnings,'status':'ready','candidates':[]}

    def search(self,item):
        title=item['raw_title'];artist=item['raw_artists'][0];found={}
        quote=lambda s:'"'+re.sub(r'([\\"+\-!(){}\[\]^~*?:/])',r'\\\1',s)+'"'
        for name in alternatives(title):
            query='recording:'+quote(name)+' AND artist:'+quote(artist)
            for r in self.mb('recording',query=query,limit=30).get('recordings',[]):found[r['id']]=r
        if not found:
            for r in self.mb('recording',query='recording:'+quote(title),limit=30).get('recordings',[]):found[r['id']]=r
        candidates=[]
        version_patterns=[r'\blive\b|라이브',r'\bremix\b|리믹스',r'\binst(?:rumental)?\.?\b|\bkaraoke\b|반주',r'\bcover\b|커버',r'\bacoustic\b|어쿠스틱',r'\bsped\b|\bslowed\b']
        for r in found.values():
            titles=[r['title']]+[a['name'] for a in r.get('aliases',[]) if a.get('name')]
            title_score=max(similar(a,b) for a in alternatives(title) for b in titles)
            artists=names(r.get('artist-credit',[]))
            for a in r.get('artist-credit',[]):
                if isinstance(a,dict):artists.extend(v['name'] for v in a.get('artist',{}).get('aliases',[]) if v.get('name'))
            artist_score=max((similar(a,b) for a in item['raw_artists'] for b in artists),default=0)
            delta=abs(item['duration']-r['length']/1000) if item.get('duration') and r.get('length') else None
            version=any(bool(re.search(p,title,re.I))!=bool(re.search(p,r['title']+' '+r.get('disambiguation',''),re.I)) for p in version_patterns)
            notes=[]
            if version:notes.append('version')
            if artist_score<.7:notes.append('artist')
            if title_score<.75:notes.append('title')
            if delta is not None and delta>12:notes.append('duration')
            if re.search(r'mashup|매시업|\s[x×]\s',title,re.I):notes.append('mashup')
            score=.58*title_score+.32*artist_score+.10*(max(0,1-delta/20) if delta is not None else .5)-(.25 if notes else 0)
            if score>=.45:candidates.append({'id':r['id'],'title':r['title'],'artists':names(r.get('artist-credit',[])),'score':round(score,3),'notes':notes})
        return sorted(candidates,key=lambda c:-c['score'])[:8]

    def name_en(self,obj):
        return next((a['name'] for a in obj.get('aliases',[]) if a.get('locale')=='en' and not HANGUL.search(a['name'])),english(obj.get('name') or obj.get('title') or ''))

    def resolve(self,item,recording_id):
        r=self.mb('recording/'+recording_id,inc='artists+releases+isrcs+aliases+artist-rels+work-rels')
        tags={'TITLE':[self.name_en(r)],'MUSICBRAINZ_TRACKID':[r['id']],'METADATA_SOURCE':['YouTube Music; MusicBrainz']}
        tags['ARTIST']=[self.name_en(a['artist']) or english(a.get('name','')) for a in r.get('artist-credit',[]) if isinstance(a,dict)]
        tags['MUSICBRAINZ_ARTISTID']=[a['artist']['id'] for a in r.get('artist-credit',[]) if isinstance(a,dict)]
        if r.get('isrcs'):tags['ISRC']=r['isrcs']
        for rel in r.get('relations',[]):
            key={'producer':'PRODUCER','arranger':'ARRANGER','composer':'COMPOSER','lyricist':'LYRICIST'}.get(rel.get('type'))
            if key and rel.get('artist'):tags.setdefault(key,[]).append(self.name_en(rel['artist']))
            if rel.get('type')=='performance' and rel.get('work'):
                try:
                    work=self.mb('work/'+rel['work']['id'],inc='artist-rels')
                    for credit in work.get('relations',[]):
                        k={'composer':'COMPOSER','lyricist':'LYRICIST','writer':'WRITER'}.get(credit.get('type'))
                        if k and credit.get('artist'):tags.setdefault(k,[]).append(self.name_en(credit['artist']))
                except requests.RequestException:item['warnings'].append('MusicBrainz work credits unavailable')
        albums=[a for a in r.get('releases',[]) if a.get('status')=='Official']
        known=(item['tags'].get('ALBUM') or [''])[0]
        if known:albums=[a for a in albums if similar(known,english(a['title']))>.88]
        elif len(albums)!=1:albums=[]
        if albums:
            a=min(albums,key=lambda a:(a.get('date') or '9999',a['id']))
            a=self.mb('release/'+a['id'],inc='recordings+artists+labels+aliases')
            tags.update(ALBUM=[self.name_en(a)],ALBUMARTIST=[self.name_en(c['artist']) for c in a.get('artist-credit',[]) if isinstance(c,dict)],MUSICBRAINZ_ALBUMID=[a['id']])
            if a.get('date'):tags['DATE']=[a['date']]
            if a.get('barcode'):tags['BARCODE']=[a['barcode']]
            labels=[self.name_en(l['label']) for l in a.get('label-info',[]) if l.get('label')]
            if labels:tags['LABEL']=labels
            positions=[(m,t) for m in a.get('media',[]) for t in m.get('tracks',[]) if t.get('recording',{}).get('id')==r['id']]
            if len(positions)==1:
                m,t=positions[0];tags.update(TRACKNUMBER=[str(t['position'])],TRACKTOTAL=[str(m['track-count'])],DISCNUMBER=[str(m['position'])],DISCTOTAL=[str(len(a['media']))])
            if a.get('cover-art-archive',{}).get('front'):item['mb_cover_url']='https://coverartarchive.org/release/'+a['id']+'/front-500'
        # Never lose a supplied English title/name when MB only supplies Korean.
        for k in ('TITLE','ARTIST','ALBUM','ALBUMARTIST'):
            old=item['tags'].get(k,[])
            if old and not any(HANGUL.search(v) for v in old) and any(HANGUL.search(v) for v in tags.get(k,[])):tags[k]=old
        item['tags'].update({k:v for k,v in tags.items() if v});item['matched_id']=r['id'];item['status']='ready'
        return item

    def enrich(self,item):
        try:
            item['candidates']=self.search(item)
            best=item['candidates'][0] if item['candidates'] else None
            if best and best['score']>.70 and not best['notes']:self.resolve(item,best['id'])
            elif best:item['status']='review'
        except Exception as exc:item['warnings'].append('MusicBrainz lookup unavailable: '+type(exc).__name__+(' (HTTP '+str(exc.response.status_code)+')' if getattr(exc,'response',None) is not None else ''))
        return item
