"""Verify all 64 native clock phases using isolated native CPU calls."""
from pathlib import Path
import ctypes as C
import json,sys
ROOT=Path(__file__).resolve().parents[2];stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes()
mapping=json.loads((stage/'inventory_character_codes.json').read_text(encoding='utf-8'))
OUT=ROOT/'ao2/analysis/clock_cpu';OUT.mkdir(parents=True,exist_ok=True)
runner=ROOT/'analysis_font_scan/run_headless.py'
rom=bytearray(source)
b=bytearray.fromhex('78 18 fb c2 30 a9 00 00 5b a2 ff 1f 9a e2 20 a9 00 48 ab c2 30')
for phase in range(64):
    b+=b'\xa9'+phase.to_bytes(2,'little')+bytes.fromhex('85 ce 22 a1 9a c4')
    for k in range(6):
        for row in range(2):
            b+=b'\xaf'+(0x7e954f+k*2+row*64).to_bytes(3,'little')
            b+=b'\x8f'+(0x7f0000+phase*24+k*2+row*12).to_bytes(3,'little')
b+=bytes.fromhex('a9 0d 60 8f 00 30 7e db')
assert len(b)<0x3000
rom[0x8000:0x8000+len(b)]=b;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
path=OUT/'clock.sfc';path.write_bytes(rom)
sys.argv=[str(runner),str(path),str(OUT)];ns={'__file__':str(runner),'__name__':'clock_diagnostic'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core']
for _ in range(300):core.retro_run()
ram=C.string_at(core.retro_get_memory_data(2),131072)
core.retro_unload_game();core.retro_deinit()
assert ram[0x3000:0x3002]==bytes.fromhex('0d60')
def tile(c):
    n=mapping[c];return ((n&0x1f0)<<1)|(n&15)
for phase in range(64):
    text=' 오후' if 16<=phase<48 else ' 오전'
    for k,c in list(enumerate(text))+[(5,'시')]:
        for row in range(2):
            p=0x10000+phase*24+k*2+row*12
            assert int.from_bytes(ram[p:p+2],'little')==tile(c)+row*16,(phase,k,row)
report={'scope':'isolated CPU; no game scene executed','clock_phases_verified':64,'korean_labels_verified':True}
(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
