"""Translate the native inventory clock without changing its time calculation."""
TEXT='오전오후시'

def install(rom, original, mapping):
    def tile(c):
        n=mapping[c];return ((n&0x1f0)<<1)|(n&15)
    b=bytearray.fromhex('c2 30')
    def cell(address,c):
        w=tile(c)
        for a,t in [(address,w),(address+64,w+16)]:
            b.extend(b'\xa9'+t.to_bytes(2,'little')+b'\x8f'+a.to_bytes(3,'little'))
    cell(0x7e954f,' ');cell(0x7e9551,'오')
    b.extend(bytes.fromhex('a5 ce 29 3f 00 c9 10 00 90 05 c9 30 00 90 10'))
    cell(0x7e9553,'전')
    b.extend(bytes.fromhex('80 0e'))
    cell(0x7e9553,'후')
    b.extend(bytes.fromhex('5c f9 9a c4'))
    assert len(b)<0x100
    rom[0x200d00:0x200d00+len(b)]=b
    assert original[0x49aa1:0x49aa5]==bytes.fromhex('e2 20 a5 ce')
    rom[0x49aa1:0x49aa5]=bytes.fromhex('5c 00 0d e0')
    for address,w in [(0x49b34,tile('시')),(0x49b3b,tile('시')+16)]:
        assert original[address-1]==0xa9
        rom[address:address+2]=w.to_bytes(2,'little')
    return {'labels':['오전','오후','시'],'native_time_calculation_preserved':True}
