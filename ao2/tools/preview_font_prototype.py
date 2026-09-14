"""Render font bytes read back from the prototype ROM; not an emulator capture."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from codec import decompress

root=Path(__file__).resolve().parents[2]
p=root/'ao2/build/font_prototype'
rom=next(p.glob('*.sfc')).read_bytes()
rows=json.loads((p/'inserted_dialogue.json').read_text(encoding='utf-8'))
out=Image.new('RGB',(1280,len(rows)*100+48),'white')
draw=ImageDraw.Draw(out)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
draw.text((12,8),'ROM glyph preview - not an emulator screenshot',font=font,fill='black')
for i,r in enumerate(rows):
    draw.text((12,45+i*100),r['id'],font=font,fill='#666666')
    for j,code in enumerate(r['codes']):
        addr=((rom[0x212000+2*code]-0xc0)<<16)|int.from_bytes(rom[0x210000+2*code:0x210002+2*code],'little')
        data,_=decompress(rom,addr)
        im=Image.new('RGB',(8,16),'white')
        for y in range(16):
            for x in range(8):
                im.putpixel((x,y),(0,0,0) if data[y*2+1]&(128>>x) else (255,255,255))
        out.paste(im.resize((32,64),Image.Resampling.NEAREST),(225+j*32,45+i*100))
out.save(p/'glyph_preview.png')
print(p/'glyph_preview.png')
