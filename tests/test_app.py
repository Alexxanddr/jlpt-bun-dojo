import pytest
from fastapi.testclient import TestClient

from tests.test_ai import evaluation
from trainer import app as module
from trainer.ai import AIClient, AIError
from trainer.db import connect
from trainer.models import Generated


def test_auth_origin_headers(client):
    assert client.get("/api/history").status_code == 401
    assert client.post("/api/login", json={"password": "x"}).status_code == 403
    assert client.post("/api/login", json={"password": "x"}, headers={
        "x-trainer-request": "1", "origin": "https://evil.example"}).status_code == 403
    assert client.get("/").headers["content-security-policy"].startswith("default-src 'self'")


def test_passwordless_instance_skips_authentication_but_keeps_mutation_header(passwordless):
    settings = passwordless.get("/api/settings")
    assert settings.status_code == 200
    assert settings.json()["authentication_enabled"] is False
    assert passwordless.get("/api/history").status_code == 200
    assert passwordless.post("/api/exercises", json={}).status_code == 403
    assert passwordless.post("/api/exercises", json={}, headers={"x-trainer-request": "1"}).status_code == 200


def test_configured_password_still_requires_sixteen_characters(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "trainer.db"))
    monkeypatch.setenv("APP_PASSWORD", "too-short")
    with pytest.raises(RuntimeError, match="at least 16 characters"), TestClient(module.app):
        pass


