"""Manual, transactional imports. Never called by a web endpoint."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import time
from pathlib import Path

import ijson

from trainer.db import connect, initialize
from trainer.grading import deterministic
from trainer.tokenizer import tokenize


def verified_file(base: Path, entry: dict) -> Path:
    path = (base / entry["file"]).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("Import file must be inside manifest directory")
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    if sha.hexdigest() != entry["sha256"]:
        raise ValueError("Checksum mismatch")
    if not entry.get("attribution") or not entry.get("license") or not entry.get("url"):
        raise ValueError("Each source needs attribution, license and URL")
    return path


def open_data(path):
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def import_source(db, entry, path):
    kind = entry["kind"]
    count = 0
    with open_data(path) as stream:
        if kind in {"jmdict", "kanjidic"}:
            prefix = "words.item" if kind == "jmdict" else "characters.item"
            for item in ijson.items(stream, prefix, use_float=True):
                identifier = str(item["id"] if kind == "jmdict" else item["literal"])
                table = "vocabulary" if kind == "jmdict" else "kanji"
                db.execute(f"INSERT INTO {table} VALUES (?,?) ON CONFLICT DO UPDATE SET data=excluded.data",
                           (identifier, json.dumps(item, ensure_ascii=False)))
                count += 1
        elif kind == "tanos":
            # A reviewed TSV transcription keeps PDF extraction errors out of grading rules.
            for row in csv.DictReader((line.decode("utf-8") for line in stream), delimiter="\t"):
                if row["type"] == "vocab":
                    for token in tokenize(row["term"]):
                        for term in {token["lemma"], token["normalized"], token["surface"]}:
                            db.execute("INSERT INTO n5_vocab VALUES (?,?) ON CONFLICT DO UPDATE SET "
                                       "source=excluded.source", (term, entry["name"]))
                elif row["type"] == "kanji":
                    if not re.fullmatch(r"[\u3400-\u9fff]", row["term"]):
                        raise ValueError("Invalid kanji entry")
                    db.execute("INSERT INTO n5_kanji VALUES (?,?) ON CONFLICT DO UPDATE SET source=excluded.source",
                               (row["term"], entry["name"]))
                elif row["type"] == "grammar":
                    if not db.execute("SELECT 1 FROM grammar WHERE id=?", (row["grammar_id"],)).fetchone():
                        raise ValueError("Map Tanos grammar to a reviewed seed grammar ID")
                else:
                    raise ValueError("Unknown Tanos row type")
                count += 1
        elif kind == "tatoeba":
            # Curated pairs: retain sentence authors and a reviewed grammar mapping per row.
            vocab = {r[0] for r in db.execute("SELECT term FROM n5_vocab")}
            kanji = {r[0] for r in db.execute("SELECT literal FROM n5_kanji")}
            for row in csv.DictReader((line.decode("utf-8") for line in stream), delimiter="\t"):
                g = db.execute("SELECT pattern FROM grammar WHERE id=?", (row["grammar_id"],)).fetchone()
                if not g or row["language"] not in {"it", "en"}:
                    raise ValueError("Invalid grammar mapping or language")
                if not row["ja_author"] or not row["source_author"]:
                    raise ValueError("Tatoeba authors must be preserved")
                if len(row["ja"]) > 60 or len(row["text"]) > 300:
                    continue
                checks = deterministic(row["ja"], [row["ja"]], vocab, kanji, g[0])
                if checks["findings"]:
                    continue
                sid = "tatoeba-" + row["ja_id"] + "-" + row["grammar_id"]
                existing = db.execute("SELECT attribution FROM sentences WHERE id=?", (sid,)).fetchone()
                attribution = json.loads(existing[0]) if existing else {
                    "source": "Tatoeba", "ja_id": row["ja_id"], "ja_author": row["ja_author"],
                    "translations": {}, "license": entry["license"],
                    "url": "https://tatoeba.org/en/sentences/show/" + row["ja_id"]}
                attribution["translations"][row["language"]] = {
                    "id": row["source_id"], "author": row["source_author"]}
                db.execute("INSERT INTO sentences VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                           "refs=excluded.refs", (
                    sid, row["grammar_id"], None, None, json.dumps([row["ja"]]), json.dumps(attribution)))
                db.execute("UPDATE sentences SET attribution=? WHERE id=?", (json.dumps(attribution), sid))
                column = "prompt_it" if row["language"] == "it" else "prompt_en"
                db.execute(f"UPDATE sentences SET {column}=? WHERE id=?", (row["text"], sid))
                count += 1
        else:
            raise ValueError("Unknown source kind")
    if count == 0:
        raise ValueError("Source yielded no importable entries")
    return count


def update(manifest: Path):
    initialize()
    entries = json.loads(manifest.read_text())["sources"]
    files = [(entry, verified_file(manifest.parent, entry)) for entry in entries]
    with connect() as db:
        for entry, path in files:
            count = import_source(db, entry, path)
            metadata = {**entry, "entries": count}
            db.execute("INSERT INTO sources VALUES (?,?,?) ON CONFLICT(name) DO UPDATE SET "
                       "data=excluded.data, imported_at=excluded.imported_at",
                       (entry["name"], json.dumps(metadata), time.time()))
            print(f"{entry['name']}: {count} entries")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    update(parser.parse_args().manifest)


if __name__ == "__main__":
    main()
