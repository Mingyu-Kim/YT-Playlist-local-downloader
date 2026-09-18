"""English preference and readable Revised Romanization of Korean."""
import re, unicodedata
from korean_romanizer.romanizer import Romanizer
HANGUL=re.compile(r'[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7ff]+')


def english(value):
    value=str(value or '').strip()
    if not HANGUL.search(value):return value
    # Only select an English component explicitly supplied in a bilingual name.
    parts=[p.strip() for p in re.split(r'[()\[\]]|\s[/|]\s',value) if p.strip()]
    options=[p for p in parts if re.search('[A-Za-z]',p) and not HANGUL.search(p)]
    return max(options,key=len) if options else value


def romanize(value):
    value=unicodedata.normalize('NFC',str(value))
    def convert(match):
        text=Romanizer(match.group()).romanize()
        # Isolated/archaic jamo have no whole-word pronunciation. Use Latin letter names.
        text=HANGUL.sub(lambda m:' '.join(unicodedata.name(c,'Korean letter').split(' ')[-1].lower() for c in m.group()),text)
        return text[:1].upper()+text[1:]
    return HANGUL.sub(convert,value)


def display_tags(tags, latin=False):
    return {k:[romanize(v) if latin else str(v) for v in values] for k,values in tags.items() if values}


def filename(tags):
    value='; '.join(tags.get('ARTIST') or ['Unknown artist'])+' - '+(tags.get('TITLE') or ['Untitled'])[0]
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',value).strip(' .')[:170].rstrip(' .')
    if re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',value):value='_'+value
    return (value or 'Untitled')+'.mp3'


DEFAULT_FORMAT = '{artist} - {title}'
FOLDERS = ('none', 'artist', 'decade', 'artist/decade', 'decade/artist')


def validate_layout(pattern=DEFAULT_FORMAT, folders='none'):
    if not isinstance(pattern,str) or not pattern.strip() or len(pattern)>200:
        raise ValueError('Enter a filename format (maximum 200 characters)')
    rest=re.sub(r'\{(artist|title|album|track|decade)\}', '', pattern)
    if re.search(r'[{}<>:"/\\|?*\x00-\x1f]',rest):
        raise ValueError('Use {artist}, {title}, {album}, {track}, {decade}; no path separators')
    if folders not in FOLDERS:raise ValueError('Invalid folder structure')
    return pattern,folders


def safe_component(value):
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).strip(' .')[:170].rstrip(' .') or 'Unknown'
    if re.match(r'(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',value):value='_'+value
    return value


def relative_path(tags, pattern=DEFAULT_FORMAT, folders='none'):
    from pathlib import Path
    validate_layout(pattern,folders)
    date=(tags.get('DATE') or [''])[0]
    year=re.match(r'^(\d{4})(?:$|[-/])',date)
    values={'artist':'; '.join(tags.get('ARTIST') or ['Unknown artist']),
            'title':(tags.get('TITLE') or ['Untitled'])[0],
            'album':(tags.get('ALBUM') or ['Unknown album'])[0],
            'track':(tags.get('TRACKNUMBER') or ['Unknown track'])[0],
            'decade':str(int(year[1])//10*10)+'s' if year else 'Unknown decade'}
    name=re.sub(r'\{(\w+)\}',lambda m:values[m[1]],pattern)
    parts=[] if folders=='none' else [safe_component(values[k]) for k in folders.split('/')]
    return Path(*parts,safe_component(name)+'.mp3')
