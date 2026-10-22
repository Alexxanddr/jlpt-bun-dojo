import json

from trainer.db import connect, initialize
from trainer.grading import deterministic, sm2
from trainer.tokenizer import normalize, tokenize


def test_real_tokenizer():
    assert normalize(" ＡＢＣ１２３ ") == "ABC123"
    assert any(t["lemma"] == "読む" for t in tokenize("昨日、本を読みました。"))


def test_variants_and_scope():
    result = deterministic("私は学校へ行きます。", ["学校に行きます。"], {"私", "学校", "行く"},
                           set("私学校行"), "N に V")
    assert not result["findings"]
    assert result["lemma_similarity"] > 0.5
    scope = deterministic("薔薇を見ます。", ["花を見ます。"], {"見る"}, {"見"}, "N を V")
    assert scope["findings"] and all(f["severity"] == "scope" for f in scope["findings"])
    repeated = deterministic("本をを読みます。", ["本を読みます。"], {"本", "読む"}, set("本読"), "N を V")
    assert any(f["code"] == "duplicate_particle" for f in repeated["findings"])


def test_sm2():
    first = sm2(5)
    assert first["interval_days"] == 1 and first["repetitions"] == 1
    second = sm2(5, **first)
    assert second["interval_days"] == 6
    third = sm2(5, **second)
    assert third["interval_days"] > 6
    failed = sm2(1, **third)
    assert failed["repetitions"] == 0 and failed["interval_days"] == 1
    assert sm2(0, ease=1.3)["ease"] == 1.3


def test_seed_idempotent(client):
    initialize()
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM grammar").fetchone()[0] == 24
        assert db.execute("SELECT COUNT(*) FROM sentences").fetchone()[0] == 26


def test_i18n_parity():
    from trainer.db import ROOT
    it = json.loads((ROOT / "static/locales/it.json").read_text())
    en = json.loads((ROOT / "static/locales/en.json").read_text())
    assert it.keys() == en.keys()


def test_bundled_sources_and_attribution(client):
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 4
        assert db.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0] == 1094
        assert db.execute("SELECT COUNT(*) FROM kanji").fetchone()[0] == 115
        row = db.execute("SELECT attribution FROM sentences WHERE id='tatoeba-219639-i-adjective'").fetchone()
        attribution = json.loads(row[0])
        assert attribution["translations"]["it"]["author"] == "Pharamp"
        assert attribution["translations"]["en"]["author"] == "CK"


def test_n5_word_with_advanced_kanji_is_rendered_in_kana():
    from trainer.grading import render_n5_reference
    vocab = {"日本", "語", "勉強", "する", "為る"}
    kanji = set("日本語")
    ref = render_n5_reference("日本語を勉強しました。", vocab, kanji)
    assert ref == "日本語をべんきょうしました。"
    assert not deterministic(ref, [ref], vocab | {"べんきょう"}, kanji, "Vました")["findings"]


def test_kana_rendering_does_not_hide_unknown_vocabulary():
    from trainer.grading import render_n5_reference
    ref = render_n5_reference("薔薇を見ます。", {"見る"}, {"見"})
    assert ref == "薔薇を見ます。"
    assert deterministic(ref, [ref], {"見る"}, {"見"}, "N を V")["findings"]


def test_loanword_reading_keeps_katakana():
    from trainer.grading import render_n5_reference
    assert render_n5_reference("珈琲を飲みます。", {"コーヒー", "珈琲", "飲む"}, {"飲"}) == "コーヒーを飲みます。"
