import hashlib
import json

import pytest

from trainer.db import connect
from trainer.import_data import update


def test_verified_idempotent_import(client, tmp_path):
    source = tmp_path / "kanji.json"
    source.write_text(json.dumps({"characters": [{"literal": "日", "misc": {"jlptLevel": 4}}]}))
    entry = {"name": "test-kanjidic", "kind": "kanjidic", "file": source.name,
             "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "attribution": "dummy fixture", "license": "CC-BY-SA-4.0", "url": "https://example.org"}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"sources": [entry]}))
    update(manifest)
    update(manifest)
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM kanji WHERE literal='日'").fetchone()[0] == 1
    entry["sha256"] = "0" * 64
    manifest.write_text(json.dumps({"sources": [entry]}))
    with pytest.raises(ValueError, match="Checksum"):
        update(manifest)
