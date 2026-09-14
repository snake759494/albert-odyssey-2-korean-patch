"""Find translated text growing into borders or other fields in native grids."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
rom=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
patched=next((ROOT/'ao2/build/ui_stage').glob('*.sfc')).read_bytes()
records={r['index']:r for r in json.loads((ROOT/'ao2/analysis/records_raw.json').read_text()) if r['group']=='ui'}
translated={r['index']:r for r in json.loads((ROOT/'ao2/build/ui_stage/inserted_ui.json').read_text(encoding='utf-8'))}
refs={}
for p in range(3,len(rom)-6):
    if rom[p-3]==0xa9 and rom[p:p+6]==bytes.fromhex('85 00 22 11 cd c2'):
        refs.setdefault(int.from_bytes(rom[p-2:p],'little'),[]).append(p-3)
grids=[];conflicts=[]
for address,callers in sorted(refs.items()):
    p=address;entries=[]
    while rom[p]!=255:
        x,y=patched[p:p+2];i=int.from_bytes(rom[p+2:p+4],'little')
        if x>31 or y>31 or i not in records:break
        entries.append({'x':x,'y':y,'index':i});p+=4
        assert len(entries)<256
    else:
        canvas={}
        for ordinal,e in enumerate(entries):
            for k,c in enumerate(records[e['index']]['codes']):
                if c&511 in [0x28,0x151]:continue
                for dy in [0,1]:canvas[e['x']+k,e['y']+dy]=(ordinal,e['index'],c&511)
        for ordinal,e in enumerate(entries):
            i=e['index']
            if i not in translated:continue
            old=records[i]['cells'];new=len(translated[i]['codes'])
            if new<=old:continue
            for k in range(old,new):
                for dy in [0,1]:
                    pos=e['x']+k,e['y']+dy
                    occupant=canvas.get(pos)
                    # Button captions are deliberately written over the interior
                    # horizontal rails; corners and outside edges stay protected.
                    if occupant and occupant[2] in [0x12b,0x136,0x10e,0x10f]:occupant=None
                    if pos[0]>31 or pos[1]>31 or (occupant and occupant[0]!=ordinal):
                        conflicts.append({'grid':f'{address:04X}','index':i,'text':translated[i]['korean'],
                                          'cell':pos,'other_record':occupant[1] if occupant else None})
        grids.append({'address':f'{address:04X}','callers':[f'{x:06X}' for x in callers],'entries':entries})
report={'scope':'known immediate C2CD11 grid references, conservative static collision candidates',
        'grids':grids,'growth_conflicts':conflicts}
(ROOT/'ao2/analysis/ui_grid_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'grids':len(grids),'conflicts':conflicts},ensure_ascii=False))
