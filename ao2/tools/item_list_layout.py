"""Retain two item columns, full names, icons and two-digit quantities.

Use the idle column to the left of each name and remove the redundant quantity
multiplication sign. The cursor moves left with the name, remaining separate.
"""
def install(rom,original):
    patches=[]
    def word_operand(p,old,new):
        assert original[p:p+2]==old.to_bytes(2,'little'),hex(p)
        rom[p:p+2]=new.to_bytes(2,'little');patches.append(hex(p))
    for p in [0x49de0,0x49e49,0x4a6fe,0x4a76d,0x4a897]:word_operand(p+1,0x8287,0x8285)
    for p in [0x49de8,0x49e4d,0x4a708,0x4a771]:word_operand(p+1,0x82c7,0x82c5)
    word_operand(0x4a89c,0x82a5,0x82a3)
    for p in [0x4936c,0x493de]:word_operand(p+1,0x8285,0x8283)
    for p in [0x49370,0x493e2]:word_operand(p+1,0x82a3,0x82a1)
    for p in range(0x4945e,0x4948a,2):
        old=int.from_bytes(original[p:p+2],'little');word_operand(p,old,old-2)
    for start,end in [(0x49e2d,0x49e40),(0x4a74f,0x4a764)]:
        assert original[start:start+2]==bytes.fromhex('a6 32') and original[end]==0x80
        rom[start:end]=b'\xea'*(end-start);patches.append(hex(start))
    for p,old in [(0x49e58,12),(0x4a77c,13),(0x4a8a3,13)]:word_operand(p,old,14)
    return {'name_cells_including_icons':12,'hangul_name_capacity':10,'quantity_digits':2,
            'first_column':{'cursor':1,'name':[2,13],'quantity':[14,15]},
            'second_column':{'cursor':16,'name':[17,28],'quantity':[29,30]},
            'native_item_count_and_navigation_unchanged':True,'operand_patches':patches}
