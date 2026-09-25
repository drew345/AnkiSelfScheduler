"""Validate a saved checkpoint, export, and prove real import/reimport behavior.

All paths are explicit; work/output directories must be new. No live profiles.
"""
import argparse
import collections
import hashlib
import json
import shutil
import sqlite3
import time
import unicodedata
from pathlib import Path

from anki.collection import Collection, DeckIdLimit, ExportAnkiPackageOptions
from anki.import_export_pb2 import ImportAnkiPackageRequest, ImportAnkiPackageOptions
from anki.utils import base91
from transform_integrate_korean import (
    DIRECTIONS, EXPECTED_INPUT_HASHES, TABLE_KEYS, sha256_file,
    unpack_modern_package, media_digest,
)


def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


def db(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    conn.create_collation('unicase', lambda a, b: (a.casefold() > b.casefold()) - (a.casefold() < b.casefold()))
    conn.row_factory = sqlite3.Row
    return conn


def original_unchanged(before, after):
    a, b = db(before), db(after)
    counts = {}
    try:
        for table, indices in TABLE_KEYS.items():
            old = {tuple(r[i] for i in indices): tuple(r) for r in a.execute('select * from ' + table)}
            new = {tuple(r[i] for i in indices): tuple(r) for r in b.execute('select * from ' + table)}
            assert all(new.get(k) == r for k, r in old.items()), 'original rows changed: ' + table
            counts[table] = len(old)
    finally:
        a.close(); b.close()
    return counts


def validate_sources(sources, target_path):
    target = db(target_path)
    notes = {r['guid']: dict(r) for r in target.execute('select * from notes')}
    cards = {r['nid']: dict(r) for r in target.execute('select * from cards')}
    histories = collections.defaultdict(list)
    for r in target.execute('select * from revlog order by id'):
        histories[r['cid']].append(tuple(r))
    report = {}
    all_new_nids, all_new_cids = set(), set()
    try:
        assert target.execute('pragma integrity_check').fetchone()[0] == 'ok'
        for direction in DIRECTIONS:
            s = db(sources[direction.key])
            try:
                scards = {r['nid']: dict(r) for r in s.execute('select * from cards')}
                epoch_shift = (s.execute('select crt from col').fetchone()[0] - target.execute('select crt from col').fetchone()[0]) // 86400
                cmap = {}; normalization_count = 0; new_order = []
                target_did = target.execute('select id from decks where name COLLATE BINARY=?', (direction.destination_deck,)).fetchone()[0]
                target_mid = target.execute('select id from notetypes where name COLLATE BINARY=?', (direction.note_type,)).fetchone()[0]
                for n in s.execute('select * from notes'):
                    seed = f"anki-self-scheduler-v1|{direction.key}|{n['guid']}|{n['id']}|0".encode()
                    guid = base91(int.from_bytes(hashlib.sha256(seed).digest()[:8], 'big'))
                    nn = notes[guid]; cc = cards[nn['id']]; c = scards[n['id']]
                    f = n['flds'].split('\x1f')
                    expected = '\x1f'.join([f[0], f[1], f[2], f[4]] if len(f) == 5 else [f[1], f[0], '', ''])
                    assert unicodedata.normalize('NFC', expected) == nn['flds'], 'field content mismatch'
                    normalization_count += expected != nn['flds']
                    assert set(n['tags'].split()) == set(nn['tags'].split()), 'tags changed'
                    assert nn['mid'] == target_mid and cc['did'] == target_did
                    assert nn['id'] != n['id'] and cc['id'] != c['id'] and guid != n['guid']
                    assert nn['id'] not in all_new_nids and cc['id'] not in all_new_cids
                    all_new_nids.add(nn['id']); all_new_cids.add(cc['id'])
                    for field in ['type','queue','ivl','factor','reps','lapses','left','odue','odid','flags','data','ord']:
                        if field == 'data':
                            assert json.loads(c[field] or '{}') == json.loads(cc[field] or '{}'), 'card custom data changed'
                        else:
                            assert c[field] == cc[field], 'card field mismatch: ' + field
                    if c['type'] != 0:
                        assert cc['due'] == c['due'] + (0 if c['queue'] == 1 else epoch_shift), 'due date mismatch'
                    else:
                        new_order.append((c['due'], c['id'], cc['due']))
                    cmap[c['id']] = cc['id']
                assert [r[2] for r in sorted(new_order)] == sorted(r[2] for r in new_order), 'new-card order changed'
                source_history = collections.defaultdict(list)
                for r in s.execute('select * from revlog order by id'):
                    if r['cid'] in cmap:
                        source_history[cmap[r['cid']]].append(tuple(r))
                drift = 0; count = 0
                for new_cid in cmap.values():
                    old_rows = source_history[new_cid]; new_rows = histories[new_cid]
                    assert len(old_rows) == len(new_rows), 'history count mismatch'
                    for x,y in zip(old_rows, new_rows):
                        assert x[3:] == y[3:], 'history contents/order mismatch'
                        drift = max(drift, abs(x[0] - y[0])); count += 1
                assert drift <= 10, 'timestamp shift exceeds 10ms verification bound'
                report[direction.destination_deck] = dict(cards=len(cmap), linked_reviews=count, unicode_normalized_notes=normalization_count, max_timestamp_shift_ms=drift)
            finally:
                s.close()
    finally:
        target.close()
    return report


def render_and_structure(path):
    c = Collection(str(path)); result = {}
    try:
        for direction in DIRECTIONS:
            did = c.decks.id(direction.destination_deck, create=False)
            deck = c.decks.get(did)
            assert deck and deck['dyn'] == 0
            conf = c.decks.get_config(deck['conf'])
            assert conf['name'] == direction.preset
            m = c.models.by_name(direction.note_type)
            assert [f['name'] for f in m['flds']] == ['Korean','English','Hanja','Number']
            assert len(m['tmpls']) == 1 and not m['tmpls'][0].get('did')
            assert m['tmpls'][0]['name'] == direction.template
            # Distinct sentinel fields prove the direction without revealing card text.
            note = c.new_note(m)
            note.fields = ['KOREAN_SENTINEL','ENGLISH_SENTINEL','HANJA_SENTINEL','999']
            card = note.ephemeral_card()
            question, answer = card.question(), card.answer()
            front = 'KOREAN_SENTINEL' if direction.key == 'ktoe' else 'ENGLISH_SENTINEL'
            back = 'ENGLISH_SENTINEL' if direction.key == 'ktoe' else 'KOREAN_SENTINEL'
            assert front in question and back not in question and back in answer
            assert '[sound:' not in question + answer
            ids = c.db.list('select id from cards where did=?', did)
            for cid in ids:
                card = c.get_card(cid)
                q,a = card.question(), card.answer()
                assert q.strip() and a.strip() and '[sound:' not in q+a
            result[direction.destination_deck] = {'rendered_cards':len(ids),'direction_verified':True,'normal_deck':True}
    finally:
        c.close()
    return result


def import_packages(path, packages):
    c = Collection(str(path))
    try:
        for p in packages:
            c.import_anki_package(ImportAnkiPackageRequest(package_path=str(p), options=ImportAnkiPackageOptions(merge_notetypes=False, with_scheduling=True, with_deck_configs=True, update_notes=2, update_notetypes=2)))
    finally:
        c.close()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    assert not args.work.exists() and not args.output.exists()
    args.work.mkdir(parents=True);args.output.mkdir(parents=True)
    root=Path(r'C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260921-pre-unification')
    inputs={
        'ktoe':root/'Korean-to-English-Kor-to-Eng-5000/Kor-to-Eng-5000_full-collection_20260921-100600.colpkg',
        'etok':root/'English-to-Korean-zEK5000/zEK5000_full-collection_20260921-101242.colpkg',
        'target':root/'Spare-account-drew3452-Burmese-and-Thai/drew3452_Burmese-and-Thai_full-collection-with-media_20260921-103137.colpkg',
    }
    log('Verify original backups and extract isolated baselines')
    originals={}
    for key,p in inputs.items():
        assert sha256_file(p)==EXPECTED_INPUT_HASHES[key]
        originals[key],_=unpack_modern_package(p,args.work/('original-'+key),include_media=key=='target')
    checkpoint=Path('tmp/integration-20260921-v4/integrated').resolve()
    shutil.copytree(checkpoint,args.work/'candidate')
    candidate=args.work/'candidate/collection.anki2'
    log('Independently compare checkpoint with source collections')
    report={'source_comparison':validate_sources(originals,candidate),'original_rows':original_unchanged(originals['target'],candidate)}
    original_media=media_digest(originals['target'].parent/'collection.media')
    assert media_digest(candidate.parent/'collection.media')==original_media
    log('Render all Korean cards and check directional templates')
    report['rendering']=render_and_structure(candidate)
    log('Export both deck packages with official Anki backend')
    c=Collection(str(candidate)); packages=[]
    try:
        for d in DIRECTIONS:
            p=args.output/(d.destination_deck+'.apkg')
            c.export_anki_package(out_path=str(p),options=ExportAnkiPackageOptions(with_scheduling=True,with_deck_configs=True,with_media=False,legacy=False),limit=DeckIdLimit(deck_id=c.decks.id(d.destination_deck,create=False)))
            packages.append(p)
    finally:c.close()
    # Import path is the intended deployment operation; test it on original target.
    log('Import exported packages into a fresh destination copy')
    shutil.copytree(originals['target'].parent,args.work/'roundtrip')
    roundtrip=args.work/'roundtrip/collection.anki2'
    import_packages(roundtrip,packages)
    report['roundtrip']=validate_sources(originals,roundtrip)
    original_unchanged(originals['target'],roundtrip)
    report['roundtrip_rendering']=render_and_structure(roundtrip)
    # Preserve the global configuration from the existing integration policy.
    c=Collection(str(roundtrip))
    try:
        c.set_config('cardStateCustomizer',Path('src/anki-custom-scheduler.js').read_text(encoding='utf8'))
        c.set_config('collapseTime',4800)
        c.set_config('newCardsIgnoreReviewLimit',True)
        c.set_config('applyAllParentLimits',False)
        c.set_config('fsrs',False)
    finally:c.close()
    log('Test reimport: existing notes, cards, and history must remain unchanged')
    shutil.copy2(roundtrip,args.work/'before-reimport.anki2')
    import_packages(roundtrip,packages)
    original_unchanged(args.work/'before-reimport.anki2',roundtrip)
    conn=db(roundtrip)
    report['totals']={t:conn.execute('select count(*) from '+t).fetchone()[0] for t in ['notes','cards','revlog']};conn.close()
    assert report['totals']=={'notes':13213,'cards':15757,'revlog':719013}
    assert media_digest(roundtrip.parent/'collection.media')==original_media
    log('Export integrated test collection and verify its contents')
    full=args.output/'drew3452-integrated-TEST-ONLY.colpkg'
    c=Collection(str(roundtrip))
    try:c.export_collection_package(str(full),include_media=True,legacy=False)
    finally:c.close()
    exported,media=unpack_modern_package(full,args.work/'export-check',include_media=True)
    original_unchanged(roundtrip,exported)
    assert media_digest(media)==original_media
    report.update(status='verified offline; not deployed',reimport_unchanged=True,media_files=original_media[0],global_settings_note='Learn Ahead is set collection-wide to 80 minutes, affecting all decks. Custom scheduling is guarded to the two Korean roots.',outputs={p.name:{'sha256':sha256_file(p),'bytes':p.stat().st_size} for p in [*packages,full]})
    (args.output/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    log('PASS: source comparison, rendering, real import, reimport, media, collection export')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
