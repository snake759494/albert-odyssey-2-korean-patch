"""Reproducible, read-only AO2 font inventory and native capacity checks."""
from pathlib import Path
import hashlib
import json
from codec import decompress

root = Path(__file__).resolve().parents[2]
rom = (root/'Albert Odyssey 2 Jashin no Taidou.smc').read_bytes()
expected = '7c6fe76fe1a414407435c7393f4d9b50a885fa6055cd9d94549725884497698b'
assert hashlib.sha256(rom).hexdigest() == expected
glyphs = []
for code in range(0x480):
    p = 0x130000 + int.from_bytes(rom[0x130000+code*2:0x130002+code*2], 'little')
    glyph, end = decompress(rom, p)
    assert len(glyph) == 32, (code, p, len(glyph))
    assert 0x130900 <= p < end <= 0x140000
    glyphs.append(glyph)
assert rom[0x250cd:0x250d2] == bytes.fromhex('c9 38 00 b0 50')
records = json.loads((root/'ao2/analysis/records_raw.json').read_text())
used = {c for r in records if r['group']=='dialogue' for c in r['codes']}
result = {
    'source_sha256': expected,
    'total_font_pointer_entries': len(glyphs),
    'unique_bitmaps_all_entries': len(set(glyphs)),
    'separate_kanji_range_inclusive': ['188', '43E'],
    'separate_kanji_slots': 0x43f-0x188,
    'separate_kanji_unique_bitmaps': len(set(glyphs[0x188:0x43f])),
    'separate_kanji_codes_referenced_by_dialogue_table': len(used & set(range(0x188,0x43f))),
    'native_dynamic_copy_counter_limit': 0x38,
    'dynamic_counter_lifetime_verified': False,
    'menu_extended_glyph_support_verified': False,
    'full_translation_completed': False,
    'korean_rom_built': False,
    'note': '695 is the separate kanji block, not the total including base-font kanji. 1152 includes kana, symbols and blank entries.',
}
(root/'ao2/analysis/font_survey.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
