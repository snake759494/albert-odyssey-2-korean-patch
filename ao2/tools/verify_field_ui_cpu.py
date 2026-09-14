"""Native CPU tests for field-font boundaries, cache hits and code remapping."""
from pathlib import Path
import ctypes as C,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ao2/analysis/field_ui_cpu';OUT.mkdir(parents=True,exist_ok=True)
source=next((ROOT/'ao2/build/ui_stage').glob('*.sfc')).read_bytes()
report=json.loads((ROOT/'ao2/build/ui_stage/field_ui_report.json').read_text(encoding='utf8'))
runner=ROOT/'analysis_font_scan/run_headless.py'
prefix=bytes.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21')
def execute(name,body):
 r=bytearray(source);b=prefix+body+bytes.fromhex('c2 30 a9 0d 60 8f 00 30 7e db');r[0x8000:0x8000+len(b)]=b;r[0xfffc:0xfffe]=bytes.fromhex('00 80')
 path=OUT/(name+'.sfc');path.write_bytes(r);sys.argv=[str(runner),str(path),str(OUT)]
 ns={'__file__':str(runner),'__name__':'field_diagnostic'};exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
 core=ns['core'];C.memset(core.retro_get_memory_data(3),0x5a,65536)
 for _ in range(180):core.retro_run()
 ram=C.string_at(core.retro_get_memory_data(2),131072);vram=C.string_at(core.retro_get_memory_data(3),65536)
 core.retro_unload_game();core.retro_deinit();assert ram[0x3000:0x3002]==bytes.fromhex('0d60'),name
 return ram,vram
body=bytes.fromhex('a9 01 85 d8 22 00 e0 e0')
ram,vram=execute('font_load',body)
expected=bytearray(b'\x5a'*65536);expected_ram=bytearray(0x800)
for off,n in report['font_segments']:
 data=source[0x2c0000+off:0x2c0000+off+n];expected[0xb000+off:0xb000+off+n]=data;expected_ram[off:off+n]=data
assert vram==expected,'VRAM outside field glyph segments changed'
assert ram[0x16168:0x16968]==expected_ram,'font staging boundary changed'
# Once staged, the second call must not DMA. Modify one glyph VRAM word first.
body+=bytes.fromhex('c2 30 a9 40 58 8d 16 21 a9 ef be 8d 18 21 e2 20 22 00 e0 e0')
_,vram=execute('cache_hit',body);expected[0xb080:0xb082]=bytes.fromhex('efbe');assert vram==expected,'cache hit uploaded glyphs again'
m=report['mapping'];old=json.loads((ROOT/'ao2/build/ui_stage/character_codes.json').read_text(encoding='utf8'))
values=list(range(0x17c,0x194))+[0x1ff,0xffff,0,4,0x400,0x180,0x187,0x188]
for mode in [0,1,2,3,4,7,12,15,16,20]:
 b=bytearray([0xa9,mode,0x85,0xd8,0xc2,0x30]);b+=bytes.fromhex('a9 5a a5 8f de 24 7e 8f 20 25 7e')
 for i,n in enumerate(values):b+=b'\xa9'+n.to_bytes(2,'little')+b'\x8f'+(0x7e24e0+i*2).to_bytes(3,'little')
 b+=bytes.fromhex('22 00 f0 e0');r,_=execute('remap_'+str(mode),b)
 expected_values=[m[next(c for c,k in old.items() if k==n)] if mode in [1,3,4] and 0x180<=n<0x188 else n for n in values]
 assert r[0x24e0:0x2520]==b''.join(n.to_bytes(2,'little') for n in expected_values),('remap',mode)
 assert r[0x24de:0x24e0]==r[0x2520:0x2522]==bytes.fromhex('5aa5')
summary={'font_segments':report['font_segments'],'vram_outside_segments_unchanged':True,'staging_boundaries_preserved':True,'cache_hit_no_dma':True,'remap_modes_tested':[0,1,2,3,4,7,12,15,16,20],'parsed_buffer_guards_preserved':True}
(OUT/'report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
