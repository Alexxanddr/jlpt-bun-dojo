"""Rebuild attributed N5 subsets from downloaded snapshots; no runtime network."""
import csv
import gzip
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

# Run from repository root, passing jmdict.zip kanjidic.zip tanos.csv tatoeba-books.json.
root = Path("trainer/data")
seed = json.loads((root / "seed.json").read_text())
terms = set(seed["vocabulary"])
rows = []
with Path(sys.argv[3]).open() as stream:
    for row in csv.DictReader(stream):
        for spelling in (row["expression"], row["reading"]):
            for term in re.split(r";\s*", spelling):
                term = term.strip()
                if term:
                    terms.add(term)
                    rows.append({"type": "vocab", "term": term, "grammar_id": ""})
with (root / "tanos-n5.tsv").open("w") as stream:
    writer = csv.DictWriter(stream, fieldnames=["type", "term", "grammar_id"], delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
for kind, archive, key in (("jmdict", sys.argv[1], "words"), ("kanjidic", sys.argv[2], "characters")):
    with zipfile.ZipFile(archive) as z:
        data = json.loads(z.read(z.namelist()[0]))
    if kind == "jmdict":
        data[key] = [w for w in data[key] if any(x["text"] in terms for x in w["kanji"] + w["kana"])]
    else:
        data[key] = [w for w in data[key] if w["literal"] in seed["kanji"]]
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    (root / f"{kind}-subset.json.gz").write_bytes(gzip.compress(payload, mtime=0))
    print(kind, len(data[key]))
selected = {219639: ("i-adjective", {"eng": 56960, "ita": 373938}),
            233021: ("possession", {"eng": 515538, "ita": 499809})}
with (root / "tatoeba.tsv").open("w") as stream:
    writer = csv.DictWriter(stream, fieldnames=["ja_id", "ja", "ja_author", "source_id", "language", "text",
                                               "source_author", "grammar_id"], delimiter="\t")
    writer.writeheader()
    for row in json.loads(Path(sys.argv[4]).read_text())["data"]:
        if row["id"] not in selected:
            continue
        grammar, ids = selected[row["id"]]
        for translation in row["translations"]:
            if translation["id"] != ids.get(translation["lang"]):
                continue
            assert translation["is_direct"] and row["owner"] and translation["owner"]
            writer.writerow({"ja_id": row["id"], "ja": row["text"], "ja_author": row["owner"],
                             "source_id": translation["id"], "language": {"eng": "en", "ita": "it"}[translation["lang"]],
                             "text": translation["text"], "source_author": translation["owner"], "grammar_id": grammar})
base = "https://github.com/scriptin/jmdict-simplified/releases/tag/3.6.2%2B20261019180022"
entries = [
    ("jmdict-subset-20261019", "jmdict", "jmdict-subset.json.gz", "CC-BY-SA-4.0", base,
     "James William Breen and EDRDG; scriptin JSON conversion; subset selected by N5 trainer"),
    ("kanjidic-subset-20261019", "kanjidic", "kanjidic-subset.json.gz", "CC-BY-SA-4.0", base,
     "James William Breen and EDRDG; scriptin JSON conversion; subset selected by N5 trainer"),
    ("tanos-vocabulary-mirror-20261021", "tanos", "tanos-n5.tsv", "CC-BY (upstream version unspecified); MIT mirror",
     "https://github.com/elzup/jlpt-word-list/blob/master/src/n5.csv",
     "Jonathan Waller / Tanos; chyyran/jlpt-anki-decks; Jamie Sinclair; elzup; spelling/reading subset"),
    ("tatoeba-curated-20261021", "tatoeba", "tatoeba.tsv", "CC-BY-2.0-FR",
     "https://tatoeba.org/en/downloads", "Tatoeba: mookeee, bunbuku, CK, Pharamp; per-row IDs/authors retained"),
]
sources = []
for name, kind, file, license, url, attribution in entries:
    sources.append(dict(name=name, kind=kind, file=file, sha256=hashlib.sha256((root / file).read_bytes()).hexdigest(),
                        license=license, url=url, attribution=attribution))
(root / "manifest.json").write_text(json.dumps({"sources": sources}, ensure_ascii=False, indent=2) + "\n")
