"""Create reviewable Japanese text; OCR is a draft glyph map, never final truth."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ao2/analysis'
sys.path.insert(0,str(ROOT/'analysis_font_scan'))
from extract_all_text import chartable
mapping={i:ch for i,ch in chartable(1).items()}
mapping.update({256+i:ch for i,ch in chartable(2).items() if ch!='X'})
for page in range(5):
    data=json.loads((OUT/f'ocr_glyphs_{page}.json').read_text(encoding='utf-8-sig'))
    for line in data['lines']:
        for word in line['words']:
            if word['height']<12:continue
            text=word['text'].strip()
            if len(text)!=1:continue
            col=round((word['x']+word['width']/2-44)/60)
            row=round((word['y']+word['height']/2-48)/72)
            code=page*256+row*16+col
            if 0<=col<16 and 0<=row<16 and 0xc5<=code<0x480:
                mapping[code]=text
votes=OUT/'context_glyph_votes.json'
if votes.exists():
    for k,counts in json.loads(votes.read_text(encoding='utf-8')).items():
        if int(k,16)>=0x188 and counts:
            mapping[int(k,16)]=max(counts,key=counts.get)
fix=ROOT/'ao2/translation/chartable_fixes.json'
if fix.exists():mapping.update({int(k,16):v for k,v in json.loads(fix.read_text(encoding='utf-8')).items()})
records=json.loads((OUT/'records_raw.json').read_text())
for r in records:
    # UI pair records carry palette/flip bits as well as font code.
    r['japanese']=''.join(mapping.get(c if r['group']=='dialogue' else c&0x3ff,f'<{c:03X}>') for c in r['codes'])
(OUT/'chartable.json').write_text(json.dumps({f'{k:03X}':v for k,v in sorted(mapping.items())},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
for group in ('ui','dialogue'):
    (OUT/f'{group}_japanese.txt').write_text('\n'.join(f"{r['id']} {r['address']:06X} {r['japanese']}" for r in records if r['group']==group),encoding='utf-8')
missing=sorted({c for r in records if r['group']=='dialogue' for c in r['codes'] if c not in mapping})
(OUT/'missing_glyphs.json').write_text(json.dumps([f'{c:03X}' for c in missing]))
print('unmapped dialogue glyphs',len(missing))
