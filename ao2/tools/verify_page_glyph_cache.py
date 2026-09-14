"""Execute only the injected cache instructions in a bounded 16-bit CPU harness.

This does not run the game or emulate the PPU. Tests cover branches, stack,
register preservation, emitted tile numbers and cache write boundaries.
"""
from pathlib import Path
import json
from page_glyph_cache import build_cache_hook

CODE=build_cache_hook()
def run(ids,glyph,x=0x1234,y=0x5678):
    mem={}; writes=[]
    def addr(a):return a+0x7e0000 if a<0x2000 else a
    def rd(a):return mem.get(addr(a),0)
    def rw(a):return rd(a)|(rd(a+1)<<8)
    def wr(a,v):mem[addr(a)]=v&255;writes.append(addr(a))
    def ww(a,v):wr(a,v);wr(a+1,v>>8)
    ww(0x12,len(ids));ww(0x0e,0x24e0);ww(0x7e24e0,glyph);ww(0,0xbeef)
    for i,g in enumerate(ids):ww(0x7f5168+2*i,g)
    writes.clear()
    a=0;s=0x1ff;pc=0;carry=zero=False;steps=0
    def push(v):
        nonlocal s
        wr(s,v>>8);s-=1;wr(s,v);s-=1
    def pop():
        nonlocal s
        s+=1;lo=rd(s);s+=1;return lo|(rd(s)<<8)
    while steps<2000:
        op=CODE[pc];pc+=1;steps+=1
        def arg(n=1):
            nonlocal pc
            v=int.from_bytes(CODE[pc:pc+n],'little');pc+=n;return v
        if op==0xda:push(x)
        elif op==0x5a:push(y)
        elif op==0x7a:y=pop()
        elif op==0xfa:x=pop()
        elif op==0x48:push(a)
        elif op==0x68:a=pop()
        elif op==0xa5:a=rw(arg())
        elif op==0xb2:a=rw(0x7e0000+rw(arg()))
        elif op==0x85:ww(arg(),a)
        elif op==0xa2:x=arg(2)
        elif op==0xbf:a=rw(arg(3)+x)
        elif op==0x9f:ww(arg(3)+x,a)
        elif op in (0xe4,0xd2,0xc9):
            left=x if op==0xe4 else a
            right=rw(arg()) if op==0xe4 else (rw(0x7e0000+rw(arg())) if op==0xd2 else arg(2))
            carry=left>=right;zero=left==right
        elif op in (0xb0,0xf0,0x80):
            delta=arg();delta=delta-256 if delta>=128 else delta
            if op==0x80 or (op==0xb0 and carry) or (op==0xf0 and zero):pc+=delta
        elif op==0xe8:x=(x+1)&65535
        elif op==0x8a:a=x
        elif op==0x0a:carry=bool(a&0x8000);a=(a<<1)&65535
        elif op==0x4a:carry=bool(a&1);a>>=1
        elif op==0x18:carry=False
        elif op==0x69:
            value=a+arg(2)+carry;carry=value>65535;a=value&65535
        elif op==0x29:a &= arg(2)
        elif op==0x05:a |= rw(arg())
        elif op==0x5c:
            target=arg(3)
            return {'a':a,'x':x,'y':y,'s':s,'target':target,'writes':writes,'mem':mem,'steps':steps}
        else:raise AssertionError((hex(op),pc-1))
    raise AssertionError('hook did not terminate')

cases=0;max_steps=0
for count in range(57):
    ids=list(range(0x480,0x480+count))
    for selected in range(count):
        r=run(ids,ids[selected]);slot=selected+8
        assert r['a']==0x300+(slot&15)+((slot&0xfff0)<<1)
        assert (r['x'],r['y'],r['s'],r['target'])==(0x1234,0x5678,0x1ff,0xc2514d)
        assert not any(0x7f0000<=a<=0x7fffff for a in r['writes'])
        cases+=1;max_steps=max(max_steps,r['steps'])
    r=run(ids,0x865)
    assert (r['a'],r['x'],r['y'],r['s'],r['target'])==(0xbeef,0x1234,0x5678,0x1fb,0xc2507e)
    cache_writes=[a for a in r['writes'] if 0x7f0000<=a<=0x7fffff]
    assert cache_writes==([0x7f5168+count*2,0x7f5169+count*2] if count<56 else [])
    assert all(0x7f5168<=a<0x7f51d8 for a in cache_writes)
    cases+=1;max_steps=max(max_steps,r['steps'])
out=Path(__file__).resolve().parents[2]/'ao2/analysis/page_cache_verification.json'
out.write_text(json.dumps({'scope':'isolated injected instructions; no game or PPU execution',
    'cases_passed':cases,'max_instructions_per_case':max_steps,
    'stack_register_tile_and_write_boundary_checks':True,
    'overflow_policy':'preserve native path at 56 unique glyphs; release must prevent such pages'},indent=2))
print(out.read_text())
