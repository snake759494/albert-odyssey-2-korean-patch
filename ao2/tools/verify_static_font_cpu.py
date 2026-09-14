"""Execute the original font initialization loop alone and inspect its VRAM."""
from pathlib import Path
import ctypes as C
import json
import sys
from codec import decompress

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/analysis/static_font_cpu';OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
rom=bytearray(source)
# Replacement reset performs no scene initialization and never enters the game.
code=bytes.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 22 00 81 c0 c2 30 a9 0d 60 8f 00 30 7e db')
rom[0x8000:0x8000+len(code)]=code
rom[0x8100:0x8105]=bytes.fromhex('08 5c 82 cb c2')
rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
path=OUT/'native_font_loop.sfc';path.write_bytes(rom)
runner=ROOT/'analysis_font_scan/run_headless.py'
sys.argv=[str(runner),str(path),str(OUT)]
ns={'__file__':str(runner),'__name__':'static_font_diagnostic'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core']
for _ in range(1200):core.retro_run()
ram=C.string_at(core.retro_get_memory_data(2),core.retro_get_memory_size(2))
vram=C.string_at(core.retro_get_memory_data(3),core.retro_get_memory_size(3))
core.retro_unload_game();core.retro_deinit()
(OUT/'ram.bin').write_bytes(ram)
print('status',ram[0x3000:0x3002].hex(),'stack',ram[0x1fe0:0x2000].hex(' '),'dp',ram[:32].hex(' '))
assert ram[0x3000:0x3002]==bytes.fromhex('0d60')
expected=bytearray(0x3000)
for c in range(384):
    g,_=decompress(source,0x130000+int.from_bytes(source[0x130000+2*c:0x130002+2*c],'little'))
    p=(c&0xfff0)*32+(c&15)*16
    expected[p:p+16]=g[:16];expected[p+256:p+272]=g[16:]
diff=[i for i in range(0x2fc0) if vram[0x8000+i]!=expected[i]]
(OUT/'vram.bin').write_bytes(vram)
report={'scope':'original static-font loop only; no game scene executed','bytes_compared':0x2fc0,
        'mismatching_bytes':len(diff),'first_mismatches':diff[:32]}
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
assert not diff

