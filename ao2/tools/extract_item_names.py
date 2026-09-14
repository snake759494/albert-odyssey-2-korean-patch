from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
r=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
chart=json.loads((ROOT/'ao2/analysis/chartable.json').read_text(encoding='utf-8'))
def decode(tile):
    c=((tile&0x3e0)>>1)|(tile&15)
    return f'<ICON:{tile:04X}>' if tile&0x800 else chart.get(f'{c:03X}', f'<{c:03X}>')
items=[]
for i in range(256):
    p=0x40000+int.from_bytes(r[0x4d1da+i*2:0x4d1dc+i*2],'little')
    q=p+(i<183);words=[]
    while True:
        w=int.from_bytes(r[q:q+2],'little');q+=2
        if w==0xffff:break
        words.append(w)
        assert len(words)<=32,(i,p)
    items.append({'index':i,'address':p,'name_address':p+(i<183),'end_name':q,
                  'tiles':words,'japanese':''.join(decode(w) for w in words)})
(ROOT/'ao2/analysis/items.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'ao2/analysis/items_japanese.txt').write_text('\n'.join(f"{a['index']:03d} {a['address']:06X} {a['japanese']}" for a in items),encoding='utf-8')
print((ROOT/'ao2/analysis/items_japanese.txt').read_text(encoding='utf-8'))
