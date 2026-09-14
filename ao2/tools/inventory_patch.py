"""Inventory resource insertion; callers must install the context font loader."""
from pathlib import Path
import json
from codec import decompress
from inventory_help import ALL_TEXT as HELP_TEXTS, install as install_help
from clock_labels import TEXT as CLOCK_TEXT, install as install_clock

ROOT=Path(__file__).resolve().parents[2]
def insert_inventory(rom,original,core_mapping,slots,native_glyphs,render):
    names=(ROOT/'ao2/translation/item_names.ko.txt').read_text(encoding='utf-8').splitlines()
    tiles=json.loads((ROOT/'ao2/translation/ui_tiles.ko.json').read_text(encoding='utf-8'))
    items=json.loads((ROOT/'ao2/analysis/items.json').read_text(encoding='utf-8'))
    assert len(names)==len(items)==256
    map_edits=json.loads((ROOT/'ao2/translation/menu_tilemaps.ko.json').read_text(encoding='utf-8'))
    chars={c for s in names+[e['korean'] for e in tiles+map_edits]+['딘',CLOCK_TEXT]+HELP_TEXTS for c in s if '가'<=c<='힣'}
    mapping={c:code for c,code in core_mapping.items() if not ('가'<=c<='힣') or c in chars}
    free=[s for s in slots if s not in mapping.values()]
    missing=sorted(chars-mapping.keys());assert len(missing)<=len(free)
    mapping.update(zip(missing,free))
    help_edits=install_help(rom,original,mapping)
    glyphs=native_glyphs.copy()
    for c in chars:glyphs[mapping[c]]=render(c)
    font=bytearray(0x3200)
    for c,g in enumerate(glyphs):
        p=(c&0x1f0)*32+(c&15)*16
        font[p:p+16]=g[:16];font[p+256:p+272]=g[16:]
    rom[0x284000:0x287200]=font
    def tile(c):
        code=mapping[c];return ((code&0x1f0)<<1)|(code&15)
    cursor=0x4d458;inserted=[]
    for i in range(1,256):
        item=items[i];old_end=items[i+1]['address'] if i<255 else items[0]['address']
        prefix=original[item['address']:item['name_address']]
        icons=item['tiles'][:2]
        assert len(icons)==2 and all(w&0x800 for w in icons),(i,icons)
        tail=original[item['end_name']:old_end]
        words=icons+[tile(c) for c in names[i]]
        payload=prefix+b''.join(w.to_bytes(2,'little') for w in words)+b'\xff\xff'+tail
        rom[0x4d1da+i*2:0x4d1dc+i*2]=(cursor&65535).to_bytes(2,'little')
        rom[cursor:cursor+len(payload)]=payload
        # Re-read the variable-length name and prove all non-text bytes survived.
        q=cursor+len(prefix)
        actual=[]
        while int.from_bytes(rom[q:q+2],'little')!=65535:
            actual.append(int.from_bytes(rom[q:q+2],'little'));q+=2
        q+=2
        assert actual==words and rom[q:q+len(tail)]==tail
        assert rom[cursor:cursor+len(prefix)]==prefix
        inserted.append({'index':i,'korean':names[i],'address':cursor,'tail_bytes':len(tail),'icons':icons})
        cursor+=len(payload)
    assert cursor<=items[0]['address'],('item data overflow',hex(cursor))
    for e in tiles:
        p=int(e['address'],16);n=e['original_cells'];text=e['korean']
        assert len(text)<=n,(e,text)
        assert original[p+2*n:p+2*n+2]==b'\xff\xff',hex(p)
        words=[tile(c) for c in text.ljust(n)]
        rom[p:p+2*n]=b''.join(w.to_bytes(2,'little') for w in words)
    redirected={};resource_cursor=0x290000
    for address in sorted({int(e['resource'],16) for e in map_edits}):
        data,_=decompress(original,address);data=bytearray(data)
        for e in map_edits:
            if int(e['resource'],16)!=address:continue
            x,y,n=e['x'],e['y'],e['cells'];assert len(e['korean'])<=n and x+n<=32
            for k,c in enumerate(e['korean'].ljust(n)):
                p=y*64+(x+k)*2
                attr=int.from_bytes(data[p:p+2],'little')&0xfc00
                word=tile(c)|attr
                data[p:p+2]=word.to_bytes(2,'little')
                data[p+64:p+66]=(word+16).to_bytes(2,'little')
        # Literal LZSS avoids the original raw decoder's DB-sensitive port writes.
        payload=b'\x03'+len(data).to_bytes(2,'little')+b'\x00\x00'
        payload+=b''.join(b'\xff'+data[p:p+8] for p in range(0,len(data),8))
        rom[resource_cursor:resource_cursor+len(payload)]=payload
        actual,_=decompress(rom,resource_cursor);assert actual==data
        redirected[address]=resource_cursor;resource_cursor+=len(payload)
    # Redirect only these exact bank-C4 resources before the native decoder.
    b=bytearray.fromhex('08 c2 30 48 e2 20 a5 02 c9 c4');fix=[];labels={}
    def emit(s):b.extend(bytes.fromhex(s))
    def branch(op,label):emit(op+' 00');fix.append((len(b)-1,label))
    branch('d0','exit');emit('c2 20 a5 00')
    for address in redirected:
        emit('c9');b+=(address&65535).to_bytes(2,'little');branch('f0',str(address))
    branch('80','exit')
    for address,target in redirected.items():
        labels[str(address)]=len(b);emit('a9');b+=(target&65535).to_bytes(2,'little')
        emit('85 00 e2 20 a9 e9 85 02');branch('80','exit')
    labels['exit']=len(b);emit('c2 30 68 28 5a da 08 e2 30 5c 81 88 c2')
    for p,label in fix:
        d=labels[label]-p-1;assert -128<=d<=127;b[p]=d&255
    assert len(b)<0x100 and original[0x2887c:0x28881]==bytes.fromhex('5a da 08 e2 30')
    rom[0x200c00:0x200c00+len(b)]=b
    rom[0x2887c:0x28881]=bytes.fromhex('5c 00 0c e0 ea')
    clock=install_clock(rom,original,mapping)
    return {'help_edits':help_edits,'font':bytes(font),'mapping':mapping,'items':inserted,'direct_strings':tiles,'clock':clock,
            'item_data_end':cursor,'hangul':len(chars),
            'metadata_and_icons_preserved':True,'font_context_loaders_installed':False,
            'compressed_resource_redirects':{hex(k):hex(v) for k,v in redirected.items()},
            'long_names_requiring_list_layout_work':[{'index':i,'name':s} for i,s in enumerate(names) if len(s)>8]}
