#!/usr/bin/python3
"""Embed the translation catalog in the standalone HTML, without external requests."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
catalog = json.loads((root / 'translations.json').read_text(encoding='utf-8'))
assert isinstance(catalog.get('en'), dict)
page = root / 'index.html'
source = page.read_text(encoding='utf-8')
replacement = ('// BEGIN KOBRIAN TRANSLATIONS\nconst translations='
               + json.dumps(catalog, ensure_ascii=False, separators=(',', ':'))
               + ';\n// END KOBRIAN TRANSLATIONS')
updated, count = re.subn(r'// BEGIN KOBRIAN TRANSLATIONS\n.*?// END KOBRIAN TRANSLATIONS',
                        lambda _: replacement, source, flags=re.S)
assert count == 1, 'Translation marker missing or ambiguous'
page.write_bytes(updated.encode('utf-8'))
print('Embedded translation entries:', len(catalog['en']))
