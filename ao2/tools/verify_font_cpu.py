"""Run a diagnostic-only CPU program, never the game's entry point.

Uses Snes9x's actual 65816 core to reproduce the DB=$7E raw-decoder bug and
verify every built font resource through the replacement loader/copy code.
"""
from pathlib import Path
import ctypes as C
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/analysis/font_cpu_fix';OUT.mkdir(parents=True,exist_ok=True)
source=next((ROOT/'ao2/build/ui_stage').glob('*.sfc')).read_bytes()
codes=json.loads((ROOT/'ao2/build/font_prototype/character_codes.json').read_text(encoding='utf-8'))
glyph_count=max(codes.values())+1
def program(call):
    b=bytearray();labels={};branches=[]
    def emit(s):b.extend(bytes.fromhex(s))
    def label(s):labels[s]=len(b)
    def branch(op,s):emit(op+' 00');branches.append((len(b)-1,s))
    emit('78 18 fb c2 30 a9 00 00 5b a2 ff 1f 9a e2 20 a9 7e 48 ab c2 30')
    emit('a9 5a a5 8f 80 21 7e a9 e0 24 85 0e 64 20')
    label('next');emit('a5 20 8f e0 24 7e 22 00 01 e0 c2 30')
    emit('22 '+call+' c2 30 a2 00 00 a0 03 00')
    label('compare');emit('b7 00 df 00 80 7e');branch('d0','failed')
    emit('e8 e8 c8 c8 e0 20 00');branch('d0','compare')
    emit('e6 20 a5 20 c9 '+glyph_count.to_bytes(2,'little').hex(' '));branch('90','next')
    emit('a9 0d 60 8f 00 30 7e db')
    label('failed');emit('a9 ad 0b 8f 00 30 7e db')
    for p,s in branches:
        n=labels[s]-p-1;assert -128<=n<=127;b[p]=n&255
    return b

results=[]
for name,call in [('old_raw_decoder','7c 88 c2'),('fixed_direct_copy','00 06 e0')]:
    rom=bytearray(source);code=program(call);rom[0x8000:0x8000+len(code)]=code
    rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
    path=OUT/(name+'.sfc');path.write_bytes(rom)
    runner=ROOT/'analysis_font_scan/run_headless.py'
    sys.argv=[str(runner),str(path),str(OUT)]
    ns={'__file__':str(runner),'__name__':'font_cpu_diagnostic'}
    exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
    core=ns['core']
    for _ in range(120):core.retro_run()
    ram=C.string_at(core.retro_get_memory_data(2),core.retro_get_memory_size(2))
    result={'case':name,'status_word':ram[0x3000:0x3002].hex(),
            'glyphs_verified':int.from_bytes(ram[0x20:0x22],'little'),
            'wram_2180_guard':ram[0x2180:0x2182].hex()}
    core.retro_unload_game();core.retro_deinit()
    results.append(result)
assert results[0]['status_word']=='ad0b',results
assert results[1]['status_word']=='0d60' and results[1]['glyphs_verified']==glyph_count,results
assert results[1]['wram_2180_guard']=='5aa5',results
(OUT/'report.json').write_text(json.dumps({'scope':'diagnostic program on Snes9x CPU; game entry point not executed','results':results},indent=2))
print(json.dumps(results,indent=2))
