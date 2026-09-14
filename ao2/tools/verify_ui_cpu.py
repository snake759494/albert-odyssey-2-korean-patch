"""Isolated Snes9x CPU checks for UI parsing, font DMA, and name-grid layout."""
from pathlib import Path
import ctypes as C
import json
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/analysis/ui_cpu';OUT.mkdir(parents=True,exist_ok=True)
stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes()
entries=json.loads((stage/'inserted_ui.json').read_text(encoding='utf-8'))
rom=bytearray(source)
for ordinal,e in enumerate(entries):
    rom[0x290000+ordinal*2:0x290002+ordinal*2]=e['index'].to_bytes(2,'little')
    for k,code in enumerate(e['codes']):rom[0x2a0000+ordinal*64+k*2:0x2a0002+ordinal*64+k*2]=code.to_bytes(2,'little')
    rom[0x2b0000+ordinal]=len(e['codes'])
b=bytearray();labels={};fixups=[]
def emit(s):b.extend(bytes.fromhex(s))
def label(s):labels[s]=len(b)
def branch(op,target):emit(op+' 00');fixups.append((len(b)-1,target))
emit('78 18 fb c2 30 a9 00 00 5b a2 00 00')
label('clear');emit('9f 00 00 7e 9f 00 00 7f e8 e8');branch('d0','clear')
emit('a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 22 00 08 e0 c2 30 64 20')
label('next')
emit('a9 5a a5 8f de 24 7e 8f 20 25 7e a5 20 0a aa bf 00 00 e9 0a aa bf 00 00 c6 85 00 e2 20 a9 c6 48 ab c2 30 22 7e 37 c4 c2 30')
emit('af de 24 7e c9 5a a5');branch('d0','failed')
emit('af 20 25 7e c9 5a a5');branch('d0','failed')
emit('a6 20 bf 00 00 eb 29 ff 00 c5 02');branch('d0','failed')
emit('a5 20 0a 0a 0a 0a 0a 0a aa a0 00 00')
label('compare');emit('bf 00 00 ea d1 00');branch('d0','failed')
emit('e8 e8 c8 c8 c6 02');branch('d0','compare')
emit('e6 20 a5 20 c9 '+len(entries).to_bytes(2,'little').hex(' '));branch('90','next')
emit('e2 20 a9 00 48 ab a9 07 85 d8 64 46 c2 30 22 95 23 c4 22 15 e0 cf c2 30 a9 0d 60 8f 00 30 7e db')
label('failed');emit('a9 ad 0b 8f 00 30 7e db')
for p,target in fixups:
    offset=labels[target]-p-1;assert -128<=offset<=127,(target,offset);b[p]=offset&255
rom[0x8000:0x8000+len(b)]=b;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
path=OUT/'ui_native_routines.sfc';path.write_bytes(rom)
runner=ROOT/'analysis_font_scan/run_headless.py';sys.argv=[str(runner),str(path),str(OUT)]
ns={'__file__':str(runner),'__name__':'ui_cpu_diagnostic'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core']
for _ in range(1200):core.retro_run()
ram=C.string_at(core.retro_get_memory_data(2),core.retro_get_memory_size(2))
vram=C.string_at(core.retro_get_memory_data(3),core.retro_get_memory_size(3))
core.retro_unload_game();core.retro_deinit()
(OUT/'ram.bin').write_bytes(ram);(OUT/'vram.bin').write_bytes(vram)
assert ram[0x3000:0x3002]==bytes.fromhex('0d60'),(ram[0x3000:0x3002].hex(),ram[0x20:0x22].hex())
for start,end in [(0,0x3000),(0x3000,0x3080),(0x3100,0x3180)]:
    assert vram[0x8000+start:0x8000+end]==source[0x280000+start:0x280000+end]
# Preview the tilemap produced by the native routines, using a diagnostic palette.
im=Image.new('RGB',(256,224),(30,40,175))
for ty in range(28):
    for tx in range(32):
        p=0xca0+(ty*32+tx)*2;word=int.from_bytes(ram[p:p+2],'little')
        tile=word&1023;palette=(word>>10)&7
        colors=[(30,40,175),(30,40,175),(120,125,205),(255,255,255)]
        if palette==4:colors=[(30,40,175),(30,40,175),(170,145,20),(255,230,20)]
        for y in range(8):
            sy=7-y if word&0x8000 else y
            a,bits=vram[0x8000+tile*16+sy*2:0x8000+tile*16+sy*2+2]
            for x in range(8):
                sx=x if word&0x4000 else 7-x
                im.putpixel((tx*8+x,ty*8+y),colors[(a>>sx&1)|((bits>>sx&1)<<1)])
im.resize((768,672),Image.Resampling.NEAREST).save(OUT/'name_grid_diagnostic.png')
report={'scope':'native UI routines on isolated diagnostic ROM; no game scene executed',
        'ui_records_verified':len(entries),'parse_buffer_guards_preserved':True,'static_font_dma_roundtrip':True,
        'name_grid_native_layout_executed':True,'preview_palette':'diagnostic approximation'}
(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
