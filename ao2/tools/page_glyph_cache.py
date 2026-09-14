"""Native page-local glyph reuse without allocating new WRAM.

The existing 7F5168..7F6167 LZSS work ring is scratch during glyph rendering.
All glyph loads in this build use raw resources, so its first 112 bytes can
hold 56 glyph IDs for the duration of C24ED1. DP12 is reset on each entry and
therefore bounds all reads without clearing scratch RAM. No persistent cache.
"""

def build_cache_hook():
    code=bytearray(); labels={}; branches=[]
    def emit(s):code.extend(bytes.fromhex(s))
    def label(s):labels[s]=len(code)
    def branch(op,target):
        emit(op+' 00');branches.append((len(code)-1,target))
    emit('da 5a')                     # preserve original X/Y
    emit('a5 12 0a 85 0a a2 00 00') # DP0A = populated cache bytes
    label('search')
    emit('e4 0a');branch('b0','miss')
    emit('bf 68 51 7f d2 0e');branch('f0','hit')
    emit('e8 e8');branch('80','search')
    label('miss')
    emit('a5 12 c9 38 00');branch('b0','native')
    emit('b2 0e 9f 68 51 7f')        # X = DP12*2; store only in 112-byte list
    label('native')
    emit('7a fa da 5a a5 00')        # replay the overwritten original instructions
    emit('5c 7e 50 c2')
    label('hit')
    emit('8a 4a 18 69 08 00 48')    # slot = X/2+8, reserved native slots untouched
    emit('29 0f 00 85 0a 68 29 f0 ff 0a 18 69 00 03 05 0a')
    emit('7a fa 5c 4d 51 c2')        # return tile in A; no counter increment
    for p,target in branches:
        delta=labels[target]-(p+1)
        assert -128<=delta<=127
        code[p]=delta&255
    return bytes(code)
