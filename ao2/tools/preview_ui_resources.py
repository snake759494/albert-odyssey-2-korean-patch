"""Render translated native menu tilemaps directly from the built ROM."""
from pathlib import Path
import json
from PIL import Image
from codec import decompress
ROOT=Path(__file__).resolve().parents[2];stage=ROOT/'ao2/build/ui_stage'
r=next(stage.glob('*.sfc')).read_bytes()
report=json.loads((stage/'inventory_report.json').read_text(encoding='utf-8'))
out=ROOT/'ao2/analysis/ui_resource_previews';out.mkdir(parents=True,exist_ok=True)
colors=[(0,0,170),(0,0,170),(130,130,220),(255,255,255)]
for src,dst in report['compressed_resource_redirects'].items():
    d,_=decompress(r,int(dst,16));im=Image.new('RGB',(256,len(d)//64*8))
    for p in range(0,len(d),2):
        w=int.from_bytes(d[p:p+2],'little');t=w&1023;x=(p//2)%32;y=(p//2)//32
        for yy in range(8):
            sy=7-yy if w&0x8000 else yy;a,b=r[0x284000+t*16+sy*2:0x284000+t*16+sy*2+2]
            for xx in range(8):
                bit=xx if w&0x4000 else 7-xx
                im.putpixel((x*8+xx,y*8+yy),colors[(a>>bit&1)|((b>>bit&1)<<1)])
    im.resize((768,im.height*3),Image.Resampling.NEAREST).save(out/(src+'.png'))
print(out)
