"""Check isolated item notification font DMA and native caption writes."""
from pathlib import Path
import ctypes as C
import json,sys
ROOT=Path(__file__).resolve().parents[2];stage=ROOT/'ao2/build/ui_stage'
source=next(stage.glob('*.sfc')).read_bytes()
names=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8').splitlines()
OUT=ROOT/'ao2/analysis/battle_item_cpu';OUT.mkdir(parents=True,exist_ok=True)
runner=ROOT/'analysis_font_scan/run_headless.py'
ids=sorted({next(i for i,s in enumerate(names) if len(s)==n) for n in set(map(len,names))}|{203,204,255})
results=[]
for i in ids:
    rom=bytearray(source)
    b=bytearray.fromhex('78 18 fb c2 30 a9 00 00 5b a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 c2 30 a2')+(i*2).to_bytes(2,'little')
    b+=bytes.fromhex('22 00 0e e0 c2 30 a9 0d 60 8f 00 30 7e db')
    rom[0x8000:0x8000+len(b)]=b;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
    path=OUT/'probe.sfc';path.write_bytes(rom)
    sys.argv=[str(runner),str(path),str(OUT)];ns={'__file__':str(runner),'__name__':'battle_item_diagnostic'}
    exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
    core=ns['core'];C.memset(core.retro_get_memory_data(3),0x5a,65536)
    C.memset(core.retro_get_memory_data(2),0x5a,131072)
    # Native NMI/HDMA remain off for the fixture, but the loader still waits for VBlank.
    rp=core.retro_get_memory_data(2);C.memset(rp+0x64,0,2)
    for _ in range(100):core.retro_run()
    ram=C.string_at(core.retro_get_memory_data(2),131072);vram=C.string_at(core.retro_get_memory_data(3),65536)
    core.retro_unload_game();core.retro_deinit()
    assert ram[0x3000:0x3002]==bytes.fromhex('0d60'),i
    bank=int.from_bytes(source[0x220200+2*i:0x220202+2*i],'little')-0xc0
    ptr=int.from_bytes(source[0x220000+2*i:0x220002+2*i],'little')+bank*65536
    expected=bytearray(b'\x5a'*65536);p=ptr
    for dest,n in [(0xb080,128),(0xb180,128),(0xb200,32),(0xb300,32)]:expected[dest:dest+n]=source[p:p+n];p+=n
    assert vram==expected,('VRAM DMA boundary or bank mismatch',i)
    for k in range(10):
        n=0x188+k;t=((n&0x1f0)<<1)|(n&15)|0x3000
        for row in range(2):
            p=0x13fc+k*2+row*64
            want=t+row*16 if k<len(names[i]) else 0x5a5a
            assert int.from_bytes(ram[p:p+2],'little')==want,(i,k,row)
    results.append({'item':i,'cells':len(names[i]),'font_and_caption_guards':True})
report={'scope':'isolated CPU; no game scene executed','cases':results}
(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
