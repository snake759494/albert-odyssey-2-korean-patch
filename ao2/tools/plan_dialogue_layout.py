"""Lossless candidate layout; event-script insertion remains a separate step.

Records are not assumed to be entire pages. Never apply these layouts to
choice/event scripts until their surrounding control flow is reconstructed.
"""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[2]
def tokenize(s):return re.findall(r'\{PLAYER\}|.',s)
def width(t):return 5 if t=='{PLAYER}' else 1
def dynamic(tokens):
    return {t for t in tokens if t!='{PLAYER}' and (ord(t)>=0xac00 or t in '…·,.')}
def layout(s):
    tokens=tokenize(s);lines=[];current=[];cells=0
    for token in tokens:
        n=width(token)
        if cells+n>32:lines.append(current);current=[];cells=0
        current.append(token);cells+=n
    if current:lines.append(current)
    pages=[];page=[];used=set()
    for line in lines:
        additions=dynamic(line)
        if page and (len(page)==3 or len(used|additions)>56):
            pages.append(page);page=[];used=set()
        page.append(line);used|=additions
    if page:pages.append(page)
    assert ''.join(t for p in pages for line in p for t in line)==s
    assert all(sum(map(width,line))<=32 for p in pages for line in p)
    assert all(len(p)<=3 and len(dynamic([t for line in p for t in line]))<=56 for p in pages)
    return [[''.join(line) for line in p] for p in pages]

if __name__=='__main__':
    rows=(ROOT/'ao2/translation/dialogue_0000_0134.ko.txt').read_text(encoding='utf-8').splitlines()
    raw={r['id']:r for r in json.loads((ROOT/'ao2/analysis/records_raw.json').read_text())}
    plans=[]
    for i,s in enumerate(rows):
        key=f'dialogue_{i:04d}';codes=raw[key]['codes']
        names=sum(codes[j:j+5]==[0,1,2,3,4] for j in range(max(0,len(codes)-4)))
        assert s.count('{PLAYER}')==names,(key,'name substitution changed')
        plans.append({'id':key,'korean':s,'candidate_pages':layout(s),
                      'type':'blank_control_record' if i==111 else 'choice_label' if i in [125,126,128,129,132,133] else 'dialogue',
                      'event_group_layout_verified':False})
    # Adversarial cases: all-distinct Hangul, repeated glyphs, and name tokens
    # straddling a line boundary. These do not run the game.
    for s in [''.join(chr(0xac00+i) for i in range(200)), '가'*300,
              '가'*30+'{PLAYER}'+'나'*31, '{PLAYER}'*20]:layout(s)
    target=ROOT/'ao2/translation/layout_candidates.json'
    target.write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'records':len(plans),'name_placeholders_preserved':True,
                      'records_requiring_multiple_lines':[p['id'] for p in plans if sum(map(len,p['candidate_pages']))>1],
                      'event_script_relocation_implemented':False}))
