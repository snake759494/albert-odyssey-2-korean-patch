"""Switch static font resources at scene/overlay boundaries, never per cursor."""
def dma_loader(base,segments,wait_vblank=False):
    b=bytearray.fromhex('08 c2 30 48 da 5a 8b e2 20 a9 00 48 ab')
    if wait_vblank:
        # Keep native NMI/HDMA out of channel zero while loading the font delta.
        b+=bytes.fromhex('78 9c 00 42 9c 0c 42 ad 12 42 29 80 d0 f9 ad 12 42 29 80 f0 f9')
    b+=bytes.fromhex('a9 80 8d 15 21 a9 01 8d 00 43 a9 18 8d 01 43 a9 e8 8d 04 43')
    for p,n in segments:
        b+=bytes.fromhex('c2 20 a9')+(0x4000+p//2).to_bytes(2,'little')+bytes.fromhex('8d 16 21 a9')
        b+=(base+p).to_bytes(2,'little')+bytes.fromhex('8d 02 43 a9')+n.to_bytes(2,'little')
        b+=bytes.fromhex('8d 05 43 e2 20 a9 01 8d 0b 42')
    if wait_vblank:b+=bytes.fromhex('a5 64 8d 0c 42 a5 65 8d 00 42')
    b+=bytes.fromhex('ab c2 30 7a fa 68 28 6b')
    return bytes(b)

def install(rom,original,corefont,inventoryfont):
    full=[(0,0x3000),(0x3000,0x80),(0x3100,0x80)]
    delta=[]
    for start,n in full:
        for p in range(start,start+n,16):
            if corefont[p:p+16]!=inventoryfont[p:p+16]:
                if delta and delta[-1][0]+delta[-1][1]==p:
                    delta[-1]=(delta[-1][0],delta[-1][1]+16)
                else:delta.append((p,16))
    transferred=sum(n for _,n in delta)
    # DMA master cycles plus generous register-write/setup allowance.
    budget=transferred*8+len(delta)*500+2000
    assert budget<48000,('font delta exceeds conservative VBlank budget',budget)
    invfull=dma_loader(0x4000,full)
    assert len(invfull)<256
    rom[0x200900:0x200900+len(invfull)]=invfull
    for address,base in [(0x206000,0),(0x206800,0x4000)]:
        code=dma_loader(base,delta,True);assert len(code)<0x800
        rom[address:address+len(code)]=code
    # Reset PPU, then select the full static font while the scene is blanked.
    wrapper=bytes.fromhex('22 53 d0 cf 08 c2 30 48 e2 20 a9 80 8f 00 21 00 a5 d8 f0 0e c9 0f f0 0a c9 10 f0 06 22 00 08 e0 80 04 22 00 09 e0 c2 30 68 28 6b')
    rom[0x200a00:0x200a00+len(wrapper)]=wrapper
    sites=[]
    for p in range(0x144,0x4f7):
        if original[p:p+4]==bytes.fromhex('22 53 d0 cf'):
            rom[p:p+4]=bytes.fromhex('22 00 0a e0');sites.append(p)
    # Overlay entry points share the inventory resource without a scene reset.
    for ordinal,(site,target) in enumerate([(0x3a0,0xc48bd8),(0x3cb,0xc48be7),(0x3f6,0xc48bc9)]):
        address=0x200b00+ordinal*0x20
        expected=b'\x22'+target.to_bytes(3,'little');assert original[site:site+4]==expected
        code=bytes.fromhex('22 00 68 e0')+expected+b'\x6b'
        rom[address:address+len(code)]=code
        rom[site:site+4]=b'\x22'+(address+0xc00000).to_bytes(3,'little')
    # Overlay return restores the core font before the world UI becomes visible.
    site=0x48e31;assert original[site:site+4]==bytes.fromhex('22 2d a2 c4')
    code=bytes.fromhex('22 00 60 e0 22 2d a2 c4 6b')
    rom[0x200b60:0x200b60+len(code)]=code;rom[site:site+4]=bytes.fromhex('22 60 0b e0')
    return {'scene_init_hooks':[hex(p) for p in sites],'overlay_delta_bytes':transferred,
            'overlay_dma_segments':delta,'conservative_master_cycle_budget':budget,
            'cursor_move_hooks':0,'extra_wram_bytes':0}
