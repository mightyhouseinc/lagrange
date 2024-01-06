#!/usr/bin/env python3
# Parses all the .po files and generates binary language strings to be loaded 
# at runtime via embedded data.

import os, sys

BUILD_LANGS = [ 'en', # base strings
    'cs',
    'de',
    'eo',
    'es',
    'es_MX',
    'eu',
    'fi',
    'fr',
    'gl',
    'hu',
    'ia',
    'ie',
    'isv',
    'it',
    'ja',
    'nl',
    'pl',
    'ru',
    'sk',
    'sr',
    'tok',
    'tr',
    'uk',
    'zh_Hans',
    'zh_Hant'
]
ESCAPES = {
    '\\': '\\',
    '"': '"',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
}
missing_count = {lang: 0 for lang in BUILD_LANGS}
MODE = 'new' if '--new' in sys.argv else 'compile'


def unquote(string):
    txt = string.strip()
    if txt[0] != '"' or txt[-1] != '"':
        raise Exception(f"invalid quoted string: {string}")
    txt = txt[1:-1]
    out = ''
    is_escape = False
    for c in txt:
        if is_escape:
            out += ESCAPES[c]
            is_escape = False
            continue
        if c == '\\':
            is_escape = True
        else:
            out += c
    return out        
    
    
def parse_po(src):
    messages = []
    is_multi = False  # string is multiple lines
    is_plural = False
    msg_id, msg_str, msg_index = None, None, None
    for line in open(src, 'rt', encoding='utf-8'):
        line = line.strip()
        if is_multi:
            if len(line) == 0 or line[0] != '"':
                if msg_id:
                    messages.append((msg_id, msg_str, msg_index))
                is_multi = False
            else:
                msg_str += unquote(line)
        if line.startswith('msgid_plural'):
            msg_id = unquote(line[12:])
            is_plural = True
        elif line.startswith('msgid'):
            msg_id = unquote(line[6:])
            is_plural = False
        elif line.startswith('msgstr'):            
            if line[6] == '[':
                msg_index = int(line[7])
                line = line[9:]
            else:
                msg_index = None
                line = line[6:]
            if line.endswith(' ""'):
                is_multi = True
                msg_str = ''
            else:
                msg_str = unquote(line)
                if msg_id:
                    messages.append((msg_id, msg_str, msg_index))
    if is_multi and msg_id:
        messages.append((msg_id, msg_str, msg_index))
    # Apply plural indices to ids.
    pluralized = []
    for msg_id, msg_str, msg_index in messages:
        if msg_index is not None:
            msg_id = f'{msg_id[:-1]}{msg_index}'
        pluralized.append((msg_id, msg_str))
            #print(msg_id, '=>', msg_str)
    return pluralized
    
    
def compile_string(msg_id, msg_str):
    return msg_id.encode('utf-8') + bytes([0]) + \
           msg_str.encode('utf-8') + bytes([0])
    

os.chdir(os.path.dirname(__file__))

if MODE == 'compile':
    BASE_STRINGS = {}
    PLURALS = set()
    for msg_id, msg_str in parse_po('en.po'):
        BASE_STRINGS[msg_id] = msg_str
        if msg_id.endswith('.0'):
            PLURALS.add(msg_id[:-2])
    for src in os.listdir('.'):
        if src.endswith('.po') and src.split('.')[0] in BUILD_LANGS:
            # Make a binary blob with strings sorted by ID.
            lang_id = src[:-3]
            lang = parse_po(src)
            have_ids = {msg_id for msg_id, _ in lang}
            # Take missing strings from the base language.
            for msg_id, value in BASE_STRINGS.items():
                if msg_id not in have_ids and msg_id[:-2] not in PLURALS:
                    #print('%10s' % src, 'missing:', msg_id)
                    missing_count[lang_id] += 1
                    lang.append((msg_id, value))
            compiled = bytes()
            for msg_id, msg_str in sorted(lang):
                compiled += compile_string(msg_id, msg_str)
            open(f'../res/lang/{lang_id}.bin', 'wb').write(compiled)
    # Show statistics.
    for lang_id in missing_count:
        if missing_count[lang_id] > 0:
            print('%7s: %4d missing' % (lang_id, missing_count[lang_id]))

elif MODE == 'new':
    messages = parse_po('en.po')
    f = open('new.po', 'wt', encoding='utf-8')
    for msg_id, _ in messages:
        print(f'\nmsgid "{msg_id}"\nmsgstr ""\n', file=f)

    
