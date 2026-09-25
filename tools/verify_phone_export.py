"""Read back a phone export into a new local verification directory, never live data."""
import argparse
import json
from pathlib import Path
from anki.collection import Collection
from finish_integration import validate_sources, render_and_structure
from transform_integrate_korean import unpack_modern_package, DIRECTIONS

ap=argparse.ArgumentParser()
ap.add_argument('package',type=Path)
ap.add_argument('work',type=Path)
args=ap.parse_args()
assert not args.work.exists(), 'Use a new verification directory'
path,_=unpack_modern_package(args.package,args.work,include_media=False)
sources={k:Path('tmp/integration-finish-v6')/('original-'+k)/'collection.anki2' for k in ['ktoe','etok']}
report={'source_comparison':validate_sources(sources,path)}
report['rendering']=render_and_structure(path)
c=Collection(str(path))
try:
    assert c.db.scalar('select count(*) from cards')==10063
    assert c.db.scalar('select count(*) from notes')==10063
    for name in ['Burmese','Pocket Thai Vocab','Thai Alphabet','Thai Vowels and Vowel Combinations','Thai_Alphabet2']:
        assert c.decks.id(name,create=False) is None
    source=Path('src/anki-custom-scheduler.js').read_text(encoding='utf8')
    assert c.get_config('cardStateCustomizer').replace('\r\n','\n')==source
    assert c.get_config('collapseTime')==4800
    assert not c.get_config('fsrs',False)
    presets={}
    for direction in DIRECTIONS:
        deck=c.decks.get(c.decks.id(direction.destination_deck,create=False))
        conf=c.decks.get_config(deck['conf'])
        presets[direction.destination_deck]=conf
    report['settings']={'scheduler_exact':True,'learn_ahead_minutes':80,'fsrs':False}
    report['counts']={'cards':10063,'notes':10063}
finally:
    c.close()
baseline=Collection(str(Path('tmp/integration-finish-v6/roundtrip/collection.anki2').resolve()))
try:
    for direction in DIRECTIONS:
        deck=baseline.decks.get(baseline.decks.id(direction.destination_deck,create=False))
        expected=baseline.decks.get_config(deck['conf'])
        actual=presets[direction.destination_deck]
        for k,v in expected.items():
            if k not in ['id','name','mod','usn']:
                assert actual[k]==v, f'Preset mismatch: {direction.destination_deck} {k}'
finally:
    baseline.close()
report['preset_behavior_preserved']=True
print(json.dumps(report,indent=2))
