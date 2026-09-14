"""Render real list routines using long names and the equipment/item boundary."""
from pathlib import Path
import ctypes as C
import json
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes()
mapping=json.loads((stage/'inventory_character_codes.json').read_text(encoding='utf-8'))
names=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8').splitlines()
OUT=ROOT/'ao2/analysis/item_list_cpu';OUT.mkdir(parents=True,exist_ok=True)
runner=ROOT/'analysis_font_scan/run_headless.py'
results=[]
for label,ids,entry,start_row in [('long_equipment',[83,123,125,141,143,145],0xc49d81,20),
                                 ('mixed_inventory',[1,182,183,240,241,255,143,123]*2,0xc4a699,9)]:
    rom=bytearray(source)
    b=bytearray.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 22 00 09 e0 c2 30')
    # A visible blank background allows stale cells and overlapping names to show.
    b+=bytes.fromhex('a2 00 00 a9 48 00 9f 81 82 7e e8 e8 e0 00 08 d0 f5')
    b+=bytes.fromhex('a9 ff 00 8f 61 82 7e a9 06 00 8f 53 82 7e')
    base=0x7fbb2c if entry==0xc49d81 else 0x7e2560
    for k,i in enumerate(ids):
        b+=b'\xa9'+(i|(99<<8)).to_bytes(2,'little')+b'\x8f'+(base+k*2).to_bytes(3,'little')
    b+=b'\x22'+entry.to_bytes(3,'little')+bytes.fromhex('c2 30 a9 0d 60 8f 00 30 7e db')
    rom[0x8000:0x8000+len(b)]=b;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
    path=OUT/(label+'.sfc');path.write_bytes(rom)
    sys.argv=[str(runner),str(path),str(OUT)];ns={'__file__':str(runner),'__name__':'item_list_diagnostic'}
    exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
    core=ns['core']
    for _ in range(300):core.retro_run()
    ram=C.string_at(core.retro_get_memory_data(2),131072);vram=C.string_at(core.retro_get_memory_data(3),65536)
    core.retro_unload_game();core.retro_deinit()
    (OUT/(label+'_ram.bin')).write_bytes(ram)
    assert ram[0x3000:0x3002]==bytes.fromhex('0d60'),label
    for k,i in enumerate(ids):
        y=start_row+(k//2)*2;x=2+(k%2)*15
        p=0x40000+int.from_bytes(source[0x4d1da+i*2:0x4d1dc+i*2],'little')+(i<183)
        expected=[]
        while int.from_bytes(source[p:p+2],'little')!=65535:
            expected.append(int.from_bytes(source[p:p+2],'little')&1023);p+=2
        row=0x8281+y*64
        actual=[int.from_bytes(ram[row+(x+n)*2:row+(x+n)*2+2],'little')&1023 for n in range(len(expected))]
        assert actual==expected,(label,i,names[i],actual,expected)
        assert x+len(expected)<=14+(k%2)*15
        for n in [14,15]:
            q=row+(n+(k%2)*15)*2
            assert int.from_bytes(ram[q:q+2],'little')&1023==9,(label,i,'quantity overwritten')
    im=Image.new('RGB',(256,224),(30,40,175))
    colors=[(30,40,175),(30,40,175),(120,125,205),(255,255,255)]
    for y in range(28):
        for x in range(32):
            p=0x8281+y*64+x*2;w=int.from_bytes(ram[p:p+2],'little');t=w&1023
            for yy in range(8):
                sy=7-yy if w&0x8000 else yy;a,bb=vram[0x8000+t*16+sy*2:0x8000+t*16+sy*2+2]
                for xx in range(8):
                    bit=xx if w&0x4000 else 7-xx
                    im.putpixel((x*8+xx,y*8+yy),colors[(a>>bit&1)|((bb>>bit&1)<<1)])
    im.resize((768,672),Image.Resampling.NEAREST).save(OUT/(label+'.png'))
    results.append({'case':label,'item_ids':ids,'full_names_icons_and_quantities_verified':True})
(OUT/'report.json').write_text(json.dumps({'scope':'isolated native list renderer, no game scene executed','cases':results},indent=2))
print(json.dumps(results))
