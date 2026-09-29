"""Source-derived identifier recognition; no query/benchmark lookup tables."""
import re,unicodedata
DASHES=str.maketrans({c:'-' for c in '‐‑‒–—−'})
NUMBER_WORDS={'one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10','eleven':'11','twelve':'12'}
STANDARD=re.compile(r'\b(?:ISO|EN|BS|ASTM|API|ACEA)\s*(?:specification\s*)?[A-Z]*\s*\d+[A-Z0-9]*(?:\s*[-/:]\s*[A-Z0-9]+)*',re.I)
MEASURE=re.compile(r'(?<!\w)[+-]?\d+(?:\.\d+)?\s*(?:hours?|weeks?|months?|minutes?|seconds?|kPa|psi|PPM|Volts?|mm|Amps?|kVA|kW|Hz|rpm|dBA|°\s*[CF])\b',re.I)
INTERVAL=re.compile(r'(?im)^\s*(?:Every\s+(?:(?:\w+|\d+)\s+)?(?:hours?|weeks?|months?|years?)(?:\s+or\s+\d+\s+hours?)?|Daily(?:\s+or\s+at\s+Each\s+Startup)?|Weekly|Monthly)\s*:?[ \t]*$')

def normalize_identifier(value):
    text=unicodedata.normalize('NFKC',value).translate(DASHES).casefold()
    text=re.sub(r'\s+',' ',text).strip().rstrip(':')
    text=re.sub(r'\b(iso|en|bs|astm|api|acea)\s*(?:specification\s*)?(?=\d)',r'\1 ',text)
    text=re.sub(r'\s*([/:+-])\s*',r'\1',text)
    text=re.sub(r'(?<=\d)\s*(?=[a-z°])',' ',text)
    m=re.fullmatch(r'every (?:(\w+|\d+) )?(hour|week|month|year)s?',text)
    if m:
        value=m[1] or '1';text=f'every {NUMBER_WORDS.get(value,value)} {m[2]}'
    return text

def extract_identifiers(text):
    normalized=text.translate(DASHES)
    found=[]
    for regex in (STANDARD,MEASURE,INTERVAL):
        for m in regex.finditer(normalized):
            raw=text[m.start():m.end()].strip().rstrip(':')
            if raw:found.append(raw)
    # Descriptive indications are explicit quoted upper-case phrases, not fabricated numeric codes.
    for m in re.finditer(r'[“"\u2018]([A-Z][A-Z /-]{3,60})[”"\u201c\u2019]',text):found.append(m[1])
    for line in text.splitlines():
        if line.startswith('Symptom: '):
            for part in line.split(':',1)[1].split(' / '):
                if part.strip().isupper():found.append(part.strip())
    return tuple(dict.fromkeys(found))
