"""Field battle UI text stored outside the C6 string table."""
TERRAIN=['평야','삼림','황무지','도로','도로','언덕','마을','제방','바다','바다',
         '바위땅','바위산','도시','바다','도로','땅','도시','바위산','바위땅','바다',
         '도로','동굴','숲','삼림','언덕','동굴','삼림','언덕','바다','도로',
         '얼음','바닥','바닥','바닥','바닥','바닥','바닥','바닥','늪','황무지',
         '풀밭','눈밭','용암','구멍','용암','구멍','구멍','연못','용암','벽']
SKILLS=['기합베기','화조','청사자','돌격','필중','열기','훔치기','회복','부활','치유','퇴마탄','뇌격','화염탄','냉동탄','마비탄','대회복','축복','난무']
TEXT=''.join(TERRAIN+SKILLS)+'체력 정신력 지형: 정상사망석화마비중독축복공격수비특수방어낮밤밝기없습니다이동력%'

def install(rom,original,core_mapping,render):
    mapping=core_mapping.copy()
    relocated={c:n for c,n in mapping.items() if n>=0x180}
    extra=sorted((set(TEXT)-mapping.keys())|relocated.keys())
    assert len(extra)<=56
    mapping.update(zip(extra,range(0x188,0x1c0)))
    changes=[]
    def tile(c):
        n=mapping[c];return ((n&0x1f0)*2)|(n&15)
    def immediate(p,c,bottom=False):
        assert original[p]==0xa9
        old=int.from_bytes(original[p+1:p+3],'little')
        new=(old&0xfc00)|tile(c)+(16 if bottom else 0)
        rom[p+1:p+3]=new.to_bytes(2,'little')
        changes.append([p+1,p+3])
    # Native full HP/MP labels have three cells, short labels have two.
    for bases,text in [([0x28e43,0x28e4f,0x28e5b],'체력 '),
                       ([0x28e84,0x28e90],'체력'),
                       ([0x28eb9,0x28ec5,0x28ed1],'정신력'),
                       ([0x28efa,0x28f06],'정신')]:
        for p,c in zip(bases,text):immediate(p,c);immediate(p+6,c,True)
    # Colon slots are overwritten by numerical output in some callers.
    for p in [0x28e67,0x28e9c,0x28edd,0x28f12]:
        immediate(p,' ');immediate(p+6,' ',True)
    for p,c in zip([0x22a3f,0x22a4c,0x22a59],'지형:'):immediate(p,c)
    for i,text in enumerate(TERRAIN):
        p=0xdbf+i*8
        words=[tile(c)|0x2400 for c in text.center(4)]
        rom[p:p+8]=b''.join(w.to_bytes(2,'little') for w in words)
        changes.append([p,p+8])
    for i,s in enumerate(SKILLS):
        p=0x23661+i*8
        rom[p:p+8]=b''.join((tile(c)|0x2000).to_bytes(2,'little') for c in s.ljust(4))
        changes.append([p,p+8])
    for base,s in [(0xfee79,'이동력:'),(0xfeeb2,'이동:'),
                   (0x43439,'정상'),(0x40111,'밝기 ')]:
        for i,c in enumerate(s):immediate(base+i*13,c)
    for p,c in [(0x4009c,'낮'),(0x400ad,'밤'),(0x400ed,':'),(0x4018e,'%'),
                (0x22b4d,'%'),(0x22f9e,'%')]:
        immediate(p,c)
        if p in [0x22b4d,0x22f9e]:immediate(p+6,c,True)
    for p,s in [(0x2378a,'없습니다'),(0x2386d,'없습니다'),(0x23917,'없습니다')]:
        for i,c in enumerate(s):immediate(p+i*13,c)
    for i,c in enumerate('없습니다'):
        immediate(0x239d0+i*12,c);immediate(0x239d0+i*12+6,c,True)
    for p,s in [(0x434c7,'사망   '),(0x43508,'석화'),(0x4353a,'마비'),(0x4356c,'중독'),(0x4359e,'축복')]:
        for i,c in enumerate(s):immediate(p+i*12,c);immediate(p+i*12+6,c,True)
    for i,c in enumerate('지형효과 '):immediate(0x22f10+i*12,c);immediate(0x22f10+i*12+6,c,True)
    # Replace four one-kanji labels plus their shared colon with two Korean cells.
    code=bytearray()
    for dst,s in [(0x138c,'공격'),(0x1396,'수비'),(0x140c,'특수'),(0x1416,'방어')]:
        for i,c in enumerate(s):
            for d,w in [(dst+i*2,tile(c)|0x2000),(dst+i*2+64,(tile(c)|0x2000)+16)]:
                code+=b'\xa9'+w.to_bytes(2,'little')+b'\x8d'+d.to_bytes(2,'little')
    code+=b'\x6b';rom[0x207e00:0x207e00+len(code)]=code
    rom[0x22bd2:0x22c1d]=bytes.fromhex('22 00 7e e0')+b'\xea'*(0x22c1d-0x22bd2-4)
    changes.append([0x22bd2,0x22c1d])
    # Field-only glyphs share the native dialogue atlas after its text closes.
    # No new WRAM allocation: compare existing staging bytes, DMA only on change.
    fragments=[]
    for c in extra:
        n=mapping[c];g=render(c);off=(n&0x1f0)*32+(n&15)*16-0x3000
        for o,data in [(off,g[:16]),(off+256,g[16:])]:
            rom[0x2c0000+o:0x2c0000+o+16]=data;fragments.append(o)
    segments=[]
    for off in sorted(fragments):
        if segments and segments[-1][0]+segments[-1][1]==off:segments[-1][1]+=16
        else:segments.append([off,16])
    b=bytearray();labels={};fix=[]
    def emit(h):b.extend(bytes.fromhex(h))
    def branch(op,label):emit(op+' 00');fix.append((len(b)-1,label))
    emit('08 c2 30 48 da 5a 8b e2 20 a5 d8 c9 01')
    branch('f0','field');emit('c9 03');branch('f0','field');emit('c9 04');branch('f0','field');emit('ab c2 30 7a fa 68 28 6b')
    labels['field']=len(b);emit('c2 30')
    # Compare all field glyph fragments; branch to upload on the first mismatch.
    for i,(off,count) in enumerate(segments):
        emit('a2 00 00');labels['compare'+str(i)]=len(b)
        b+=b'\xbf'+(0xec0000+off).to_bytes(3,'little')+b'\xdf'+(0x7f6168+off).to_bytes(3,'little')
        branch('f0','equal'+str(i));emit('82 00 00');fix.append((len(b)-2,'upload',16))
        labels['equal'+str(i)]=len(b);emit('e8 e8 e0');b+=count.to_bytes(2,'little');branch('90','compare'+str(i))
    emit('ab 7a fa 68 28 6b');labels['upload']=len(b)
    for i,(off,count) in enumerate(segments):
        emit('a2 00 00');labels['copy'+str(i)]=len(b)
        b+=b'\xbf'+(0xec0000+off).to_bytes(3,'little')+b'\x9f'+(0x7f6168+off).to_bytes(3,'little')
        emit('e8 e8 e0');b+=count.to_bytes(2,'little');branch('90','copy'+str(i))
    # Bounded VBlank transfer. Nothing is uploaded on ordinary cursor redraws.
    emit('e2 20 a9 00 48 ab 78 9c 00 42 9c 0c 42 ad 12 42 29 80 d0 f9 ad 12 42 29 80 f0 f9')
    emit('a9 80 8d 15 21 a9 01 8d 00 43 a9 18 8d 01 43 a9 ec 8d 04 43')
    for off,count in segments:
        emit('c2 20 a9');b+=(0x5800+off//2).to_bytes(2,'little');emit('8d 16 21 a9');b+=off.to_bytes(2,'little')
        emit('8d 02 43 a9');b+=count.to_bytes(2,'little');emit('8d 05 43 e2 20 a9 01 8d 0b 42')
    emit('a5 64 8d 0c 42 a5 65 8d 00 42 ab c2 30 7a fa 68 28 6b')
    for f in fix:
        p,label,*wide=f;size=2 if wide else 1;delta=labels[label]-(p+size)
        assert -(1<<(size*8-1))<=delta<(1<<(size*8-1)),(p,label,delta)
        b[p:p+size]=delta.to_bytes(size,'little',signed=True)
    assert len(b)<0x600
    rom[0x20e000:0x20e000+len(b)]=b
    # Native grid entry. Preserve the exact original prologue and return address.
    assert original[0x2cd11:0x2cd15]==bytes.fromhex('da 08 e2 20')
    trampoline=bytes.fromhex('22 00 e0 e0 da 08 e2 20 5c 15 cd c2')
    rom[0x207f00:0x207f00+len(trampoline)]=trampoline
    rom[0x2cd11:0x2cd15]=bytes.fromhex('5c 00 7f e0');changes.append([0x2cd11,0x2cd15])
    # The engine also uses 180..187 for transient graphics in field scenes.
    # Relocate those static letters in every parsed C6 field grid/name.
    table=bytearray(16)
    for c,n in relocated.items():table[(n-0x180)*2:(n-0x180)*2+2]=mapping[c].to_bytes(2,'little')
    rom[0x20f100:0x20f110]=table
    remap=bytearray.fromhex('08 c2 30 48 da 5a a5 d8 29 ff 00 c9 01 00 f0 0a c9 03 00 f0 05 c9 04 00 d0 28 a2 00 00 bf e0 24 7e c9 80 01 90 15 c9 88 01 b0 10 38 e9 80 01 0a da aa bf 00 f1 e0 fa 9f e0 24 7e e8 e8 e0 40 00 d0 db 7a fa 68 28 6b')
    rom[0x20f000:0x20f000+len(remap)]=remap
    wrapper=bytes.fromhex('22 33 36 c4 22 00 f0 e0 6b')
    rom[0x20f080:0x20f080+len(wrapper)]=wrapper
    rom[0x2cd46:0x2cd4a]=bytes.fromhex('22 80 f0 e0');changes.append([0x2cd46,0x2cd4a])
    wrapper=bytes.fromhex('22 00 f0 e0 08 c2 20 e2 10 5c 70 8d c2')
    rom[0x20f0a0:0x20f0a0+len(wrapper)]=wrapper
    assert original[0x28d6b:0x28d70]==bytes.fromhex('08 c2 20 e2 10')
    rom[0x28d6b:0x28d70]=bytes.fromhex('5c a0 f0 e0 ea');changes.append([0x28d6b,0x28d70])
    # A scene font reset invalidates the staging comparison before field re-entry.
    invalid=bytes.fromhex('08 c2 20 48 a9 ff ff 8f e8 61 7f 68 28')
    for start,end in [(0x200800,0x200900),(0x206000,0x206800)]:
        q=rom.index(bytes.fromhex('ab c2 30 7a fa 68 28 6b'),start,end)+7
        rom[q:q+len(invalid)+1]=invalid+b'\x6b'
    return {'modified_ranges':changes,'terrain_names':TERRAIN,'skills':SKILLS,
            'mapping':mapping,'extra_glyphs':extra,'font_segments':segments,
            'font_vram_end':hex(0xb000+max(o+n for o,n in segments)),
            'new_wram_bytes':0,'font_copy_on_cursor':False}

