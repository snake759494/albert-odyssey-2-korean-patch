"""Repeatable headless AO2 joypad probe; never writes the original ROM."""
import argparse
import ctypes as C
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('out');p.add_argument('commands')
p.add_argument('--state');p.add_argument('--rom',default=str(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc'))
args=p.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
rom=Path(args.rom);sha=hashlib.sha256(rom.read_bytes()).hexdigest()
runner=ROOT/'analysis_font_scan/run_headless.py'
sys.argv=[str(runner),str(rom),str(out)]
ns={'__file__':str(runner),'__name__':'ao2_probe'}
exec(compile(runner.read_text().split('for frame in range(5001):')[0],str(runner),'exec'),ns)
core=ns['core'];core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool
state=Path(args.state) if args.state else out/'latest.state'
if state.exists():
    data=state.read_bytes();buf=C.create_string_buffer(data);assert core.retro_unserialize(buf,len(data))
buttons={'b':0,'y':1,'select':2,'start':3,'up':4,'down':5,'left':6,'right':7,'a':8,'x':9,'l':10,'r':11}
pressed=set()
@ns['INPUT']
def inp(port,device,index,button):return int(port==0 and button in pressed)
core.retro_set_input_state(inp)
logpath=out/'steps.jsonl';steps=logpath.read_text().splitlines() if logpath.exists() else []
step=len(steps)+1
for command in args.commands.split(','):
    key,count=command.split(':');pressed={buttons[b] for b in key.split('+')} if key!='wait' else set()
    for _ in range(int(count)):core.retro_run()
ns['frame']=step;ns['capture']()
(out/f'frame{step:04d}.state').replace(out/'latest.state')
logpath.write_text('\n'.join(steps+[json.dumps({'step':step,'commands':args.commands,'rom_sha256':sha})])+'\n')
core.retro_unload_game();core.retro_deinit()
print(out/f'frame{step:04d}.png')
