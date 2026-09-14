import json
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ao2/analysis'
records=[r for r in json.loads((OUT/'records_raw.json').read_text()) if r['group']=='dialogue']
votes=defaultdict(Counter)
for path in sorted((OUT/'source_ocr').glob('page*.json')):
    page=int(path.stem[4:]);data=json.loads(path.read_text(encoding='utf-8-sig'))
    for line in data['lines']:
        for word in line['words']:
            text=word['text'].strip()
            if len(text)!=1 or word['width']>38 or word['height']<15:continue
            row=int((word['y']-16)//72)
            col=round((word['x']+word['width']/2-32)/36)
            index=page*16+row
            if 0<=row<16 and index<len(records) and 0<=col<len(records[index]['codes']):
                code=records[index]['codes'][col]
                if code>=0x188 and not '\u3400'<=text<='\u9fff':continue
                votes[code][text]+=1
result={f'{k:03X}':dict(v.most_common()) for k,v in sorted(votes.items())}
(OUT/'context_glyph_votes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('context voted glyphs',len(votes))
