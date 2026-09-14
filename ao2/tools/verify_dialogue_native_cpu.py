"""Exercise the integrated native dialogue renderer, without game execution."""
from pathlib import Path
import ctypes as C
import json, sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/analysis/dialogue_native_cpu';OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'Albert Odyssey 2 - Korean Full v03.sfc').read_bytes() if '--baseline' in sys.argv else next((ROOT/'ao2/build/ui_stage').glob('*.sfc')).read_bytes()
rom=bytearray(source)
# Enter the native line loop with a synthetic three-line event page. All
# text lookup, parsing, cache, glyph staging and name replacement stay native.
rom[0x207800:0x207805]=bytes.fromhex('08 5c 96 4f c2')
rom[0x207900:0x20790a]=bytes.fromhex('2a 00 2b 00 2c 00 ff ff ff ff')
b=bytearray.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00')
p=len(b);b.extend(bytes.fromhex('9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4'))
b.extend(bytes.fromhex('a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 c2 30 a9 08 00 85 2a 85 30 22 b6 c6 c2 c2 30 a9 00 79 85 00 a9 e0 00 85 02 a9 06 00 85 06 64 08 64 0c 64 10 64 12 64 2c a2 00 00 22 00 78 e0 c2 30 a9 0d 60 8f 00 30 7e db'))
rom[0x8000:0x8000+len(b)]=b;rom[0xfffc:0xfffe]=bytes.fromhex('00 80')
path=OUT/'dialogue_native.sfc';path.write_bytes(rom)
runner=ROOT/'analysis_font_scan/run_headless.py';sys.argv=[str(runner),str(path),str(OUT)]
ns={'__file__':str(runner),'__name__':'dialogue_diagnostic'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core']
for _ in range(120):core.retro_run()
ram=C.string_at(core.retro_get_memory_data(2),core.retro_get_memory_size(2))
core.retro_unload_game();core.retro_deinit()
(OUT/'ram.bin').write_bytes(ram)
print({'completion':ram[0x3000:0x3002].hex(),'dp':ram[:64].hex(' '),'glyphs':int.from_bytes(ram[0x12:0x14],'little')})
assert ram[0x3000:0x3002]==bytes.fromhex('0d60')

# Check every translated record through width lookup, window creation, native
# parsing, cached glyph staging and tile output. Event controls are unchanged.
entries=json.loads((ROOT/'ao2/build/font_prototype/inserted_dialogue.json').read_text(encoding='utf-8'))
b=bytearray.fromhex('78 18 fb c2 30 a9 00 00 5b a2 00 00 9f 00 00 7e 9f 00 00 7f e8 e8 d0 f4 a2 ff 1f 9a e2 20 a9 00 48 ab a9 80 8d 00 21 c2 30 64 40')
begin=len(b)
b.extend(bytes.fromhex('a9 5a a5 8f a0 14 7e 8f de 24 7e 8f 20 25 7e 8f d8 51 7f 8f 68 69 7f'))
b.extend(bytes.fromhex('a5 40 22 00 02 e0 c2 30 b2 08 29 1f 00 1a 4a 4a 1a 85 30 85 2a e2 20 a9 00 48 ab c2 30 22 b6 c6 c2 c2 30'))
b.extend(bytes.fromhex('a5 40 8f 00 31 7e a9 ff ff 8f 02 31 7e 8f 04 31 7e a9 00 31 85 00 a9 7e 00 85 02 a9 02 00 85 06 64 0c 64 10 64 12 64 2c 22 00 78 e0 c2 30'))
failed=[]
for address in [0x7e14a0,0x7e24de,0x7e2520,0x7f51d8,0x7f6968]:
    b+=b'\xaf'+address.to_bytes(3,'little')+bytes.fromhex('c9 5a a5 f0 03 82 00 00')
    failed.append(len(b)-2)
b.extend(bytes.fromhex('e6 40 a5 40 c9')+len(entries).to_bytes(2,'little')+bytes.fromhex('b0 03 82'))
b+=(begin-(len(b)+2)).to_bytes(2,'little',signed=True)
b.extend(bytes.fromhex('a9 0d 60 8f 00 30 7e db'))
fail=len(b);b.extend(bytes.fromhex('a9 ad 0b 8f 00 30 7e db'))
for p in failed:b[p:p+2]=(fail-p-2).to_bytes(2,'little',signed=True)
rom[0x8000:0x8000+len(b)]=b;path.write_bytes(rom)
sys.argv=[str(runner),str(path),str(OUT)]
ns={'__file__':str(runner),'__name__':'all_dialogue_diagnostic'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core']
for _ in range(4000):core.retro_run()
allram=C.string_at(core.retro_get_memory_data(2),core.retro_get_memory_size(2))
core.retro_unload_game();core.retro_deinit()
report={'scope':'isolated Snes9x CPU routines, no game playthrough',
        'opening_lines_42_44_returned':True,'completed_records':int.from_bytes(allram[0x40:0x42],'little'),
        'status':allram[0x3000:0x3002].hex(),'boundary_guards_preserved':allram[0x3000:0x3002]==bytes.fromhex('0d60')}
print(report)
assert report['status']=='0d60' and report['completed_records']==2131
(OUT/'report.json').write_text(json.dumps(report,indent=2))

