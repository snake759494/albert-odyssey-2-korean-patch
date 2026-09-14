"""Extract native CB event selection and dialogue/control word lists."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
rom=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
bank=rom[0xb0000:0xc0000]
def u16(p):return int.from_bytes(bank[p:p+2],'little')
roots=sorted({u16(i*2) for i in range(512)})
events=[];scripts={};boundaries=set(roots)|{0x10000};unresolved=[]
for root in roots:
    first=u16(root+1)
    if first<=root or (first-root-1)%2:
        unresolved.append({'root':root,'first_pointer':first});continue
    count=(first-root-1)//2
    assert 0<count<256,(root,count)
    conditions=[]
    for slot in range(count):
        p=u16(root+1+slot*2);chain=[]
        for _ in range(256):
            flag,mask=bank[p:p+2];script=u16(p+2)
            chain.append({'address':p,'flag':flag,'mask':mask,'script':script})
            boundaries.add(p);boundaries.add(script)
            scripts[script]={'address':script}
            if mask==0:break
            p+=4
        else:raise ValueError(('condition loop',root,slot))
        conditions.append(chain)
    events.append({'root':root,'first_phase':bank[root],'conditions':conditions})
for script,entry in scripts.items():
    end=min(x for x in boundaries if x>script)
    words=[];invalid=[]
    for q in range(script,end-1,2):
        w=u16(q)
        if not (w<2131 or w>=0x8000):
            invalid.append({'address':q,'value':w});break
        words.append(w)
        if w==0xffff:break
    entry.update(words=words,word_count=len(words),boundary=end,invalid_words=invalid)
out=ROOT/'ao2/analysis/event_scripts.json'
out.write_text(json.dumps({'events':events,'scripts':list(scripts.values()),'unresolved_roots':unresolved},indent=2))
print(json.dumps({'event_roots':len(events),'unique_scripts':len(scripts),
                 'longest_script_words':max(s['word_count'] for s in scripts.values()),
                 'invalid_scripts':sum(bool(s['invalid_words']) for s in scripts.values()),'unresolved_roots':unresolved}))
