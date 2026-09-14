"""Glyph-by-glyph transcription from the five extracted AO2 font sheets.

Keep uncertain readings explicit; do not infer Japanese from an AO1 table.
The JSON output is a review source, not proof that all Japanese was proofread.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
rows = {
    0x0C5: '武器攻撃生腕正精移動力',
    0x0D0: '乱制復退防々:敏剣操ぅ守備抑拒地',
    0x0E0: '魔法治癒必突盗冷凍十青獅子気合鳥',
    0x0F0: '特弾行具間見炎一要残酔技約右向泣',
    0x100: '定抜大図鉱横歩形',
    0x110: '道路海山平野地森',
    0x11A: '戻続進命令草',
    0x120: '性丘取消終了町村都',
    0x12D: '神瞬効',
    0x132: '持物果名ー雷火触ゥ名待石化済',
    0x140: '手右左頭服体回',
    0x14A: '中重冊ェ剥重',
    0x150: '鍵目選ぉ',
    0x155: 'ォ択率棲点ぃィぇ値',
    0x160: '装備ヴ而足異常葉城',
    0x17B: '言急号器',
    0x188: '世勇者王国平和戻',
    0x190: '余助母私無事知界旅出思合残念失礼',
    0x1A0: '陛下心中行達父様今一緒何起我不死',
    0x1B0: '小僧吟遊詩人哀永遠語給新英雄頌歌',
    0x1C0: '騎士妃取乱待女生命令竜承腰高手首',
    0x1D0: '返甘反逆剣流長飛大変墓地落来見前',
    0x1E0: '殺呼魔術師海東召喚法将軍精鋭部隊',
    0x1F0: '司祭方理娘丈夫太陽室守枢機卿救亡',
    0x200: '苦労件決口外神御霊光慈悲明日備休',
    0x210: '団物任務他侵攻年戦争悪真紅閃役言',
    0x220: '聖上文字味親恨許気友本渇殺昔共後',
    0x230: '職遺従当涯望勝利度劇営重必要城固',
    0x240: '塔立黒常白門閉聞子稽古巡眠西酒場',
    0x250: '眠用屋宿泊娘冒険記録帳入廉滅名活',
    0x260: '想指代求現男忘欲秘力千操兵彼船乗',
    0x270: '相料特妙扉消間趣夜多堂蘇治癒寄付',
    0x280: '忍全能売更再息吹清水痛時問仲儀非',
    0x290: '諸南辺強居作的分仕妻宝道紹護参二',
    0x2A0: '先昨港町利圧宜方告撃空近冒赤晩会',
    0x2B0: '染申引渡謎頭冷静考集結奪回転世向',
    0x2C0: '意頼敵身王連足少対関係皆虎住城丘',
    0x2D0: '漢差階病陣間開完涙糸寒受民居温都',
    0x2E0: '描形己信道進運食昼金属袋別業麗伯',
    0x2F0: '爵供産毎心感謝罪憎幼良所官廷庭底',
    0x300: '熟才喜飲店買売品色具燃博村拝客品',
    0x310: '左危移使果続誰尾殿因縁加兵修様足',
    0x320: '指月内刻恐追動兄姫闘退状態迷惑習',
    0x330: '期通未半敗走至増援万根元面逃二持',
    0x340: '監視正義血節獣育運化邪孔鳥姿爆速',
    0x350: '真顔有育天探帰葉止次働成建者老同',
    0x360: '故野郎笑始絹狂破熱愛溢威優姫乙岩',
    0x370: '屈照歩初薬康以凍弾ぬ杖怒映員準着',
    0x380: '折曲案望下座自専暴切墓支導呪歴史',
    0x390: '引豊又絶頂富封砂渡髪栄偉散功荷由',
    0x3A0: '忍送現防責誰葉父厄印岩招焦蔵声借',
    0x3B0: '那妹禁放体簡単阻寺院跡皆覚荒晶姫',
    0x3C0: '去少弱復話塞苗討頑殺可惜跡北君長',
    0x3D0: '定質断奥刻銃也笑頃続黒塔貴負情提',
    0x3E0: '表能崇喜美輝汗遅柄越品石捧肉闇幸',
    0x3F0: '約束限呪止興造活在注討落交接影逢',
    0x400: '市斬原隣故慈排喜空置若郎屋頼墓光',
    0x410: '猫火迫僕没故払賢組患材迎黙雄故害',
    0x420: '猫陸波嵐氷必悔泣凸誉山炭飲武器紋',
    0x430: '万商発番汲忘種斧還評議雪官兄位々',
    0x440: '「」',
}
mapping = {}
for start, text in rows.items():
    assert len(text) <= 16, (hex(start), text, len(text))
    for offset, char in enumerate(text):
        code = start + offset
        assert code not in mapping, hex(code)
        mapping[code] = char
# Resolve readings against repeated original Japanese sentences. Pixel-font
# transcriptions above are deliberately retained as a review trail.
context_fixes = {
    0x0D0:'乱',0x0D1:'制',0x0D2:'復',0x0D7:'戦',0x0D9:'機',
    0x0DF:'地',0x0EF:'鳥',0x0F7:'ー',0x0FF:'決',0x11F:'墓',
    0x120:'士',0x12E:'能',0x141:'方',0x153:'上',0x155:'間',
    0x159:'的',0x15C:'ィ',0x15D:'ェ',0x15E:'ぉ',0x167:'薬',
    0x158:'率',0x20E:'備',0x217:'年',0x21B:'導',0x21C:'征',
    0x21D:'服',0x222:'十',0x223:'字',0x22B:'謁',0x23A:'警',
    0x25C:'願',0x2A6:'宣',0x2A7:'布',0x2C4:'主',0x2CE:'抵',
    0x2CF:'抗',0x30A:'然',0x30B:'便',0x317:'解',0x31E:'練',
    0x36D:'妖',0x379:'快',0x399:'繁',0x3A2:'摂',0x3A3:'政',
    0x3A7:'災',0x3BF:'傷',0x3C8:'預',0x3CC:'姉',0x3D6:'屯',
    0x3DF:'彼',0x3F3:'脱',0x41D:'確',0x41E:'被',0x42F:'緑',
}
mapping.update(context_fixes)
# Repeated phrases in dialogue, rather than visually similar pixel strokes.
mapping.update({0x0FD:'方',0x139:'敵',0x152:'目',0x1F9:'家',
                0x221:'十',0x222:'字',0x223:'率',0x25F:'高',
                0x266:'忌',0x273:'炒',0x274:'最',0x276:'聞',
                0x284:'志',0x285:'倒',0x28C:'間',0x290:'識',
                0x294:'房',0x296:'飯',0x29B:'過',0x29C:'保',
                0x29F:'上',0x2A4:'制',0x2AC:'配',0x2B4:'談',0x1B6:'魂',0x3AC:'輪',
                0x2BD:'伝',0x2BE:'協',0x2C0:'急',0x2CC:'族'})
# The narrow original pixel font makes these readings ambiguous. Resolve them
# against source sentences before allowing translated text to be finalized.
uncertain = [0x0D2,0x0D7,0x11F,0x129,0x12E,0x153,0x155,0x159,
             0x163,0x167,0x17B,0x17E,0x20E,0x21D,0x25C,0x28E,
             0x2A6,0x2AE,0x2B0,0x2C4,0x2CE,0x309,0x30B,0x317,
             0x31E,0x348,0x355,0x366,0x36D,0x379,0x396,0x399,
             0x3A2,0x3A7,0x3A8,0x3AE,0x3BF,0x3C8,0x3CC,0x3D6,
             0x3F3,0x3F9,0x415,0x41A,0x41D,0x41E,0x421,0x42F]
(ROOT/'ao2/translation/chartable_fixes.json').write_text(json.dumps(
    {f'{k:03X}':v for k,v in sorted(mapping.items())}, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT/'ao2/translation/chartable_review_pending.json').write_text(json.dumps(
    {'status':'draft; all readings need final source review',
     'ambiguous_codes':[f'{k:03X}' for k in uncertain if k not in context_fixes],
     'context_corrected_codes':[f'{k:03X}' for k in context_fixes]}, indent=2), encoding='utf-8')
print('manual glyph transcriptions', len(mapping), 'readings to review',len(uncertain))