def test_demo_keeps_practice_but_blocks_shared_data_and_configuration(passwordless, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    headers = {"x-trainer-request": "1"}
    assert passwordless.get("/api/settings").json()["demo_mode"] is True
    assert passwordless.post("/api/exercises", json={}, headers=headers).status_code == 200
    for path in ("history", "journal", "stats"):
        assert passwordless.get(f"/api/{path}").status_code == 403
    assert passwordless.put("/api/settings", json={}, headers=headers).status_code == 403
    assert passwordless.post("/api/mcp/sync", json={}, headers=headers).status_code == 403


def test_attempt_review_cram_journal(authenticated, monkeypatch):
    async def evaluate(*args, **kwargs):
        result = evaluation()
        result.suggestions = ["Prova anche senza il pronome."]
        return result
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    c = authenticated
    exercise = c.post("/api/exercises", json={"language": "it", "category": "basics"}).json()
    assert "references" not in exercise and "refs" not in exercise
    answer = {"exercise_id": exercise["id"], "answer": "私は学生です。"}
    result = c.post("/api/answers", json=answer)
    assert result.status_code == 200, result.text
    assert result.json()["accepted"]
    assert c.post("/api/answers", json=answer).json() == result.json()
    assert len(c.get("/api/history").json()) == 1
    assert len(c.get("/api/journal").json()) == 1
    assert c.get("/api/stats").json()["attempts"] == 1
    assert c.post("/api/exercises", json={"mode": "review"}).status_code == 404
    with connect() as db:
        before = dict(db.execute("SELECT * FROM reviews").fetchone())
    cram = c.post("/api/exercises", json={"mode": "cram"}).json()
    assert c.post("/api/answers", json={"exercise_id": cram["id"], "answer": "学生です。"}).status_code == 200
    with connect() as db:
        assert before == dict(db.execute("SELECT * FROM reviews").fetchone())


def test_failure_does_not_persist_attempt(authenticated, monkeypatch):
    async def fail(*args, **kwargs):
        raise AIError("provider_failed")
    monkeypatch.setattr(AIClient, "evaluate", fail)
    e = authenticated.post("/api/exercises", json={}).json()
    r = authenticated.post("/api/answers", json={"exercise_id": e["id"], "answer": "本です。"})
    assert r.status_code == 502
    assert authenticated.get("/api/history").json() == []


def test_generation_and_hint(authenticated, monkeypatch):
    async def generate(*args, **kwargs):
        assert "学" in kwargs["allowed_kanji"]
        assert "学生" in kwargs["allowed_vocabulary"]
        return Generated(prompt="Sono uno studente.", references=["私は学生です。"])
    async def evaluate(*args, **kwargs):
        return evaluation()
    monkeypatch.setattr(AIClient, "generate", generate)
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    r = authenticated.post("/api/exercises", json={"generate": True, "category": "basics"})
    assert r.status_code == 200, r.text
    e = r.json()
    assert authenticated.get(f"/api/exercises/{e['id']}/hint").status_code == 200
    result = authenticated.post("/api/answers", json={"exercise_id": e["id"], "answer": "学生です。",
                                                     "hinted": True}).json()
    assert result["quality"] <= 2


def test_settings_no_keys(authenticated, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-that-must-not-leak")
    r = authenticated.get("/api/settings")
    assert "secret-that-must-not-leak" not in r.text
    data = r.json()["settings"]
    assert "openai_api_key" not in data and "openrouter_api_key" not in data
    data["api_key"] = "should-not-be-accepted"
    assert authenticated.put("/api/settings", json=data).status_code == 422


def test_llm_settings_and_secrets_are_saved_without_being_returned(authenticated):
    data = authenticated.get("/api/settings").json()["settings"]
    data.update({"openai_base_url": "http://model-server:8080/v1", "openai_api_key": "new-secret",
                 "generation_temperature": 0.7, "generation_max_tokens": 512})
    assert authenticated.put("/api/settings", json=data).status_code == 200
    response = authenticated.get("/api/settings")
    assert "new-secret" not in response.text
    assert response.json()["settings"]["openai_base_url"] == "http://model-server:8080/v1"
    from trainer.app import load_settings
    saved = load_settings()
    assert saved.openai_api_key == "new-secret" and saved.generation_temperature == 0.7


def test_oversized_and_rate_limit(authenticated):
    assert authenticated.post("/api/exercises", content="x" * 9000).status_code == 413
    from trainer.app import requests_window
    requests_window.clear()
    for _ in range(20):
        assert authenticated.post("/api/exercises", json={}).status_code == 200
    assert authenticated.post("/api/exercises", json={}).status_code == 429


def test_hint_cannot_be_hidden_by_client(authenticated, monkeypatch):
    async def evaluate(*args, **kwargs):
        return evaluation()
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    e = authenticated.post("/api/exercises", json={}).json()
    authenticated.get(f"/api/exercises/{e['id']}/hint")
    result = authenticated.post("/api/answers", json={"exercise_id": e["id"], "answer": "学生です。",
                                                     "hinted": False}).json()
    assert result["quality"] <= 2
    assert authenticated.get("/api/stats").json()["axes"]["independence"] == 0


def test_all_generated_variants_are_filtered(authenticated, monkeypatch):
    async def generate(*args, **kwargs):
        return Generated(prompt="Sono uno studente.", references=["学生です。", "薔薇です。"])
    monkeypatch.setattr(AIClient, "generate", generate)
    r = authenticated.post("/api/exercises", json={"generate": True})
    assert r.status_code == 422
    assert r.json()["detail"] == "generated_outside_dataset"


def test_certain_error_overrides_ai_acceptance(authenticated, monkeypatch):
    async def evaluate(*args, **kwargs):
        return evaluation()
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    e = authenticated.post("/api/exercises", json={}).json()
    r = authenticated.post("/api/answers", json={"exercise_id": e["id"], "answer": "本をを読みます。"}).json()
    assert r["accepted"] is False and r["quality"] <= 2
    assert any(f["code"] == "duplicate_particle" for f in r["checks"]["findings"])


def test_generation_does_not_replace_due_review(authenticated):
    r = authenticated.post("/api/exercises", json={"generate": True, "mode": "review"})
    assert r.status_code == 422


def test_targeted_filters_weaknesses_before_generation(authenticated, monkeypatch):
    from trainer import app as module
    allowed = {"source": "wanikani", "evidence": {"subject_type": "vocabulary", "characters": "学生"}}
    excluded = {"source": "wanikani", "evidence": {"subject_type": "vocabulary", "characters": "王子"}}
    monkeypatch.setattr(module, "weakness_cache", {"items": [excluded, allowed], "unavailable": []})
    config = authenticated.get("/api/settings").json()["settings"]
    config["mcp_enabled"] = True
    authenticated.put("/api/settings", json=config)

    async def generate(self, language, grammar, context, **kwargs):
        assert context == [{"source": "wanikani", "target": "学生", "kind": "vocabulary",
                            "meanings": [], "accuracy": None}]
        return Generated(prompt="Sono uno studente.", references=["学生です。"])
    monkeypatch.setattr(AIClient, "generate", generate)
    r = authenticated.post("/api/exercises", json={"mode": "targeted"})
    assert r.status_code == 200 and r.json()["weaknesses"][0]["target"] == "学生"


def test_targeted_without_n5_does_not_call_ai(authenticated, monkeypatch):
    from trainer import app as module
    monkeypatch.setattr(module, "weakness_cache", {"items": [{"source": "wanikani", "evidence": {
        "subject_type": "vocabulary", "characters": "王子"}}], "unavailable": []})
    config = authenticated.get("/api/settings").json()["settings"]
    config["mcp_enabled"] = True
    authenticated.put("/api/settings", json=config)

    async def generate(*args, **kwargs):
        raise AssertionError("Out-of-scope weaknesses must not reach AI")
    monkeypatch.setattr(AIClient, "generate", generate)
    r = authenticated.post("/api/exercises", json={"mode": "targeted"})
    assert r.status_code == 409 and r.json()["detail"] == "no_n5_weaknesses"


def test_wrong_language_is_not_saved(authenticated, monkeypatch):
    async def structured(*args, **kwargs):
        return Generated(prompt="I like cats.", references=["猫が好きです。"])
    monkeypatch.setattr(AIClient, "structured", structured)
    with connect() as db:
        before = db.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
    r = authenticated.post("/api/exercises", json={"language": "it", "generate": True})
    assert r.status_code == 502 and r.json()["detail"] == "generated_wrong_language"
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sentences").fetchone()[0] == before
        assert db.execute("SELECT COUNT(*) FROM exercises").fetchone()[0] == 0


def test_review_translation_preserves_sentence_and_schedule(authenticated, monkeypatch):
    import json

    with connect() as db:
        db.execute("INSERT INTO sentences VALUES (?,?,?,?,?,?)", (
            "generated-translation-case", db.execute("SELECT id FROM grammar LIMIT 1").fetchone()[0], None, "I am a student.",
            json.dumps(["学生です。"]), "AI-generated; unreviewed"))
        db.execute("INSERT INTO reviews VALUES (?, 1, 1, 2.5, 0)", ("generated-translation-case",))

    async def generate(*args, **kwargs):
        assert kwargs["reference"] == ["学生です。"]
        return Generated(prompt="Sono uno studente.", references=["学生です。"])

    async def evaluate(*args, **kwargs):
        return evaluation()

    monkeypatch.setattr(AIClient, "generate", generate)
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    response = authenticated.post("/api/exercises", json={"mode": "review", "language": "it"})
    assert response.status_code == 200
    exercise = response.json()
    with connect() as db:
        assert db.execute("SELECT sentence_id FROM exercises WHERE id=?", (exercise["id"],)).fetchone()[0] == "generated-translation-case"
    assert authenticated.post("/api/answers", json={"exercise_id": exercise["id"], "answer": "学生です。"}).status_code == 200
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 1
        assert db.execute("SELECT repetitions FROM reviews").fetchone()[0] == 2


def test_hint_during_evaluation_is_counted(authenticated, monkeypatch):
    exercise = authenticated.post("/api/exercises", json={}).json()

    async def evaluate(*args, **kwargs):
        await module.hint(exercise["id"])
        return evaluation()

    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    result = authenticated.post("/api/answers", json={"exercise_id": exercise["id"], "answer": "学生です。"})
    assert result.status_code == 200
    assert result.json()["quality"] <= 2
    assert authenticated.get("/api/stats").json()["axes"]["independence"] == 0


def test_due_review_journal_resolution_and_saved_key_retention(authenticated, monkeypatch):
    async def evaluate(*args, **kwargs):
        result = evaluation()
        result.suggestions = ["Ripassa questa costruzione."]
        return result
    monkeypatch.setattr(AIClient, "evaluate", evaluate)
    config = authenticated.get("/api/settings").json()["settings"]
    config["openai_api_key"] = "private-test-key"
    assert authenticated.put("/api/settings", json=config).status_code == 200
    config["openai_api_key"] = ""
    assert authenticated.put("/api/settings", json=config).status_code == 200
    assert module.load_settings().openai_api_key == "private-test-key"
    assert "private-test-key" not in authenticated.get("/api/settings").text
    exercise = authenticated.post("/api/exercises", json={}).json()
    assert authenticated.post("/api/answers", json={"exercise_id": exercise["id"], "answer": "学生です。"}).status_code == 200
    grammar_id = authenticated.get("/api/journal").json()[0]["grammar_id"]
    assert authenticated.post(f"/api/journal/{grammar_id}/resolve", json={}).status_code == 200
    assert authenticated.get("/api/journal").json()[0]["resolved"] == 1
    with connect() as db:
        db.execute("UPDATE reviews SET due=0")
    assert authenticated.get("/api/stats").json()["due"] == 1
    review = authenticated.post("/api/exercises", json={"mode": "review"}).json()
    assert authenticated.post("/api/answers", json={"exercise_id": review["id"], "answer": "学生です。"}).status_code == 200
    stats = authenticated.get("/api/stats").json()
    assert stats["due"] == 0 and stats["axes"]["recall"] == 100
    assert authenticated.get("/api/journal").json()[0]["resolved"] == 0
    assert authenticated.post("/api/logout", json={}).status_code == 200
    assert authenticated.get("/api/history").status_code == 401


def test_partial_mcp_sync_keeps_successful_source_usable(authenticated, monkeypatch):
    config = authenticated.get("/api/settings").json()["settings"]
    config["mcp_enabled"] = True
    authenticated.put("/api/settings", json=config)
    item = {"source": "wanikani", "evidence": {"subject_type": "vocabulary", "characters": "学生"}}
    monkeypatch.setattr(module, "weakness_cache", {"items": [], "unavailable": []})
    async def sync():
        return {"items": [item], "unavailable": ["bunpro"]}
    async def generate(*args, **kwargs):
        return Generated(prompt="Sono uno studente.", references=["学生です。"])
    monkeypatch.setattr(module, "all_weaknesses", sync)
    monkeypatch.setattr(AIClient, "generate", generate)
    response = authenticated.post("/api/mcp/sync", json={})
    assert response.json() == {"items": [item], "unavailable": ["bunpro"]}
    assert authenticated.post("/api/exercises", json={"mode": "targeted"}).status_code == 200
