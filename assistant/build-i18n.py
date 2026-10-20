"""Embed desktop assistant translations. No network resources at runtime."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parent
catalog=json.loads((root/'translations.json').read_text(encoding='utf-8'))
script='const KOBRIAN_TRANSLATIONS='+json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+';\n'+(root/'i18n.js').read_text(encoding='utf-8')
page=root/'index.html'
source=page.read_text(encoding='utf-8')
block='<!-- BEGIN ASSISTANT I18N -->\n<script>\n'+script+'\n</script>\n<!-- END ASSISTANT I18N -->'
if '<!-- BEGIN ASSISTANT I18N -->' in source:
    source,count=re.subn(r'<!-- BEGIN ASSISTANT I18N -->.*?<!-- END ASSISTANT I18N -->',lambda _:block,source,flags=re.S)
    assert count==1
else:
    source=source.replace('</body>',block+'\n</body>')
page.write_bytes(source.encode('utf-8'))
print('Embedded assistant translations:',len(catalog['en']))
