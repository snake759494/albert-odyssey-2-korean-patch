"""Native battle HUD/name/notification regression, without running a scene."""
from pathlib import Path
import ctypes as C
import json,sys
from PIL import Image
from codec import decompress
ROOT=Path(__file__).resolve().parents[2];stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes();original=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
report=json.loads((stage/'battle_ui_report.json').read_text(encoding='utf-8'));mapping=report['mapping']
ui=json.loads((ROOT/'ao2/translation/ui.ko.json').read_text(encoding='utf-8'))
OUT=ROOT/'ao2/analysis/battle_ui_cpu';OUT.mkdir(parents=True,exist_ok=True)
runner=ROOT/'analysis_font_scan/run_headless.py'
def tile(c):
 n=mapping[c];return ((n&0x1f0)<<1)|(n&15)
def execute(body):
 rom=bytearray(source)
 code=bytes.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 c2 30 a9 02 00 85 d8 22 00 70 e0')+body+bytes.fromhex('c2 30 a9 0d 60 8f 00 30 7e db')
 rom[0x8000:0x8000+len(code)]=code;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
 # Stop immediately after the native HUD copying loops, before scene logic.
 rom[0x53d27]=0x6b
 path=OUT/'probe.sfc';path.write_bytes(rom)
 sys.argv=[str(runner),str(path),str(OUT)];ns={'__file__':str(runner),'__name__':'battle_ui_diagnostic'}
 exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
 core=ns['core'];C.memset(core.retro_get_memory_data(3),0x5a,65536)
 for _ in range(100):core.retro_run()
 ram=C.string_at(core.retro_get_memory_data(2),131072);vram=C.string_at(core.retro_get_memory_data(3),65536)
 core.retro_unload_game();core.retro_deinit()
 assert ram[0x3000:0x3002]==bytes.fromhex('0d60')
 assert vram[:0x8000]==b'\x5a'*0x8000 and vram[0xb000:]==b'\x5a'*0x5000
 assert vram[0x8000:0xb000]==source[0x28c000:0x28f000]
 return ram,vram
ram,vram=execute(bytes.fromhex('22 ce 3c c5'))
data,_=decompress(source,0x2d0000)
for x,y,n,s in report['hud_labels']:
 for k,c in enumerate(s.ljust(n)):
  for row in range(2):
   p=0xa002+(y+row)*64+(x+k)*2
   assert int.from_bytes(ram[p:p+2],'little')&1023==tile(c)+row*16,(s,k,row)
# A focused preview of the actual HUD text emitted by the native routine.
preview=Image.new('RGB',(256,56),(10,20,70));colors=[(10,20,70),(10,20,70),(140,150,190),(255,255,255)]
for x,y,n,s in report['hud_labels']:
 for k in range(n):
  for row in range(2):
   p=0xa002+(y+row)*64+(x+k)*2;t=int.from_bytes(ram[p:p+2],'little')&1023
   for yy in range(8):
    a,b=vram[0x8000+t*16+yy*2:0x8000+t*16+yy*2+2]
    for xx in range(8):preview.putpixel(((x+k)*8+xx,(y+row)*8+yy),colors[(a>>(7-xx)&1)|((b>>(7-xx)&1)<<1)])
preview.resize((768,168),Image.Resampling.NEAREST).save(OUT/'hud_text.png')
cases=[]
for unit in [next(i for i in range(114) if int.from_bytes(original[0x12e2+i*2:0x12e4+i*2],'little')==3),40,48,57,64,65,68,69]:
 name=ui[str(int.from_bytes(original[0x12e2+unit*2:0x12e4+unit*2],'little'))]
 body=b'\xa9'+unit.to_bytes(2,'little')+bytes.fromhex('8d 03 02 a9 80 00 85 2a 64 b5 22 6d 30 c5')
 ram,_=execute(body)
 text=name+'의 공격!'
 for k,c in enumerate(text):
  for row in range(2):
   p=0x9594+k*2+row*64
   assert int.from_bytes(ram[p:p+2],'little')&1023==tile(c)+row*16,(unit,text,k,row,ram[p:p+2].hex())
 cases.append({'unit':unit,'text':text,'cells':len(text)})
# All 114 translated unit names crossed with all literal notifications fit.
names=[ui.get(str(int.from_bytes(original[0x12e2+i*2:0x12e4+i*2],'little')),'') for i in range(114)]
literal=[s for s in report['strings'] if not s['text'].startswith('native')]
assert all(len(name)+len(s['words'])<=14 for name in names for s in literal)
result={'scope':'isolated native HUD and notification CPU routines; no game scene executed',
 'hud_labels_verified':len(report['hud_labels']),'notification_cases':cases,
 'name_notification_width_combinations':len(names)*len(literal),'vram_at_or_above_b000_untouched':True}
(OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
