import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from codec import decompress

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ao2/analysis'
rom=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
glyphs=[];font_entries=[]
for i in range(0x480):
    start=0x130000+int.from_bytes(rom[0x130000+i*2:0x130002+i*2],'little')
    data,end=decompress(rom,start)
    assert len(data)==32,(i,len(data))
    glyphs.append(data);font_entries.append({'code':i,'start':start,'end':end,'format':rom[start]})
(OUT/'glyphs.bin').write_bytes(b''.join(glyphs))
(OUT/'font_entries.json').write_text(json.dumps(font_entries,indent=2))
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for page in range(5):
    sheet=Image.new('RGB',(16*60,16*72),'white');draw=ImageDraw.Draw(sheet)
    ocr=Image.new('RGB',(16*60+32,16*72+32),'white')
    for i in range(page*256,min(page*256+256,len(glyphs))):
        g=Image.new('RGB',(8,16),'white');data=glyphs[i]
        for y in range(16):
            for x in range(8):
                v=((data[y*2]>>(7-x))&1)|(((data[y*2+1]>>(7-x))&1)<<1)
                g.putpixel((x,y),(0,0,0) if v>=2 else (255,255,255))
        g=g.resize((40,48),Image.Resampling.NEAREST)
        x=(i%16)*60;y=(i//16%16)*72
        sheet.paste(g,(x+8,y+18));draw.text((x,y),f'{i:03X}',font=font,fill='black')
        ocr.paste(g,(x+24,y+24))
    sheet.save(OUT/f'glyphs_{page}.png');ocr.save(OUT/f'ocr_glyphs_{page}.png')

records=[]
for group,table,count in [('ui',0x60000,0xc60//2),('dialogue',0x70000,0x10a6//2)]:
    for index in range(count):
        local=int.from_bytes(rom[table+index*2:table+index*2+2],'little')
        bank=(0x60000 if group=='ui' else (0x70000 if index<0x700 else 0x170000))
        start=bank+local;header=rom[start];kind=header>>5;n=(header&31)+1
        if kind==7:
            pairs=[int.from_bytes(rom[start+1+i*2:start+3+i*2],'little') for i in range(n)]
            end=start+1+n*2
        else:
            flags=rom[start+1:start+1+kind];pairs=list(rom[start+1+kind:start+1+kind+n])
            for flag in flags:
                position=flag&31 if group=='dialogue' else flag
                if position>=n:raise ValueError((group,index,start,flag,n))
                pairs[position]|=((flag&0xe0)<<3) if group=='dialogue' else 0x100
            end=start+1+kind+n
        records.append({'id':f'{group}_{index:04d}','group':group,'index':index,'bank':0xc0+(bank>>16),'address':start,'local':local,'kind':kind,'cells':n,'size':end-start,'codes':pairs})
(OUT/'records_raw.json').write_text(json.dumps(records,indent=2))
used={c for r in records for c in r['codes']}
print(json.dumps({'glyphs':len(glyphs),'unique_glyphs':len(set(glyphs)),'records':len(records),'used_codes':len(used),'highest_code':max(used)}))
