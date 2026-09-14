"""Extend the native eight-stage speech window to 32 text cells."""
def install(rom, original):
    # Stage 8/9 previously indexed past D3A350's eight resource pointers.
    # Keep stages 0..7, and use a full-screen-width panel for long lines.
    code=bytearray.fromhex('08 c2 30 a5 2a 29 ff 00 c9 08 00 b0 04 5c 60 73 e0')
    code+=bytes.fromhex('22 3c f0 cf a2 00 00')
    code+=bytes.fromhex('bf 00 74 e0 9f e0 11 7e e8 e8 e0 40 02 90 f1')
    code+=bytes.fromhex('e2 20 a5 d9 09 02 85 d9 28 6b')
    assert original[0x2c6b6:0x2c6ba]==bytes.fromhex('08 c2 30')+b'\x22'
    rom[0x2c6b6:0x2c6ba]=bytes.fromhex('5c 00 73 e0')
    # JSL's opcode was overwritten, so provide a native-path trampoline.
    rom[0x207300:0x207300+len(code)]=code
    rom[0x207360:0x207368]=bytes.fromhex('22 3c f0 cf 5c bd c6 c2')
    panel=[]
    for y in range(9):
        for x in range(32):
            tile=([0x82fd,0x82fe,0xc2fe,0xc2fd][x%4] if y==0 else
                  [0x2fd,0x2fe,0x42fe,0x42fd][x%4] if y==8 else 0x48)
            panel.append(tile|0x2000)
    payload=b''.join(v.to_bytes(2,'little') for v in panel)
    rom[0x207400:0x207400+len(payload)]=payload
    # Include a guard entry because callers use a 16-bit LDA then mask.
    rom[0x207700:0x20770b]=original[0x13aac3:0x13aacb]+bytes([2,0,0])
    for p in (0x24f9d,0x41a11):
        assert original[p:p+3]==bytes.fromhex('c3 aa d3')
        rom[p:p+3]=bytes.fromhex('00 77 e0')
    return {'maximum_cells':32,'native_stages':8,'extended_stages':[8,9],
            'new_wram_bytes':0,'panel_wram_range':[0x11e0,0x1420]}
