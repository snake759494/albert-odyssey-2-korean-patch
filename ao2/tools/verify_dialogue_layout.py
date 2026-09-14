"""Check serialized dialogue and conservatively scan native event windows.

This does not assert that undecoded event roots are reachable or verified.
Native event bytes are preserved, so none of these checks rewrite game logic.
"""
from pathlib import Path
import json
from translation_data import load_dialogue, cells

ROOT=Path(__file__).resolve().parents[2]
translations=load_dialogue()
entries=json.loads((ROOT/'ao2/build/font_prototype/inserted_dialogue.json').read_text(encoding='utf-8'))
codes={int(e['id'].split('_')[1]):e['codes'] for e in entries}
events=json.loads((ROOT/'ao2/analysis/event_scripts.json').read_text())
windows=[]
for script in events['scripts']:
    words=script['words']
    for start,w in enumerate(words):
        if w>=len(translations):continue
        line_ids=[];glyphs=set()
        for index in words[start:start+3]:
            if index>=len(translations):break
            line_ids.append(index)
            glyphs.update(c for c in codes[index] if c>=0x180)
            windows.append({'script':f"CB{script['address']:04X}", 'line_ids':line_ids.copy(),
                            'dynamic_glyphs':len(glyphs)})
overflow=[w for w in windows if w['dynamic_glyphs']>56]
report={
    'scope':'static serialized dialogue and contiguous native event windows; not a gameplay run',
    'translated_records':len(translations),
    'max_cells_per_record':max(map(cells,translations.values())),
    'native_line_limit':32,'native_lines_per_page':3,'native_dynamic_glyph_capacity':56,
    'event_windows_checked':len(windows),'overflow_windows':overflow,
    'largest_windows':sorted(windows,key=lambda w:w['dynamic_glyphs'],reverse=True)[:20],
    'unresolved_event_roots':events['unresolved_roots'],
    'partially_decoded_scripts':[s for s in events['scripts'] if s['invalid_words']],
    'event_control_bytes_changed':False,
}
assert len(translations)==2131
assert report['max_cells_per_record']<=32
assert not overflow,overflow
(ROOT/'ao2/analysis/dialogue_layout_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['largest_windows','partially_decoded_scripts']},ensure_ascii=False))
