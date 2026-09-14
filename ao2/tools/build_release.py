"""Package a verified integration ROM and prove the xdelta round trip.

The release report distinguishes static/isolated CPU checks from game progress.
The Japanese original, AO1 build, v02 build, SRAM and save states are untouched.
"""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
stage=ROOT/'ao2/build/ui_stage';analysis=ROOT/'ao2/analysis'
original_path=ROOT/'Albert Odyssey 2 Jashin no Taidou.smc'
original=original_path.read_bytes();rom=next(stage.glob('*.sfc')).read_bytes()
report=json.loads((stage/'report.json').read_text(encoding='utf-8'))
inv=json.loads((stage/'inventory_report.json').read_text(encoding='utf-8'))
battle=json.loads((stage/'battle_ui_report.json').read_text(encoding='utf-8'))
def digest(data):return hashlib.sha256(data).hexdigest()
assert digest(original)=='7c6fe76fe1a414407435c7393f4d9b50a885fa6055cd9d94549725884497698b'
assert digest(rom)==report['sha256']
assert len(rom)==0x400000 and rom[0xffd7]==12
check=int.from_bytes(rom[0xffde:0xffe0],'little')
assert sum(rom)&65535==check and int.from_bytes(rom[0xffdc:0xffde],'little')==check^65535
allowed=[(0x2503a,0x2505d),(0x2507a,0x2507e),(0x25088,0x250a1),(0x252ba,0x252d8),
 (0x2c6b6,0x2c6ba),(0x24f9d,0x24fa0),(0x41a11,0x41a14),
 (0xfe495,0xfe4b3),(0xfe4fc,0xfe515),(0x250b5,0x250b9),(0xfe529,0xfe52d),
 (0xffd7,0xffd8),(0xffdc,0xffe0),(0x2cb82,0x2cc23),(0x60000,int(report['ui_text_end'],16)),
 (0xfe0a0,0xfe208),(0x4d1da,0x4d3da),(0x4d458,inv['item_data_end']),
 (0x2887c,0x28881),(0x49aa1,0x49aa5),(0x49b34,0x49b36),(0x49b3b,0x49b3d),
 (0x24026,0x2402d),(0x49e2d,0x49e40),(0x4a74f,0x4a764)]
for p in [0x21010,0x21016,0x2101c,0x21022,0x21028]:allowed.append((p,p+2))
for s in report['font_context']['scene_init_hooks']:
 p=int(s,16);allowed.append((p,p+4))
for p in [0x3a0,0x3cb,0x3f6,0x48e31]:allowed.append((p,p+4))
for s in report['item_list_layout']['operand_patches']:
 p=int(s,16);allowed.append((p,p+2))
for g in report['grid_position_changes']:
 p=int(g['grid'],16)
 while original[p]!=255:
  if int.from_bytes(original[p+2:p+4],'little')==g['index']:allowed.append((p,p+1));break
  p+=4
for e in inv['direct_strings']:
 p=int(e['address'],16);allowed.append((p,p+e['original_cells']*2))
