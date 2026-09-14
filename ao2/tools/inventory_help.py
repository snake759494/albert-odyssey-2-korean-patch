"""Length-prefixed item-use messages omitted by the terminated-string scanner."""
TEXTS=['사용할','도구를','선택하세요','X 버튼으로 정리합니다','이 도구는 사용할 수 없습니다','을',
       '누구에게 사용할지','전투불능 동료가 없습니다','이 도구는 필드에서 사용합니다','사용할까요?',
       '경험치가','공격력이','명중률이','수비력이','회피율이','특수율이','방어율이','최대 체력이','최대 정신력이','이동력이','올랐다']
FIXED={0x4950d:('장비하기',5),0x49517:('장비해제',6),0x49554:('바꿀 장비를 선택하세요',12),0x4959d:('장비할 것을 선택하세요',12),0x495e6:('해제할 장비를 선택하세요',13),0x498d5:('LV:체력 정신력/',10)}
ALL_TEXT=TEXTS+[s for s,n in FIXED.values()]
def install(rom,original,mapping):
    edits=[]
    for i,text in enumerate(TEXTS):
        p=0x40000+int.from_bytes(original[0x4c116+i*2:0x4c118+i*2],'little');n=original[p]
        assert len(text)<=n,(i,text,n)
        def word(c):
            k=mapping[c];return ((k&0x1f0)*2)|(k&15)
        rom[p+1:p+1+n*2]=b''.join(word(c).to_bytes(2,'little') for c in text.ljust(n))
        edits.append({'address':p+1,'end':p+1+n*2,'korean':text,'cells':n})
    for p,(text,n) in FIXED.items():
        assert len(text)<=n,(text,n)
        rom[p:p+n*2]=b''.join(word(c).to_bytes(2,'little') for c in text.ljust(n))
        edits.append({'address':p,'end':p+n*2,'korean':text,'cells':n})
    return edits

