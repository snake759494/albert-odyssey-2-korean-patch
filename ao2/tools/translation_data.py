"""Load contiguous, explicitly indexed translation records without silent shifts."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]

def load_dialogue():
    result = {}
    for path in sorted((ROOT/'ao2/translation').glob('dialogue_*.ko.txt')):
        match = re.fullmatch(r'dialogue_(\d+)_(\d+)\.ko\.txt', path.name)
        if not match:
            raise ValueError(path)
        start, end = map(int, match.groups())
        lines = path.read_text(encoding='utf-8').splitlines()
        assert len(lines) == end-start+1, (path.name, len(lines), end-start+1)
        for index, line in enumerate(lines, start):
            assert index not in result, ('duplicate', index)
            assert line, ('empty record; use an explicit blank space', index)
            result[index] = line
    assert sorted(result) == list(range(len(result))), 'gap in translated record IDs'
    return result

def tokens(text):
    return re.findall(r'\{PLAYER\}|.', text)

def cells(text):
    return sum(5 if token == '{PLAYER}' else 1 for token in tokens(text))

if __name__ == '__main__':
    translations = load_dialogue()
    records = {r['index']: r for r in json.loads((ROOT/'ao2/analysis/records_raw.json').read_text()) if r['group']=='dialogue'}
    mismatches = []
    for index, text in translations.items():
        codes = records[index]['codes']
        count = sum(codes[i:i+5] == [0,1,2,3,4] for i in range(len(codes)-4))
        if count != text.count('{PLAYER}'):
            mismatches.append(index)
    report = {'translated_records':len(translations), 'total_records':len(records),
              'player_placeholder_mismatches':mismatches,
              'over_32_cells':[{ 'index':i,'cells':cells(t)} for i,t in translations.items() if cells(t)>32],
              'unique_hangul':len({c for t in translations.values() for c in t if '가'<=c<='힣'})}
    (ROOT/'ao2/analysis/translation_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    assert not mismatches, 'player name placeholder mismatch'
