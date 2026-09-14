from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ao2/analysis'
data=(OUT/'glyphs.bin').read_bytes();glyphs=[]
for i in range(1152):
    raw=data[i*32:i*32+32];im=Image.new('RGB',(8,16),'white')
    for y in range(16):
        for x in range(8):
            im.putpixel((x,y),(0,0,0) if (raw[y*2+1]>>(7-x))&1 else (255,255,255))
    glyphs.append(im.resize((32,48),Image.Resampling.NEAREST))
records=json.loads((OUT/'records_raw.json').read_text())
records=[r for r in records if r['group']=='dialogue']
folder=OUT/'source_pages';folder.mkdir(exist_ok=True)
for page in range((len(records)+15)//16):
    image=Image.new('RGB',(32*36+32,16*72+32),'white')
    for row,r in enumerate(records[page*16:page*16+16]):
        for col,code in enumerate(r['codes']):
            image.paste(glyphs[code],(16+col*36,16+row*72))
    image.save(folder/f'page{page:03d}.png')
