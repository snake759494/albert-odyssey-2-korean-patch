"""Render item notifications in the native transient dialogue glyph area.

Inventory glyph IDs cannot be displayed with the world font. A notification
loads only its own ten cells (320 bytes), retaining every static UI glyph.
The native notification is mutually exclusive with a dialogue page; its font
area is rebuilt normally when the next dialogue starts. No persistent WRAM.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def install(rom,original,render):
    names=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8').splitlines()
    cursor=0x2a0000
    for i,s in enumerate(names):
        assert len(s)<=10,(i,s)
        if cursor%65536+320>65536:cursor=(cursor+65535)&~65535
        glyphs=[render(c) for c in s.ljust(10)]
        data=b''.join(g[:16] for g in glyphs[:8])+b''.join(g[16:] for g in glyphs[:8])
        data+=b''.join(g[:16] for g in glyphs[8:])+b''.join(g[16:] for g in glyphs[8:])
        rom[cursor:cursor+320]=data
        rom[0x220000+i*2:0x220002+i*2]=(cursor&65535).to_bytes(2,'little')
        rom[0x220200+i*2:0x220202+i*2]=(0xc0+(cursor>>16)).to_bytes(2,'little')
        rom[0x220400+i*2:0x220402+i*2]=len(s).to_bytes(2,'little')
        cursor+=320
    b=bytearray.fromhex('08 c2 30 48 da 5a 8b e2 20 a9 00 48 ab 78 9c 00 42 9c 0c 42 ad 12 42 29 80 d0 f9 ad 12 42 29 80 f0 f9 a9 80 8d 15 21 a9 01 8d 00 43 a9 18 8d 01 43 bf 00 02 e2 8d 04 43 c2 20 bf 00 00 e2 8d 02 43')
    for dest,count in [(0x5840,128),(0x58c0,128),(0x5900,32),(0x5980,32)]:
        b+=bytes.fromhex('c2 20 a9')+dest.to_bytes(2,'little')+bytes.fromhex('8d 16 21 a9')+count.to_bytes(2,'little')
        b+=bytes.fromhex('8d 05 43 e2 20 a9 01 8d 0b 42')
    b+=bytes.fromhex('c2 30 bf 00 04 e2 a8')
    # Exactly the native name length is written to the original caption cells.
    for k in range(10):
        n=0x188+k;t=((n&0x1f0)<<1)|(n&15)|0x3000
        b+=bytes.fromhex('c0 00 00 f0 0e')
        b+=b'\xa9'+t.to_bytes(2,'little')+b'\x8d'+(0x13fc+k*2).to_bytes(2,'little')
        b+=b'\xa9'+(t+16).to_bytes(2,'little')+b'\x8d'+(0x143c+k*2).to_bytes(2,'little')+b'\x88\xea'
    b+=bytes.fromhex('e2 20 a5 64 8d 0c 42 a5 65 8d 00 42 ab c2 30 7a fa 68 28 6b')
    assert len(b)<0x200
    rom[0x200e00:0x200e00+len(b)]=b
    assert original[0x24026:0x2402a]==bytes.fromhex('bf da d1 c4')
    rom[0x24026:0x2402d]=bytes.fromhex('22 00 0e e0 82 36 00')
    return {'font_bytes_per_notification':320,'cursor_hooks':0,'extra_wram_bytes':0,
            'vram_ranges':[[0xb080,0xb100],[0xb180,0xb200],[0xb200,0xb220],[0xb300,0xb320]],
            'name_capacity':10,'item_count':256,'font_data_end':hex(cursor)}
