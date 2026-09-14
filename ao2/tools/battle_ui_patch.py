"""Battle-only text resources, atlas, and name remapping.

BG3 starts at VRAM B000 in battle, so glyphs 180..187 must not be used there.
The battle atlas is loaded once under forced blank and ends at AFFF.
"""
from pathlib import Path
import json
from codec import decompress
from font_context import dma_loader
ROOT=Path(__file__).resolve().parents[2]
TEXT={0x6a28e:'의 공격!',0x6a2a2:'의 독 공격!',0x6a2ae:'의 마비공격!',
0x6a2ba:'의 석화공격!',0x6a2c6:'의 난무!',0x6a2d2:'의 기합베기!',
0x6a2de:'의 퇴마탄!',0x6a2e8:'의 냉동탄!',0x6a2f2:'의 돌격!',
0x6a2fa:'의 필중!',0x6a302:'의 화조!',0x6a30a:'의 청사자!',
0x6a314:'의 뇌격!',0x6a31c:'의 화염탄!',0x6a326:'파이어!',
0x6a332:'의 브레스!',0x6a33c:'의 마비탄!',0x6a35c:'의 돌격!'}

def install(rom,original,mapping,slots,render):
    ui=json.loads((ROOT/'ao2/translation/ui.ko.json').read_text(encoding='utf-8'))
    names=[ui.get(str(int.from_bytes(original[0x12e2+i*2:0x12e4+i*2],'little')),'') for i in range(114)]
    assert max(map(len,names))+max(map(len,TEXT.values()))<=14
    # The name input uses shared core/inventory characters; keep their positions.
    keep=set(''.join(names)+''.join(TEXT.values())+'공격수비명중률의:%')
    for p in [0xfe0a0,0xfe154]:
        for q in range(p,p+180,2):
            w=int.from_bytes(rom[q:q+2],'little');n=((w&0x3e0)>>1)|(w&15)
            keep.update(c for c,k in mapping.items() if k==n)
    bm=mapping.copy()
    needed=sorted((keep-mapping.keys())|{c for c,n in mapping.items() if n>=0x180})
    occupied={mapping[c] for c in keep if c in mapping and mapping[c]<0x180}
    free=[n for n in slots if n<0x180 and n not in occupied]
    assert len(needed)<=len(free)
    bm.update(zip(needed,free))
    font=bytearray(rom[0x280000:0x283000])
    for c in needed:
        n=bm[c];g=render(c);p=(n&0x1f0)*32+(n&15)*16
        font[p:p+16]=g[:16];font[p+256:p+272]=g[16:]
    rom[0x28c000:0x28f000]=font
    loader=dma_loader(0xc000,[(0,0x3000)])
    rom[0x207000:0x207000+len(loader)]=loader
    wrapper=bytes.fromhex('8f db 00 00 22 00 70 e0 6b')
    rom[0x207100:0x207100+len(wrapper)]=wrapper
    assert original[0x50007:0x5000b]==bytes.fromhex('8f db 00 00')
    rom[0x50007:0x5000b]=bytes.fromhex('22 00 71 e0')
    # Remap the eight out-of-range codes only in a battle's parsed name buffer.
    for c,n in mapping.items():
        if n>=0x180:rom[0x2d2000+(n-0x180)*2:0x2d2002+(n-0x180)*2]=bm[c].to_bytes(2,'little')
    b=bytearray();labels={};fix=[]
    def emit(s):b.extend(bytes.fromhex(s))
    def label(s):labels[s]=len(b)
    def branch(op,s):emit(op+' 00');fix.append((len(b)-1,s))
    emit('08 c2 30 48 da 5a a5 d8 29 ff 00 c9 02 00');branch('d0','done')
    emit('a2 00 00');label('loop');emit('bf e0 24 7e c9 80 01');branch('90','next')
    emit('c9 88 01');branch('b0','next')
    emit('38 e9 80 01 0a da aa bf 00 20 ed fa 9f e0 24 7e')
    label('next');emit('e8 e8 e0 40 00');branch('d0','loop')
    label('done');emit('7a fa 68 28 22 6b 8d c2 6b')
    for p,s in fix:b[p]=(labels[s]-p-1)&255
    rom[0x207200:0x207200+len(b)]=b
    assert original[0x28b90:0x28b94]==bytes.fromhex('22 6b 8d c2')
    rom[0x28b90:0x28b94]=bytes.fromhex('22 00 72 e0')
    def tile(c):
        n=bm[c];assert n<0x180;return ((n&0x1f0)<<1)|(n&15)
    # Patch the separate compressed battle HUD, not the general C6 string table.
    panel,_=decompress(original,0xc3e4d);panel=bytearray(panel)
    edits=[(14,1,4,'명중률'),(1,4,2,'공격'),(7,4,2,'수비'),(20,4,2,'공격'),(26,4,2,'수비'),(17,4,1,'%')]
    for x,y,n,s in edits:
        for k,c in enumerate(s.ljust(n)):
            p=y*64+(x+k)*2;attrs=int.from_bytes(panel[p:p+2],'little')&0xfc00
            w=tile(c)|attrs;panel[p:p+2]=w.to_bytes(2,'little');panel[p+64:p+66]=(w+16).to_bytes(2,'little')
    payload=b'\x03'+len(panel).to_bytes(2,'little')+b'\0\0'+b''.join(b'\xff'+panel[p:p+8] for p in range(0,len(panel),8))
    rom[0x2d0000:0x2d0000+len(payload)]=payload
    rom[0x53cd1:0x53cd3]=bytes.fromhex('00 00');rom[0x53cd6:0x53cd8]=bytes.fromhex('ed 00')
    cursor=0x2d1000;strings=[];patches=[]
    for source in range(0x6a28e,0x6a380,2):
        refs=[p for p in range(0x53000,0x5355b) if original[p:p+4]==b'\xbf'+(source+0xc00000).to_bytes(3,'little')]
        if not refs:continue
        if source in TEXT:words=[tile(c) for c in TEXT[source]];text=TEXT[source]
        else:
            # The other notices contain native runtime symbols in ASCII slots.
            # Retain those symbols, translating the literal Japanese particles.
            words=[];p=source
            while True:
                w=int.from_bytes(original[p:p+2],'little');p+=2
                w={0x81:tile('의'),0xa7:tile(' '),0x187:tile('공'),0x188:tile('격'),0x1c0:tile('마'),0x1e1:tile('탄'),0xaa:tile('기'),0x18e:tile('동')}.get(w,w)
                words.append(w)
                if w==0x45:break
            text='native dynamic symbols; Korean literal particles'
        assert words[-1]==0x45
        rom[cursor:cursor+len(words)*2]=b''.join(w.to_bytes(2,'little') for w in words)
        for p in refs:rom[p+1:p+4]=(cursor+0xc00000).to_bytes(3,'little');patches.append(p)
        strings.append({'source':hex(source),'address':cursor,'text':text,'words':words,'callers':refs});cursor+=len(words)*2
    # A longer translated name must never make the native clearing loop wrap.
    assert original[0x5314a]==0xf0;rom[0x5314a]=0xb0
    return {'font':bytes(font),'mapping':bm,'panel':bytes(panel),'strings':strings,
            'operand_patches':patches,'hud_labels':edits,'battle_font_vram_end':0xb000,
            'name_codes_relocated':needed,'font_loads_per_scene':1,'cursor_font_loads':0}
