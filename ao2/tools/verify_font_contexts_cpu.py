"""Run only injected font switches / native resource decoder in diagnostic ROMs."""
from pathlib import Path
import ctypes as C
import json
import sys
from codec import decompress

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/analysis/font_context_cpu';OUT.mkdir(parents=True,exist_ok=True)
stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes()
inv=json.loads((stage/'inventory_report.json').read_text(encoding='utf-8'))
runner=ROOT/'analysis_font_scan/run_headless.py'
prefix=bytes.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21')
suffix=bytes.fromhex('c2 30 a9 0d 60 8f 00 30 7e db')
def execute(name,body):
    rom=bytearray(source);code=prefix+body+suffix
    assert len(code)<0x1000
    rom[0x8000:0x8000+len(code)]=code;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
    path=OUT/(name+'.sfc');path.write_bytes(rom)
    sys.argv=[str(runner),str(path),str(OUT)]
    ns={'__file__':str(runner),'__name__':'font_context_diagnostic'}
    exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
    core=ns['core'];C.memset(core.retro_get_memory_data(3),0x5a,65536)
    for _ in range(300):core.retro_run()
    ram=C.string_at(core.retro_get_memory_data(2),131072)
    vram=C.string_at(core.retro_get_memory_data(3),65536)
    core.retro_unload_game();core.retro_deinit()
    assert ram[0x3000:0x3002]==bytes.fromhex('0d60'),(name,ram[0x3000:0x3002].hex())
    return ram,vram
results=[]
for mode in [0,1,3,7,15,16,20]:
    _,vram=execute(f'scene_{mode}',bytes([0xa9,mode,0x85,0xd8])+bytes.fromhex('22 00 0a e0'))
    base=0x284000 if mode in [0,15,16] else 0x280000
    expected=bytearray(b'\x5a'*65536)
    for a,z in [(0,0x3000),(0x3000,0x3080),(0x3100,0x3180)]:expected[0x8000+a:0x8000+z]=source[base+a:base+z]
    assert vram==expected,('scene font or VRAM boundary mismatch',mode)
    results.append({'scene':mode,'font':'inventory' if base==0x284000 else 'core','vram_guards':True})
for name,body,base in [('enter_inventory',bytes.fromhex('22 00 08 e0 22 00 68 e0'),0x284000),
                       ('leave_inventory',bytes.fromhex('22 00 09 e0 22 00 60 e0'),0x280000)]:
    _,vram=execute(name,body)
    expected=bytearray(b'\x5a'*65536)
    for a,z in [(0,0x3000),(0x3000,0x3080),(0x3100,0x3180)]:expected[0x8000+a:0x8000+z]=source[base+a:base+z]
    assert vram==expected,('delta font mismatch',name)
    results.append({'case':name,'vram_guards':True})
for src,dst in inv['compressed_resource_redirects'].items():
    address=int(src,16);target=int(dst,16)
    body=bytes.fromhex('c2 30 a9')+(address&65535).to_bytes(2,'little')+bytes.fromhex('85 00 a9 c4 00 85 02 a9 00 80 85 04 a9 7e 00 85 06 22 7c 88 c2')
    ram,_=execute(f'resource_{address:x}',body)
    expected,_=decompress(source,target)
    assert ram[0x8000:0x8000+len(expected)]==expected,('resource redirect mismatch',src)
    results.append({'resource':src,'bytes_verified':len(expected)})
report={'scope':'isolated CPU/VRAM diagnostic; no game scene executed','cases':results}
(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
