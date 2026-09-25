#!/usr/bin/env python3
"""Build and verify an isolated Korean-deck integration collection.

This script operates on copies extracted from verified .colpkg backups. It uses
Anki's own Python/backend package for schema-aware object creation and export,
and direct SQLite writes only for scheduling fields and review history that the
public add-note API does not preserve.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import zstandard as zstd
from anki.collection import (
    AddNoteRequest,
    Collection,
    DeckIdLimit,
    ExportAnkiPackageOptions,
)
from anki.import_export_pb2 import MediaEntries
from anki.utils import base91, split_fields


EXPECTED_INPUT_HASHES = {
    "ktoe": "58E656EDF03A5C2B94B9EB8F46FF121533DE6F89C5218671DDBEF73CFF80D631",
    "etok": "59ED6AB4B3CE0F8368913968E208B01189C8C56983F04743DBA28EED1A67E2B8",
    "target": "30E26350809235B7CC2D6DD52EC4030D1741617D390DA622BBE4781E23DF6C2D",
}

TABLE_KEYS = {
    "decks": (0,),
    "deck_config": (0,),
    "notetypes": (0,),
    "fields": (0, 1),
    "templates": (0, 1),
    "notes": (0,),
    "cards": (0,),
    "revlog": (0,),
}


@dataclass(frozen=True)
class Direction:
    key: str
    source_deck: str
    destination_deck: str
    note_type: str
    template: str
    preset: str


DIRECTIONS = (
    Direction(
        key="ktoe",
        source_deck="Kor to Eng 5000",
        destination_deck="Kor2Eng5000",
        note_type="Kor2Eng5000 Note",
        template="Kor2Eng",
        preset="Kor2Eng5000 Options",
    ),
    Direction(
        key="etok",
        source_deck="zEK5000",
        destination_deck="Eng2Kor5000",
        note_type="Eng2Kor5000 Note",
        template="Eng2Kor",
        preset="Eng2Kor5000 Options",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def zstd_decompress(data: bytes) -> bytes:
    with zstd.ZstdDecompressor().stream_reader(io.BytesIO(data)) as reader:
        return reader.read()


@contextmanager
def open_sqlite(path: Path):
    db = sqlite3.connect(path)
    db.create_collation("unicase", lambda left, right: (left.casefold() > right.casefold()) - (left.casefold() < right.casefold()))
    try:
        yield db
    finally:
        db.close()


def safe_media_path(root: Path, name: str) -> Path:
    candidate = (root / name).resolve()
    root_resolved = root.resolve()
    if root_resolved != candidate and root_resolved not in candidate.parents:
        raise ValueError(f"unsafe media path: {name!r}")
    return candidate


def unpack_modern_package(package: Path, profile_dir: Path, include_media: bool) -> tuple[Path, Path]:
    if profile_dir.exists():
        raise FileExistsError(f"working directory already exists: {profile_dir}")
    profile_dir.mkdir(parents=True)
    collection_path = profile_dir / "collection.anki2"
    media_dir = profile_dir / "collection.media"
    media_dir.mkdir()

    with zipfile.ZipFile(package) as archive:
        if archive.read("meta") != b"\x08\x03":
            raise ValueError(f"{package.name} is not a modern Anki package")
        collection_path.write_bytes(zstd_decompress(archive.read("collection.anki21b")))

        if include_media:
            entries = MediaEntries.FromString(zstd_decompress(archive.read("media")))
            for index, entry in enumerate(entries.entries):
                archive_index = entry.legacy_zip_filename if entry.HasField("legacy_zip_filename") else index
                payload = zstd_decompress(archive.read(str(archive_index)))
                if len(payload) != entry.size:
                    raise ValueError(f"media size mismatch for {entry.name}")
                if entry.sha1 and hashlib.sha1(payload).digest() != entry.sha1:
                    raise ValueError(f"media digest mismatch for {entry.name}")
                destination = safe_media_path(media_dir, entry.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)

    with open_sqlite(collection_path) as db:
        if db.execute("pragma integrity_check").fetchone()[0] != "ok":
            raise ValueError(f"SQLite integrity check failed for {package.name}")
    return collection_path, media_dir


def media_digest(media_dir: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in media_dir.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(media_dir).as_posix().encode("utf8")
        payload_hash = hashlib.sha256(path.read_bytes()).digest()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(payload_hash)
    return len(files), digest.hexdigest()


def encode_cell(value: Any) -> bytes:
    if value is None:
        return b"N"
    if isinstance(value, bytes):
        return b"B" + len(value).to_bytes(8, "big") + value
    payload = str(value).encode("utf8")
    return b"T" + len(payload).to_bytes(8, "big") + payload


def digest_rows(rows: Iterable[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(b"R")
        for value in row:
            digest.update(encode_cell(value))
    return digest.hexdigest()


def snapshot_original_rows(collection_path: Path) -> tuple[dict[str, set[tuple[Any, ...]]], dict[str, str]]:
    keys: dict[str, set[tuple[Any, ...]]] = {}
    digests: dict[str, str] = {}
    with open_sqlite(collection_path) as db:
        for table, key_indexes in TABLE_KEYS.items():
            rows = list(db.execute(f"select * from {table}"))
            keys[table] = {tuple(row[index] for index in key_indexes) for row in rows}
            digests[table] = digest_rows(sorted(rows, key=lambda row: tuple(row[index] for index in key_indexes)))
    return keys, digests


def verify_original_rows(
    collection_path: Path,
    original_keys: dict[str, set[tuple[Any, ...]]],
    original_digests: dict[str, str],
) -> None:
    with open_sqlite(collection_path) as db:
        for table, key_indexes in TABLE_KEYS.items():
            rows = list(db.execute(f"select * from {table}"))
            retained = [
                row
                for row in rows
                if tuple(row[index] for index in key_indexes) in original_keys[table]
            ]
            if len(retained) != len(original_keys[table]):
                raise AssertionError(f"original {table} row count changed")
            if digest_rows(sorted(retained, key=lambda row: tuple(row[index] for index in key_indexes))) != original_digests[table]:
                raise AssertionError(f"original {table} rows changed")


def deterministic_guid(namespace: str, source_guid: str, source_nid: int, occupied: set[str]) -> str:
    salt = 0
    while True:
        seed = f"anki-self-scheduler-v1|{namespace}|{source_guid}|{source_nid}|{salt}".encode()
        candidate = base91(int.from_bytes(hashlib.sha256(seed).digest()[:8], "big"))
        if candidate not in occupied:
            occupied.add(candidate)
            return candidate
        salt += 1


def clone_directional_notetype(
    target: Collection,
    source: Collection,
    source_mid: int,
    direction: Direction,
    destination_deck_id: int,
) -> int:
    source_model = source.models.get(source_mid)
    if not source_model:
        raise ValueError(f"missing source notetype {source_mid}")

    model = target.models.new(direction.note_type)
    for key in ("css", "latexPre", "latexPost", "latexsvg"):
        model[key] = copy.deepcopy(source_model[key])
    model["sortf"] = 3  # Number after Audio is removed.
    model["did"] = destination_deck_id

    source_fields = {field["name"]: field for field in source_model["flds"]}
    for field_name in ("Korean", "English", "Hanja", "Number"):
        field = target.models.new_field(field_name)
        source_field = source_fields[field_name]
        for key in (
            "sticky",
            "rtl",
            "font",
            "size",
            "description",
            "plainText",
            "collapsed",
            "excludeFromSearch",
            "preventDeletion",
        ):
            if key in source_field:
                field[key] = copy.deepcopy(source_field[key])
        target.models.add_field(model, field)

    source_template = source_model["tmpls"][0]
    template = target.models.new_template(direction.template)
    template["qfmt"] = source_template["qfmt"].replace("{{Audio}}", "")
    template["afmt"] = source_template["afmt"].replace("{{Audio}}", "")
    template["bqfmt"] = source_template.get("bqfmt", "")
    template["bafmt"] = source_template.get("bafmt", "")
    template["bfont"] = source_template.get("bfont", "Arial")
    template["bsize"] = source_template.get("bsize", 12)
    template["did"] = None
    target.models.add_template(model, template)

    result = target.models.add(model)
    return int(result.id)


def source_rows(source: Collection, source_deck_id: int) -> list[tuple[Any, ...]]:
    rows = source.db.all(
        """
        select n.id,n.guid,n.mid,n.mod,n.tags,n.flds,n.flags,n.data,
               c.id,c.mod,c.type,c.queue,c.due,c.ivl,c.factor,c.reps,c.lapses,
               c.left,c.odue,c.odid,c.flags,c.data
        from notes n join cards c on c.nid=n.id
        where c.did=?
        order by case when c.type=0 then 0 else 1 end,c.due,c.id
        """,
        source_deck_id,
    )
    note_ids = [row[0] for row in rows]
    if len(note_ids) != len(set(note_ids)):
        raise AssertionError("expected exactly one card per source note")
    return rows


def map_fields(direction: Direction, source_mid: int, values: list[str]) -> list[str]:
    if source_mid == 1076778696:
        if len(values) != 5:
            raise AssertionError("unexpected Korean Vocab field count")
        korean, english, hanja, _audio, number = values
        return [korean, english, hanja, number]
    if direction.key == "etok" and len(values) == 2:
        front_english, back_korean = values
        return [back_korean, front_english, "", ""]
    raise AssertionError(f"unexpected notetype {source_mid} in {direction.source_deck}")


def due_for_target(card_type: int, queue: int, source_due: int, day_shift: int, new_due: int) -> int:
    if card_type == 0:
        return new_due
    if queue == 1:
        return source_due
    return source_due + day_shift


def add_direction(
    target: Collection,
    source: Collection,
    direction: Direction,
    scheduler_script: str,
    occupied_guids: set[str],
    next_new_position: int,
) -> tuple[dict[str, Any], dict[int, int], int]:
    if target.decks.id(direction.destination_deck, create=False):
        raise AssertionError(f"destination deck already exists: {direction.destination_deck}")
    if target.models.by_name(direction.note_type):
        raise AssertionError(f"destination notetype already exists: {direction.note_type}")

    source_deck_id = int(source.decks.id(direction.source_deck, create=False) or 0)
    if not source_deck_id:
        raise ValueError(f"missing source deck {direction.source_deck}")
    source_deck = source.decks.get(source_deck_id)
    assert source_deck
    source_config = source.decks.get_config(source_deck["conf"])
    assert source_config

    new_config = target.decks.add_config(direction.preset, clone_from=source_config)
    # DeckManager.id()'s `type` argument selects normal vs. filtered deck; it
    # is not a preset ID. Create a normal deck, then assign its preset below.
    destination_deck_id = int(target.decks.id(direction.destination_deck) or 0)
    destination_deck = target.decks.get(destination_deck_id)
    assert destination_deck
    destination_deck["conf"] = new_config["id"]
    target.decks.update(destination_deck)

    new_mid = clone_directional_notetype(
        target, source, 1076778696, direction, destination_deck_id
    )
    rows = source_rows(source, source_deck_id)

    requests: list[AddNoteRequest] = []
    source_nid_to_guid: dict[int, str] = {}
    source_metadata: dict[int, tuple[int, int, str, bytes]] = {}
    for row in rows:
        source_nid, source_guid, source_mid, note_mod, tags, flds, note_flags, note_data = row[:8]
        note = target.new_note(target.models.get(new_mid))
        note.guid = deterministic_guid(direction.key, source_guid, source_nid, occupied_guids)
        note.fields = map_fields(direction, source_mid, split_fields(flds))
        note.tags = tags.strip().split()
        source_nid_to_guid[source_nid] = note.guid
        source_metadata[source_nid] = (note_mod, note_flags, tags, note_data)
        requests.append(AddNoteRequest(note=note, deck_id=destination_deck_id))

    target.add_notes(requests)
    guid_to_nid = dict(target.db.all("select guid,id from notes where mid=?", new_mid))
    if len(guid_to_nid) != len(rows):
        raise AssertionError("not all transformed notes were added")
    source_nid_to_target_nid = {
        source_nid: int(guid_to_nid[guid]) for source_nid, guid in source_nid_to_guid.items()
    }
    target_nid_to_cid = dict(
        target.db.all(
            "select nid,id from cards where nid in (select id from notes where mid=?)", new_mid
        )
    )
    if len(target_nid_to_cid) != len(rows):
        raise AssertionError("not all transformed cards were generated")

    target.db.transact(lambda: target.db.executemany(
        "update notes set mod=?,usn=-1,flags=?,data=? where id=?",
        [
            (
                source_metadata[source_nid][0],
                source_metadata[source_nid][1],
                source_metadata[source_nid][3],
                target_nid,
            )
            for source_nid, target_nid in source_nid_to_target_nid.items()
        ],
    ))

    day_delta_seconds = int(source.crt) - int(target.crt)
    if day_delta_seconds % 86400:
        raise AssertionError("collection creation times are not whole days apart")
    day_shift = day_delta_seconds // 86400

    card_updates: list[tuple[Any, ...]] = []
    source_cid_to_target_cid: dict[int, int] = {}
    for row in rows:
        source_nid = row[0]
        (
            source_cid,
            card_mod,
            card_type,
            queue,
            due,
            interval,
            factor,
            reps,
            lapses,
            left,
            original_due,
            original_deck,
            card_flags,
            card_data,
        ) = row[8:]
        target_nid = source_nid_to_target_nid[source_nid]
        target_cid = int(target_nid_to_cid[target_nid])
        source_cid_to_target_cid[source_cid] = target_cid
        if card_type == 0:
            transformed_due = next_new_position
            next_new_position += 1
        else:
            transformed_due = due_for_target(card_type, queue, due, day_shift, 0)
        transformed_odue = original_due + day_shift if original_due else 0
        if original_deck:
            raise AssertionError("filtered-deck cards were not expected")
        card_updates.append(
            (
                destination_deck_id,
                card_mod,
                card_type,
                queue,
                transformed_due,
                interval,
                factor,
                reps,
                lapses,
                left,
                transformed_odue,
                0,
                card_flags,
                card_data,
                target_cid,
            )
        )

    target.db.transact(lambda: target.db.executemany(
        """
        update cards set did=?,mod=?,usn=-1,type=?,queue=?,due=?,ivl=?,factor=?,
                         reps=?,lapses=?,left=?,odue=?,odid=?,flags=?,data=?
        where id=?
        """,
        card_updates,
    ))

    details = {
        "deck_id": destination_deck_id,
        "deck_name": direction.destination_deck,
        "notetype_id": new_mid,
        "notetype_name": direction.note_type,
        "template_name": direction.template,
        "preset_id": int(new_config["id"]),
        "preset_name": direction.preset,
        "notes": len(rows),
        "cards": len(rows),
        "source_day_shift": day_shift,
        "scheduler_guard_present": direction.destination_deck in scheduler_script,
    }
    return details, source_cid_to_target_cid, next_new_position


def gather_source_revlogs(source: Collection, card_map: dict[int, int]) -> list[tuple[Any, ...]]:
    source_card_ids = set(card_map)
    return [row for row in source.db.all("select * from revlog order by id") if row[1] in source_card_ids]


def allocate_review_ids(
    target: Collection,
    directional_rows: list[tuple[str, list[tuple[Any, ...]], dict[int, int]]],
) -> tuple[list[tuple[Any, ...]], int]:
    used = set(target.db.list("select id from revlog"))
    desired_ids = {row[0] for _, rows, _ in directional_rows for row in rows}
    # Collision allocations must not consume an exact timestamp wanted by a
    # later row. A successor map finds the next unreserved millisecond with
    # path compression, avoiding repeated linear scans through dense history.
    successor = {value: value + 1 for value in used | desired_ids}

    def next_unreserved(value: int) -> int:
        path: list[int] = []
        while value in successor:
            path.append(value)
            value = successor[value]
        for blocked in path:
            successor[blocked] = value
        return value

    inserts: list[tuple[Any, ...]] = []
    maximum_drift = 0

    for _direction, rows, card_map in directional_rows:
        for row in rows:
            desired = row[0]
            if desired not in used:
                allocated = desired
            else:
                allocated = next_unreserved(desired + 1)
                successor[allocated] = next_unreserved(allocated + 1)
            used.add(allocated)
            maximum_drift = max(maximum_drift, abs(allocated - desired))
            values = list(row)
            values[0] = allocated
            values[1] = card_map[row[1]]
            values[2] = -1
            inserts.append(tuple(values))
    return inserts, maximum_drift


def verify_direction(target: Collection, details: dict[str, Any]) -> None:
    deck_id = details["deck_id"]
    notetype_id = details["notetype_id"]
    note_count = target.db.scalar("select count(*) from notes where mid=?", notetype_id)
    card_count = target.db.scalar("select count(*) from cards where did=?", deck_id)
    if note_count != details["notes"] or card_count != details["cards"]:
        raise AssertionError(f"count mismatch for {details['deck_name']}")
    model = target.models.get(notetype_id)
    assert model
    if [field["name"] for field in model["flds"]] != ["Korean", "English", "Hanja", "Number"]:
        raise AssertionError("directional field layout is incorrect")
    if len(model["tmpls"]) != 1 or model["tmpls"][0]["name"] != details["template_name"]:
        raise AssertionError("directional template layout is incorrect")
    template = model["tmpls"][0]
    if template.get("did"):
        raise AssertionError("template retained a fixed target deck")
    if "Audio" in template["qfmt"] + template["afmt"]:
        raise AssertionError("template retained Audio")
    deck = target.decks.get(deck_id)
    assert deck
    if int(deck["conf"]) != details["preset_id"]:
        raise AssertionError("deck is not assigned to its directional preset")


def package_db_summary(package: Path, verification_dir: Path) -> dict[str, Any]:
    collection_path, media_dir = unpack_modern_package(package, verification_dir, include_media=True)
    with open_sqlite(collection_path) as db:
        summary = {
            "sqlite_integrity": db.execute("pragma integrity_check").fetchone()[0],
            "notes": db.execute("select count(*) from notes").fetchone()[0],
            "cards": db.execute("select count(*) from cards").fetchone()[0],
            "revlog": db.execute("select count(*) from revlog").fetchone()[0],
            "decks": [row[0] for row in db.execute("select name from decks")],
        }
    summary["media_files"], summary["media_digest"] = media_digest(media_dir)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ktoe", type=Path, required=True)
    parser.add_argument("--etok", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--scheduler", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packages = {"ktoe": args.ktoe, "etok": args.etok, "target": args.target}
    for key, package in packages.items():
        actual = sha256_file(package)
        if actual != EXPECTED_INPUT_HASHES[key]:
            raise ValueError(f"unexpected SHA-256 for {key}: {actual}")
    if args.work_dir.exists() or args.output_dir.exists():
        raise FileExistsError("work-dir and output-dir must both be new paths")
    args.work_dir.mkdir(parents=True)
    args.output_dir.mkdir(parents=True)

    source_paths: dict[str, Path] = {}
    for direction in DIRECTIONS:
        source_paths[direction.key], _ = unpack_modern_package(
            packages[direction.key], args.work_dir / direction.key, include_media=False
        )
    target_path, target_media = unpack_modern_package(
        packages["target"], args.work_dir / "integrated", include_media=True
    )

    original_media = media_digest(target_media)
    original_keys, original_digests = snapshot_original_rows(target_path)
    scheduler_script = args.scheduler.read_text(encoding="utf8")
    for direction in DIRECTIONS:
        if direction.destination_deck not in scheduler_script:
            raise AssertionError(f"scheduler does not guard {direction.destination_deck}")
    if "zEK5000" in scheduler_script or "Kor to Eng 5000" in scheduler_script:
        raise AssertionError("scheduler still includes pre-integration deck names")

    sources = {key: Collection(str(path)) for key, path in source_paths.items()}
    target = Collection(str(target_path))
    details: list[dict[str, Any]] = []
    card_maps: dict[str, dict[int, int]] = {}
    try:
        occupied_guids = set(target.db.list("select guid from notes"))
        original_target_notes = target.db.scalar("select count(*) from notes")
        original_target_cards = target.db.scalar("select count(*) from cards")
        original_target_revlogs = target.db.scalar("select count(*) from revlog")
        next_new_position = max(
            int(target.get_config("nextPos", 1)),
            int(target.db.scalar("select coalesce(max(due),0)+1 from cards where type=0")),
        )

        for direction in DIRECTIONS:
            result, card_map, next_new_position = add_direction(
                target,
                sources[direction.key],
                direction,
                scheduler_script,
                occupied_guids,
                next_new_position,
            )
            details.append(result)
            card_maps[direction.key] = card_map

        directional_revlogs = [
            (direction.key, gather_source_revlogs(sources[direction.key], card_maps[direction.key]), card_maps[direction.key])
            for direction in DIRECTIONS
        ]
        review_inserts, maximum_review_id_drift_ms = allocate_review_ids(target, directional_revlogs)
        target.db.transact(lambda: target.db.executemany(
            "insert into revlog (id,cid,usn,ease,ivl,lastIvl,factor,time,type) values (?,?,?,?,?,?,?,?,?)",
            review_inserts,
        ))

        target.set_config("nextPos", next_new_position)
        target.set_config("cardStateCustomizer", scheduler_script)
        target.set_config("collapseTime", 4800)
        target.set_config("newCardsIgnoreReviewLimit", True)
        target.set_config("applyAllParentLimits", False)
        target.set_config("fsrs", False)

        for result in details:
            verify_direction(target, result)
        if target.db.scalar("select count(*) from notes") != original_target_notes + 5179 + 4884:
            raise AssertionError("integrated note total is incorrect")
        if target.db.scalar("select count(*) from cards") != original_target_cards + 5179 + 4884:
            raise AssertionError("integrated card total is incorrect")
        if target.db.scalar("select count(*) from revlog") != original_target_revlogs + len(review_inserts):
            raise AssertionError("integrated review-history total is incorrect")

        # Release the backend's exclusive DB lock before independent SQLite reads.
        target.close()
        verify_original_rows(target_path, original_keys, original_digests)
        if media_digest(target_media) != original_media:
            raise AssertionError("target media changed during integration")
        target = Collection(str(target_path))

        output_packages: dict[str, Path] = {}
        for result in details:
            package = args.output_dir / f"{result['deck_name']}_transformed-with-scheduling.apkg"
            target.export_anki_package(
                out_path=str(package),
                options=ExportAnkiPackageOptions(
                    with_scheduling=True,
                    with_deck_configs=True,
                    with_media=False,
                    legacy=False,
                ),
                limit=DeckIdLimit(deck_id=result["deck_id"]),
            )
            output_packages[result["deck_name"]] = package

        integrated_package = args.output_dir / "drew3452_integrated-Korean-test-collection-with-media.colpkg"
        target.export_collection_package(str(integrated_package), include_media=True, legacy=False)

        verification: dict[str, Any] = {}
        for name, package in output_packages.items():
            verification[name] = package_db_summary(
                package, args.work_dir / f"verify-{name}"
            )
        verification["integrated_collection"] = package_db_summary(
            integrated_package, args.work_dir / "verify-integrated"
        )

        integrated_media = (
            verification["integrated_collection"]["media_files"],
            verification["integrated_collection"]["media_digest"],
        )
        if integrated_media != original_media:
            raise AssertionError("integrated package did not preserve target media")

        report = {
            "status": "verified-test-artifacts-only",
            "inputs": {
                key: {"path": str(path), "sha256": sha256_file(path)}
                for key, path in packages.items()
            },
            "directions": details,
            "linked_review_rows_added": len(review_inserts),
            "maximum_review_timestamp_adjustment_ms": maximum_review_id_drift_ms,
            "original_target_rows_unchanged": True,
            "original_target_media": {
                "files": original_media[0],
                "digest": original_media[1],
            },
            "global_settings": {
                "learn_ahead_seconds": 4800,
                "fsrs": False,
                "new_cards_ignore_review_limit": True,
                "apply_all_parent_limits": False,
                "custom_scheduler_guarded_decks": [d.destination_deck for d in DIRECTIONS],
            },
            "outputs": {
                path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in [*output_packages.values(), integrated_package]
            },
            "package_verification": verification,
        }
        (args.output_dir / "verification-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
    finally:
        for source in sources.values():
            source.close()
        if target.db:
            target.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
