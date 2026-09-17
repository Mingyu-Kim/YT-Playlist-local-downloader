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