allowed.extend(report['field_ui']['modified_ranges'])
allowed.extend((e['address'],e['end']) for e in inv['help_edits'])
mask=bytearray(0x200000)
allowed.extend([(0x50007,0x5000b),(0x28b90,0x28b94),(0x53cd1,0x53cd3),(0x53cd6,0x53cd8),(0x5314a,0x5314b)])
allowed.extend((p+1,p+4) for p in battle['operand_patches'])
for a,z in allowed:mask[a:z]=b'\x01'*(z-a)
unexpected=[p for p,(a,b) in enumerate(zip(original,rom)) if a!=b and not mask[p]]
assert not unexpected,[hex(p) for p in unexpected[:30]]
assert rom[0xb0000:0xc0000]==original[0xb0000:0xc0000], 'event control data changed'
protected={}
assert int(report['ui_text_end'],16)<=0x67c9e
assert rom[0x67c9e:0x68000]==original[0x67c9e:0x68000], 'UI pool overflow'
previous=ROOT/'Albert Odyssey 2 - Korean Full v05.sfc'
assert digest(previous.read_bytes())=='4da81fa321c7b3608d5957ee5fe6bf2a95e3f8d483ef4d50db5b56c4e232964e'
protected[previous.name]=digest(previous.read_bytes())
for name,sha in [('Albert Odyssey - Korean Full.sfc','5509b4d8afda2bc497c2245bd2824629a703eac907d65660347041ffba2f183b'),
                 ('Albert Odyssey 2 - Korean Test v02.sfc','e4cfcb6bd1f9181e17f511aecd8b84565e5a174bfeeaa5e17515233972d8ba37'),
                 ('Albert Odyssey 2 - Korean Full v03.sfc','82b1bd30fedf654a9470dab2ef8e927ca9545d056f3be377b89f88c9de665d16'),
                 ('Albert Odyssey 2 - Korean Full v04.sfc','32a923fffe9757f5691ffbf24499233d0e1af2dc4a34d51b46e7a1aabd9527e3')]:
 p=ROOT/name;assert digest(p.read_bytes())==sha,name;protected[name]=sha
checks={}
for name in ['translation_validation.json','dialogue_layout_verification.json','ui_grid_audit.json',
             'ui_cpu/report.json','font_context_cpu/report.json','item_list_cpu/report.json',
             'clock_cpu/report.json','battle_item_cpu/report.json','battle_ui_cpu/report.json',
             'dialogue_native_cpu/report.json','font_cpu_fix/report.json','field_ui_cpu/report.json']:
 checks[name]=json.loads((analysis/name).read_text(encoding='utf-8'))
assert checks['translation_validation.json']['translated_records']==2131
assert not checks['translation_validation.json']['over_32_cells']
assert not checks['dialogue_layout_verification.json']['overflow_windows']
assert not checks['ui_grid_audit.json']['growth_conflicts']
assert checks['dialogue_native_cpu/report.json']['completed_records']==2131
assert checks['dialogue_native_cpu/report.json']['boundary_guards_preserved']
target=ROOT/'Albert Odyssey 2 - Korean Full v06.sfc';patch=target.with_suffix('.xdelta')
target.write_bytes(rom)
subprocess.run([str(ROOT/'xdelta.exe'),'-f','-e','-s',str(original_path),str(target),str(patch)],check=True)
roundtrip=ROOT/'ao2/build/release_roundtrip.sfc'
subprocess.run([str(ROOT/'xdelta.exe'),'-f','-d','-s',str(original_path),str(patch),str(roundtrip)],check=True)
assert roundtrip.read_bytes()==rom
out=ROOT/'ao2/build/release_v06';out.mkdir(parents=True,exist_ok=True)
gameplay=json.loads((analysis/'gameplay_v06.json').read_text(encoding='utf8'))
assert gameplay['sha256']==digest(rom)
summary={'gameplay':gameplay,'version':'v06','rom':str(target),'patch':str(patch),'sha256':digest(rom),'rom_bytes':len(rom),
 'dialogue_window_extension':report['dialogue_window'],
 'field_ui':report['field_ui'],'inventory_help_strings':inv['help_edits'],
 'dialogue_records':2131,'ui_records':report['ui_records_inserted'],'item_names':255,
 'direct_ui_strings':len(inv['direct_strings']),'compressed_menu_maps':len(inv['compressed_resource_redirects']),
 'checksum_valid':True,'xdelta_roundtrip_identical':True,'original_changes_whitelisted':True,
 'event_data_unchanged':True,'preserved_builds':protected,'checks':checks,
 'verification_scope':'actual Snes9x gameplay from reset through opening, name entry, first field battle; movement, status, terrain, skills, equipment and empty item lists; normal/special attack and enemy turn; plus isolated CPU/VRAM tests. Ending and all later encounters were not played.',
 'untranslated_auxiliary_records':report['pending_ui_ids'],
 'auxiliary_classification':'debug/sound-test labels and legacy enemy names outside the 54 native encounter tables; full reachability not proven'}
(out/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['checks','preserved_builds']},ensure_ascii=False))
