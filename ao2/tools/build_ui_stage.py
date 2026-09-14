"""Internal UI integration build. This is not a release builder.

Keep all static symbols; use eight originally blank slots below the native
dialogue cache. Inventory font and direct tilemap integration are separate.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
from codec import decompress
from inventory_patch import insert_inventory
from font_context import install as install_font_context
from item_list_layout import install as install_item_list_layout
from clock_labels import TEXT as CLOCK_TEXT
from battle_item_font import install as install_battle_item_font
from battle_ui_patch import install as install_battle_ui
from field_ui_patch import install as install_field_ui
from dialogue_window import install as install_dialogue_window

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ao2/build/ui_stage';OUT.mkdir(parents=True,exist_ok=True)
original=(ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
rom=bytearray(next((ROOT/'ao2/build/font_prototype').glob('*.sfc')).read_bytes())
dialogue_window=install_dialogue_window(rom,original)
translations={int(k):v for k,v in json.loads((ROOT/'ao2/translation/ui.ko.json').read_text(encoding='utf-8')).items()}
# These records remain explicitly pending until their callers are classified.
pending={85,138,139,140,141,318,319,320,321,341,342,343}|set(range(1471,1504))
active={i:s for i,s in translations.items() if i not in pending}
hangul=sorted({c for s in active.values() for c in s if '가'<=c<='힣'})
inventory_text=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8')
inventory_text+=''.join(e['korean'] for e in json.loads((ROOT/'ao2/translation/ui_tiles.ko.json').read_text(encoding='utf-8')))+'딘'
inventory_text+=''.join(e['korean'] for e in json.loads((ROOT/'ao2/translation/menu_tilemaps.ko.json').read_text(encoding='utf-8')))
inventory_text+=CLOCK_TEXT
# Put shared glyphs first so a context change transfers a compact font tail.
hangul.sort(key=lambda c:(c not in inventory_text,c))
reserved=set(range(0x29))|set(range(0xc1,0xc5))|set(range(0x108,0x110))|{0x118,0x119}
reserved|=set(range(0x129,0x12d))|{0x130,0x131,0x136}|set(range(0x147,0x14a))|{0x151,0x154,0x15f}
reserved|=set(range(0x169,0x180))
slots=[i for i in range(0x188) if i not in reserved]
assert len(hangul)+1<=len(slots),(len(hangul)+1,len(slots))
mapping=dict(zip(hangul,slots))
mapping.update({str(i):i for i in range(10)})
mapping.update({chr(65+i):10+i for i in range(26)})
mapping.update({' ':0x28,'?':0x24,'!':0x25,'-':0x26,'/':0x27,':':slots[-1],'·':0x118,'.':0x118})
font=ImageFont.truetype('C:/Windows/Fonts/gulim.ttc',16)
def render(c):
    im=Image.new('L',(16,16),0);ImageDraw.Draw(im).text((0,0),c,font=font,fill=255)
    im=im.resize((8,16),Image.Resampling.LANCZOS)
    result=bytearray()
    for y in range(16):
        a=b=0
        for x in range(8):
            p=im.getpixel((x,y));v=3 if p>=192 else 2 if p>=80 else 1
            a|=(v&1)<<(7-x);b|=(v>>1)<<(7-x)
        result.extend((a,b))
    return bytes(result)
glyphs=[]
for c in range(0x188):
    g,_=decompress(original,0x130000+int.from_bytes(original[0x130000+2*c:0x130002+2*c],'little'))
    glyphs.append(g)
native_glyphs=glyphs.copy()
for c in hangul+[':']:glyphs[mapping[c]]=render(c)
font_bytes=bytearray(0x3200)
for c,g in enumerate(glyphs):
    p=(c&0x1f0)*32+(c&15)*16
    font_bytes[p:p+16]=g[:16];font_bytes[p+256:p+272]=g[16:]
rom[0x280000:0x283200]=font_bytes
# Preserve full A/X/Y, DB and flags. Caller is a forced-blank initialization.
b=bytearray.fromhex('08 c2 30 48 da 5a 8b e2 20 a9 00 48 ab a9 80 8d 15 21 a9 01 8d 00 43 a9 18 8d 01 43 a9 e8 8d 04 43')
for src,dest,count in [(0,0x4000,0x3000),(0x3000,0x5800,0x80),(0x3100,0x5880,0x80)]:
    b+=bytes.fromhex('c2 20 a9')+dest.to_bytes(2,'little')+bytes.fromhex('8d 16 21 a9')
    b+=src.to_bytes(2,'little')+bytes.fromhex('8d 02 43 a9')+count.to_bytes(2,'little')
    b+=bytes.fromhex('8d 05 43 e2 20 a9 01 8d 0b 42')
b+=bytes.fromhex('ab c2 30 7a fa 68 28 6b')
assert len(b)<0x100
rom[0x200800:0x200800+len(b)]=b
rom[0x2cb82:0x2cc23]=bytes.fromhex('22 00 08 e0')+b'\xea'*(0x2cc23-0x2cb82-4)
def tile(c):
    code=mapping[c]
    return ((code&0x1f0)<<1)|(code&15)
inventory_strings=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8')
inventory_strings+=''.join(r['korean'] for r in json.loads((ROOT/'ao2/translation/ui_tiles.ko.json').read_text(encoding='utf-8')))
common=set(hangul)&set(inventory_strings)
common.add('딘')
preferred='딘가나다라마바사아자차카타파하강건경고구기길노누다단대더도동두드디라란람랑래레로루리린마만명모무문미민바박반방버범보부비빈사상서선성세소수순승시신안야양어연영예오옥와왕우원위유은의이인일임장전정제종주지진창철초춘치태택토페한해현호화환황효'
name_hangul=list(dict.fromkeys(c for c in preferred if c in common))
name_hangul=(name_hangul+[c for c in sorted(common) if c not in name_hangul])[:90]
assert len(name_hangul)==90
english=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')+[' ']*54
for address,characters in [(0xfe0a0,name_hangul),(0xfe154,english)]:
    rom[address:address+180]=b''.join(tile(c).to_bytes(2,'little') for c in characters)
for address,c in [(0x21010,'딘'),(0x21016,' '),(0x2101c,' '),(0x21022,' '),(0x21028,' ')]:
    assert original[address-1]==0xa9
    rom[address:address+2]=tile(c).to_bytes(2,'little')
# Center longer Korean labels within the original frame's available interior.
grid_position_changes=[]
for grid,index in [(0xe8a1,308),(0xee2a,2),(0xee80,252)]:
    p=grid
    while original[p]!=255:
        if int.from_bytes(original[p+2:p+4],'little')==index:
            assert original[p]>0;rom[p]=original[p]-1
            grid_position_changes.append({'grid':hex(grid),'index':index,'x_before':original[p],'x_after':rom[p]})
            break
        p+=4
    else:raise AssertionError((grid,index))
# Every untranslated record is copied byte-for-byte, including graphic rows.
records=[r for r in json.loads((ROOT/'ao2/analysis/records_raw.json').read_text()) if r['group']=='ui']
cursor=0x60c60;inserted=[]
for r in records:
    i=r['index']
    if i in active:
        s=active[i];assert 1<=len(s)<=32,(i,s)
        codes=([0x4173,0x4172] if i==200 else [])+[mapping[c] for c in s]
        high=[k for k,c in enumerate(codes) if c>=0x100]
        if all(c<0x200 for c in codes) and len(high)<=6:
            payload=bytes([(len(high)<<5)|(len(codes)-1)]+high+[c&255 for c in codes])
        else:
            payload=bytes([0xe0|len(codes)-1])+b''.join(c.to_bytes(2,'little') for c in codes)
        inserted.append({'index':i,'korean':s,'codes':codes,'address':cursor,'source_cells':r['cells']})
    else:payload=original[r['address']:r['address']+r['size']]
    assert cursor+len(payload)<=0x67c9e,'UI text would overwrite bytes outside original text pool'
    rom[0x60000+i*2:0x60002+i*2]=(cursor&0xffff).to_bytes(2,'little')
    rom[cursor:cursor+len(payload)]=payload;cursor+=len(payload)
for e in inserted:
    p=int.from_bytes(rom[0x60000+e['index']*2:0x60002+e['index']*2],'little')+0x60000
    assert p==e['address']
    n=(rom[p]&31)+1
    kind=rom[p]>>5
    if kind==7:
        decoded=[int.from_bytes(rom[p+1+2*k:p+3+2*k],'little') for k in range(n)]
    else:
        high=rom[p+1:p+1+kind]
        decoded=[rom[p+1+kind+k]|(0x100 if k in high else 0) for k in range(n)]
    assert decoded==e['codes']
for c in reserved:
    p=(c&0x1f0)*32+(c&15)*16
    assert font_bytes[p:p+16]+font_bytes[p+256:p+272]==glyphs[c]
inventory=insert_inventory(rom,original,mapping,slots,glyphs,render)
font_context=install_font_context(rom,original,font_bytes,inventory['font'])
inventory['font_context_loaders_installed']=True
item_list_layout=install_item_list_layout(rom,original)
battle_item_font=install_battle_item_font(rom,original,render)
battle_ui=install_battle_ui(rom,original,mapping,slots,render)
(OUT/'battle_ui_report.json').write_text(json.dumps({k:v for k,v in battle_ui.items() if k not in ['font','panel']},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'inventory_character_codes.json').write_text(json.dumps(inventory['mapping'],ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'inventory_report.json').write_text(json.dumps({k:v for k,v in inventory.items() if k not in ['font','mapping']},ensure_ascii=False,indent=2),encoding='utf-8')
field_ui=install_field_ui(rom,original,mapping,render)
(OUT/'field_ui_report.json').write_text(json.dumps(field_ui,ensure_ascii=False,indent=2),encoding='utf8')
rom[0xffdc:0xffe0]=bytes.fromhex('ff ff 00 00');check=sum(rom)&65535
rom[0xffdc:0xffe0]=(check^65535).to_bytes(2,'little')+check.to_bytes(2,'little')
target=OUT/'Albert Odyssey 2 - UI STAGE - NOT RELEASE.sfc';target.write_bytes(rom)
(OUT/'character_codes.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'inserted_ui.json').write_text(json.dumps(inserted,ensure_ascii=False,indent=2),encoding='utf-8')
report={'status':'internal; incomplete UI integration; not release','sha256':hashlib.sha256(rom).hexdigest(),
        'ui_records_inserted':len(inserted),'hangul':len(hangul),'static_slots':len(slots),'symbols_preserved':len(reserved),
        'font_vram_writes':[[0x8000,0xb000],[0xb000,0xb080],[0xb100,0xb180]],
        'dynamic_font_vram_preserved':True,'ui_text_end':hex(cursor),'dialogue_window':dialogue_window,
        'pending_ui_ids':sorted(pending & translations.keys()),
        'name_input_hangul':''.join(name_hangul),'default_name':'딘',
        'inventory_names_inserted':len(inventory['items']),'inventory_hangul':inventory['hangul'],
        'font_context':font_context, 'field_ui':field_ui,
        'item_list_layout':item_list_layout,
        'battle_item_font':battle_item_font,
        'grid_position_changes':grid_position_changes,
        'remaining':['remaining compressed tilemaps','UI rendering and caller classification']}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
