"""AO2 resource formats: raw, original bit-transpose groups, and LZSS."""
def decompress(rom,start):
    kind=rom[start];p=start+1;out=bytearray()
    if kind==0:
        n=int.from_bytes(rom[p:p+2],'little')+1
        return rom[p+2:p+2+n],p+2+n
    if kind==3:
        n=int.from_bytes(rom[p:p+2],'little');p+=4
        ring=bytearray(4096);cursor=0xfee
        while len(out)<n:
            flags=rom[p];p+=1
            for bit in range(8):
                if flags&(1<<bit):
                    chunk=[rom[p]];p+=1
                    for value in chunk:
                        out.append(value);ring[cursor]=value;cursor=(cursor+1)&4095
                else:
                    lo,hi=rom[p:p+2];p+=2
                    src=lo|((hi&0xf0)<<4)
                    for k in range((hi&15)+3):
                        value=ring[(src+k)&4095];out.append(value)
                        ring[cursor]=value;cursor=(cursor+1)&4095
                        if len(out)==n:break
                if len(out)==n:break
        return bytes(out),p
    if kind==1:
        while True:
            flags=rom[p];p+=1
            if flags==1:return bytes(out),p
            seed=rom[p];p+=1;group=[seed]
            for bit in range(7,0,-1):
                if flags&(1<<bit):group.append(seed)
                else:group.append(rom[p]);p+=1
            if flags&1:
                group=[sum(((group[x]>>(7-y))&1)<<(7-x) for x in range(8)) for y in range(8)]
            out.extend(group)
            assert len(out)<=0x10000
    raise ValueError((hex(start),kind))

def raw_resource(data):
    assert 0<len(data)<=0x10000
    return b'\0'+(len(data)-1).to_bytes(2,'little')+data
