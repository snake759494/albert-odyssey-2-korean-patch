"""Build an explicitly non-release AO2 expanded-font/text integration prototype.

All counted dialogue records are inserted. Menu integration remains a separate
step. No emulator is launched by this tool.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
from codec import decompress, raw_resource
from page_glyph_cache import build_cache_hook
from translation_data import load_dialogue

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'ao2/build/font_prototype'
OUT.mkdir(parents=True, exist_ok=True)
original = (ROOT/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
assert hashlib.sha256(original).hexdigest() == '7c6fe76fe1a414407435c7393f4d9b50a885fa6055cd9d94549725884497698b'
rom = bytearray(original + b'\xff'*0x200000)
records = [r for r in json.loads((ROOT/'ao2/analysis/records_raw.json').read_text()) if r['group']=='dialogue']
translations = load_dialogue()
assert len(translations)==2131
used = sorted({c for s in translations.values() for c in s if '\uac00'<=c<='\ud7a3'})
hangul = list(used)
for value in range(0xac00,0xd7a4):
    if len(hangul)>=1000: break
    if chr(value) not in hangul: hangul.append(chr(value))
assert len(hangul)==1000
extras = sorted({c for s in translations.values() for c in s.replace('{PLAYER}','')
                 if not ('가'<=c<='힣') and c not in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ 「」?!'})
char_codes = {c:0x480+i for i,c in enumerate(hangul+extras)}
char_codes.update({str(i):i for i in range(10)})
char_codes.update({chr(65+i):10+i for i in range(26)})
char_codes.update({' ':0x28,'「':0xc1,'」':0xc2,'?':0x24,'!':0x25})
font = ImageFont.truetype('C:/Windows/Fonts/gulim.ttc',16)
def render(c):
    image=Image.new('L',(16,16),0)
    ImageDraw.Draw(image).text((0,0),c,font=font,fill=255)
    image=image.resize((8,16),Image.Resampling.LANCZOS)
    image=image.point(lambda p:3 if p>=192 else (2 if p>=80 else 1))
    data=bytearray()
    for y in range(16):
        p0=p1=0
        for x in range(8):
            v=image.getpixel((x,y));p0|=(v&1)<<(7-x);p1|=((v>>1)&1)<<(7-x)
        data.extend((p0,p1))
    return bytes(data)

glyphs=[]
for code in range(0x480):
    start=0x130000+int.from_bytes(original[0x130000+2*code:0x130002+2*code],'little')
    data,_=decompress(original,start);assert len(data)==32;glyphs.append(data)
glyphs += [render(c) for c in hangul+extras]
assert len(glyphs)<0x1000
assert len(set(glyphs[0x480:0x480+1000]))==1000, 'indistinguishable Hangul glyphs'
font_addresses=[]
cursor=0x230000
for code,data in enumerate(glyphs):
    payload=raw_resource(data)
    if (cursor&0xffff)+len(payload)>0x10000:cursor=(cursor+0xffff)&~0xffff
    assert cursor+len(payload)<=0x250000
    rom[cursor:cursor+len(payload)]=payload
    rom[0x210000+2*code:0x210002+2*code]=(cursor&0xffff).to_bytes(2,'little')
    # A word per entry makes lookup constant-time with the doubled glyph index.
    rom[0x212000+2*code:0x212002+2*code]=(0xc0+(cursor>>16)).to_bytes(2,'little')
    font_addresses.append(cursor);cursor+=len(payload)

text_cursor=0x250000
inserted=[]
for r in records:
    i=r['index'];ptr=r['local'];bank=r['bank']
    if i in translations:
        s=translations[i]
        codes=[]
        import re
        for token in re.findall(r'\{PLAYER\}|.',s):
            codes.extend([0,1,2,3,4] if token=='{PLAYER}' else [char_codes[token]])
        assert 1<=len(codes)<=32,(i,len(codes))
        # Preserve native counted-pair format and the native 64-byte parse buffer.
        payload=bytes([0xe0|len(codes)-1])+b''.join(c.to_bytes(2,'little') for c in codes)
        if (text_cursor&0xffff)+len(payload)>0x10000:
            text_cursor=(text_cursor+0xffff)&~0xffff
        assert text_cursor+len(payload)<=0x270000
        rom[text_cursor:text_cursor+len(payload)]=payload
        ptr=text_cursor&0xffff;bank=0xc0+(text_cursor>>16)
        inserted.append({'id':r['id'],'korean':s,'address':text_cursor,'codes':codes,
                         'dynamic_glyph_occurrences':sum(c>=0x180 for c in codes)})
        text_cursor+=len(payload)
    rom[0x201000+2*i:0x201002+2*i]=ptr.to_bytes(2,'little')
    rom[0x203000+i]=bank
    rom[0x204000+2*i:0x204002+2*i]=bank.to_bytes(2,'little')

# Entry: A=dialogue index, M16/X16, X=tile destination. Exit matches native
# lookup: DP0E=source pointer, DB=source bank, M8/X16, original X restored.
lookup=bytes.fromhex('da 0a aa bf 00 10 e0 85 0e 8a 4a aa e2 20 bf 00 30 e0 48 ab fa 6b')
rom[0x200000:0x200000+len(lookup)]=lookup
assert original[0x2503a:0x2503d]==bytes.fromhex('da 0a aa')
rom[0x2503a:0x2505d]=bytes.fromhex('22 00 00 e0')+b'\xea'*(0x23-4)
# The window-sizing pass must see the same translated record lengths.
# These two original paths leave X at index*2, unlike the main text path.
width_lookup=bytes.fromhex('0a aa bf 00 10 e0 85 08 e2 20 bf 00 40 e0 48 ab 6b')
caption_lookup=bytes.fromhex('0a aa bf 00 10 e0 85 0e e2 20 bf 00 40 e0 48 ab 6b')
rom[0x200200:0x200200+len(width_lookup)]=width_lookup
rom[0x200240:0x200240+len(caption_lookup)]=caption_lookup
assert original[0x252ba:0x252c0]==bytes.fromhex('0a aa bf 00 00 c7')
rom[0x252ba:0x252d8]=bytes.fromhex('22 00 02 e0')+b'\xea'*(0x1e-4)
assert original[0xfe495:0xfe49b]==bytes.fromhex('0a aa bf 00 00 c7')
rom[0xfe495:0xfe4b3]=bytes.fromhex('22 40 02 e0')+b'\xea'*(0x1e-4)

# Entry: M16/X16, parsed glyph at DP0E. Exit: source DP00/02,
# destination 7E8000 in DP04/06, M8/X16; X and Y preserved.
# The original decompressor and staging-buffer writes remain in place.
load_font=bytes.fromhex('da b2 0e 0a aa bf 00 00 e1 85 00 a9 00 80 85 04 e2 20 bf 00 20 e1 85 02 a9 7e 85 06 fa 6b')
rom[0x200100:0x200100+len(load_font)]=load_font
assert original[0x25088:0x2508c]==bytes.fromhex('b2 0e 0a aa')
rom[0x25088:0x250a1]=bytes.fromhex('22 00 01 e0')+b'\xea'*(0x19-4)
assert original[0xfe4fc:0xfe515]==original[0x25088:0x250a1]
rom[0xfe4fc:0xfe515]=bytes.fromhex('22 00 01 e0')+b'\xea'*(0x19-4)
cache=build_cache_hook()
rom[0x200400:0x200400+len(cache)]=cache
assert original[0x2507a:0x2507e]==bytes.fromhex('da 5a a5 00')
rom[0x2507a:0x2507e]=bytes.fromhex('5c 00 04 e0')
# The generic raw decoder writes absolute $2180 using DB. Dialogue leaves
# DB=$7E, so those writes hit WRAM $7E2180 rather than the hardware port!
# Copy the 32-byte raw glyph payload directly to its explicit long address.
copy_glyph=bytes.fromhex('da 5a 08 c2 30 a2 00 00 a0 03 00 b7 00 9f 00 80 7e e8 e8 c8 c8 e0 20 00 90 f1 28 7a fa 6b')
rom[0x200600:0x200600+len(copy_glyph)]=copy_glyph
for callsite in (0x250b5,0xfe529):
    assert original[callsite:callsite+4]==bytes.fromhex('22 7c 88 c2')
    rom[callsite:callsite+4]=bytes.fromhex('22 00 06 e0')
rom[0xffd7]=0x0c
rom[0xffdc:0xffe0]=bytes.fromhex('ff ff 00 00')
checksum=sum(rom)&0xffff
rom[0xffdc:0xffe0]=(checksum^0xffff).to_bytes(2,'little')+checksum.to_bytes(2,'little')

# Read the serialized output back, including entries above 0x7FF and bank edges.
for code,expected in enumerate(glyphs):
    lo=int.from_bytes(rom[0x210000+2*code:0x210002+2*code],'little')
    bank=rom[0x212000+2*code]
    addr=((bank-0xc0)<<16)|lo
    actual,end=decompress(rom,addr)
    assert actual==expected and (end-1)>>16==addr>>16
for entry in inserted:
    p=entry['address'];n=(rom[p]&31)+1
    actual=[int.from_bytes(rom[p+1+2*k:p+3+2*k],'little') for k in range(n)]
    assert actual==entry['codes']
inserted_by_id={r['id']:r for r in inserted}
for r in records:
    i=r['index']
    ptr=int.from_bytes(rom[0x201000+2*i:0x201002+2*i],'little')
    bank=rom[0x203000+i]
    assert bank==rom[0x204000+2*i]
    address=((bank-0xc0)<<16)|ptr
    expected=inserted_by_id[r['id']]['address'] if r['id'] in inserted_by_id else r['address']
    assert address==expected
assert sum(rom)&0xffff==checksum
allowed=[(0x2503a,0x2505d),(0x2507a,0x2507e),(0x25088,0x250a1),(0x252ba,0x252d8),
         (0xfe495,0xfe4b3),(0xfe4fc,0xfe515),(0x250b5,0x250b9),(0xfe529,0xfe52d),
         (0xffd7,0xffd8),(0xffdc,0xffe0)]
changed=[i for i,(a,b) in enumerate(zip(original,rom)) if a!=b]
assert all(any(start<=i<end for start,end in allowed) for i in changed)
target=OUT/'Albert Odyssey 2 - FONT PROTOTYPE - NOT RELEASE.sfc'
target.write_bytes(rom)
(OUT/'inserted_dialogue.json').write_text(json.dumps(inserted,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'character_codes.json').write_text(json.dumps(char_codes,ensure_ascii=False,indent=2),encoding='utf-8')
report={'status':'prototype; not release; runtime unverified','rom':str(target),
        'sha256':hashlib.sha256(rom).hexdigest(),'rom_bytes':len(rom),
        'hangul_glyphs':len(hangul),'native_glyphs_preserved':0x480,
        'hangul_used_in_current_translation_draft':len(used),
        'hangul_slot_policy':'draft characters first; remaining slots populated as expansion test data',
        'page_glyph_cache':{'capacity':56,'wram_start':'7F5168','bytes':112,
                            'lifetime':'one native page construction; DP12 reset at C24ED4',
                            'prerequisite':'all glyph resources use raw format, no LZSS ring writes'},
        'font_resource_banks':sorted({0xc0+(p>>16) for p in font_addresses}),
        'translated_records_inserted':len(inserted),'translation_draft_records':len(translations),
        'static_checks':{'all_font_resources_roundtrip':True,'all_inserted_records_roundtrip':True,
                         'all_dialogue_pointer_paths_agree':True,'hangul_1000_bitmaps_distinct':True,
                         'original_rom_changes_limited_to_declared_hooks_and_header':True,'checksum_valid':True},
        'release_blockers':['native three-line page has a 56-dynamic-glyph limit; expansion handling pending',
                           'menus untranslated',
                           'complete translation and source review pending',
                           'hook execution, screen rendering, freezing and input latency unverified']}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
