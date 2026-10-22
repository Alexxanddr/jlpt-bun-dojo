import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).parent


@contextmanager
def connect():
    path = Path(os.getenv("DATABASE_PATH", "var/trainer.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY)")
        for file in sorted((ROOT / "migrations").glob("*.sql")):
            if not db.execute("SELECT 1 FROM migrations WHERE name=?", (file.name,)).fetchone():
                # executescript commits implicitly; include the migration record in its transaction.
                db.executescript("BEGIN IMMEDIATE;\n" + file.read_text() +
                                 "\nINSERT INTO migrations VALUES ('" + file.name + "');\nCOMMIT;")
        seed(db)


def seed(db):
    data = json.loads((ROOT / "data/seed.json").read_text())
    for g in data["grammar"]:
        db.execute("INSERT OR IGNORE INTO grammar VALUES (?,?,?,?,?,?,?)", tuple(g.values()))
    for s in data["sentences"]:
        db.execute("INSERT OR IGNORE INTO sentences VALUES (?,?,?,?,?,?)",
                   (s["id"], s["grammar_id"], s["it"], s["en"], json.dumps(s["refs"]), "Original / MIT"))
    db.executemany("INSERT OR IGNORE INTO n5_vocab VALUES (?, 'original starter list')",
                   [(s,) for s in data["vocabulary"]])
    db.executemany("INSERT OR IGNORE INTO n5_kanji VALUES (?, 'original starter list')",
                   [(s,) for s in data["kanji"]])

    from trainer.import_data import import_source, verified_file
    manifest = ROOT / "data/manifest.json"
    for entry in json.loads(manifest.read_text())["sources"]:
        if db.execute("SELECT 1 FROM sources WHERE name=?", (entry["name"],)).fetchone():
            continue
        path = verified_file(manifest.parent, entry)
        count = import_source(db, entry, path)
        db.execute("INSERT INTO sources VALUES (?,?,?)", (
            entry["name"], json.dumps({**entry, "entries": count}), time.time()))
