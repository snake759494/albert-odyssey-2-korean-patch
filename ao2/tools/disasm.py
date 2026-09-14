from pathlib import Path
import capstone,sys
b=Path('Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
start=int(sys.argv[1],16) if len(sys.argv)>1 else 0
end=int(sys.argv[2],16) if len(sys.argv)>2 else start+0x100
# Optional initial M/X register widths; straight-line REP/SEP tracking cannot
# recover widths across arbitrary branches, PLP or subroutine calls.
m=(int(sys.argv[3])==16) if len(sys.argv)>3 else True
x=(int(sys.argv[4])==16) if len(sys.argv)>4 else True
p=start
while p<end:
    # This installed Capstone build rejects the nominal 65816 base mode.
    # Decode in long-MX and explicitly shorten width-dependent immediates.
    md=capstone.Cs(capstone.CS_ARCH_MOS65XX,96)
    ins=next(md.disasm(b[p:p+4],0xc00000+p,count=1),None)
    if ins is None: p+=1;continue
    size=ins.size; operand=ins.op_str
    if ((not m and b[p] in (0x09,0x29,0x49,0x69,0x89,0xa9,0xc9,0xe9))
        or (not x and b[p] in (0xa0,0xa2,0xc0,0xe0))):
        size=2; operand=f'#0x{b[p+1]:02x}'
    print(f'{p:06X} {b[p:p+size].hex(" "):11s} {ins.mnemonic:5s} {operand}')
    if b[p]==0xc2:
        m=m or bool(b[p+1]&0x20);x=x or bool(b[p+1]&0x10)
    elif b[p]==0xe2:
        m=m and not bool(b[p+1]&0x20);x=x and not bool(b[p+1]&0x10)
    p+=size

