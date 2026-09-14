"""Conservative candidate inventory; code/data references still require review."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
r=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
ct=json.loads((ROOT/'ao2/analysis/chartable.json').read_text(encoding='utf-8'))
def decode(w):
    if w&0x800:return f'<ICON:{w:04X}>'
    c=((w&0x3e0)>>1)|(w&15)
    return ct.get(f'{c:03X}',f'<{w:04X}>')
rows=[]
for lo,hi in [(0x47000,0x48700),(0x4d3da,0x4d458),(0x4ee2a,0x4f36d)]:
    p=lo
    while p<hi:
        q=p;ws=[]
        while q<hi and len(ws)<40:
            w=int.from_bytes(r[q:q+2],'little');q+=2
            if w==65535:break
            if w&0x1000 or (w&0x3ff)>=0x300 or w&0x10:break
            ws.append(w)
        s=''.join(decode(w) for w in ws)
        if len(ws)>=2 and w==65535:
            rows.append({'address':p,'end':q,'tiles':ws,'japanese':s});p=q
        else:p+=1
(ROOT/'ao2/analysis/ui_tiles.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(f"{a['address']:06X} {len(a['tiles']):2d} {a['japanese']}" for a in rows))
