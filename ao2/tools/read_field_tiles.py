from pathlib import Path
import json,sys
ct={int(k,16):v for k,v in json.loads(Path('ao2/analysis/chartable.json').read_text(encoding='utf8')).items()}
b=Path(sys.argv[1]).read_bytes()
for p in range(int(sys.argv[2],16) if len(sys.argv)>2 else 0xca0,int(sys.argv[3],16) if len(sys.argv)>3 else 0x1420,64):
 w=[int.from_bytes(b[q:q+2],'little') for q in range(p,p+64,2)]
 s=''.join(ct.get(((n&0x3e0)>>1)|(n&15),'?') if n&16==0 else ' ' for n in w)
 if s.strip():print(hex(p),s, ' '.join(f'{n:04x}' for n in w))

