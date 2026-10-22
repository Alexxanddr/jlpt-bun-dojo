import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

from trainer.mcp_client import StdioMCPClient, extract_weaknesses


def test_adapter_with_mock(monkeypatch):
    monkeypatch.setenv("BUNPRO_MCP_COMMAND", "/dummy/node")
    monkeypatch.setenv("BUNPRO_MCP_ARGS", '["/dummy/server.js"]')
    monkeypatch.setenv("BUNPRO_API_TOKEN", "dummy-token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "must-not-leak")
    calls = []

    @asynccontextmanager
    async def transport(params, **kwargs):
        assert "OPENROUTER_API_KEY" not in params.env
        yield ("in", "out")

    class Session:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def initialize(self): pass
        async def call_tool(self, name, args):
            calls.append((name, args))
            return SimpleNamespace(isError=False, content=[SimpleNamespace(type="text", text=json.dumps({
                "grammar": [{"id": 1, "title": "です", "level": "N5", "type": "GrammarPoint",
                             "accuracy": 72, "unsafe_link": "https://evil.example"}],
                "vocab": [{"id": 2, "title": "学生", "level": "N5", "type": "Vocab",
                           "accuracy": 60}]}
            ))])
    result = asyncio.run(StdioMCPClient("bunpro", Session, transport).weaknesses())
    assert calls == [("get_weak_items", {"limit": 15})]
    assert result[0]["evidence"]["title"] == "です"
    assert result[0]["evidence"]["subject_type"] == "grammar"
    assert result[1]["evidence"]["subject_type"] == "vocabulary"
    assert "evil.example" not in json.dumps(result)


def test_nested_wanikani_statistics():
    result = extract_weaknesses({"data": [{"id": 1, "data": {
        "subject_id": 123, "percentage_correct": 45}}]}, "wanikani")
    assert result == [{"source": "wanikani", "evidence": {"subject_id": 123, "percentage_correct": 45}}]


def test_targeting_excludes_out_of_scope_wanikani_and_radicals():
    from trainer.mcp_client import n5_weaknesses
    def item(kind, characters):
        return {"source": "wanikani", "evidence": {"subject_type": kind, "characters": characters}}
    allowed = [item("kanji", "本"), item("vocabulary", "学生")]
    excluded = [item("kanji", "王"), item("vocabulary", "王子"), item("radical", "本")]
    bunpro = [
        {"source": "bunpro", "evidence": {"subject_type": "grammar", "title": "です", "level": "N5"}},
        {"source": "bunpro", "evidence": {"subject_type": "grammar", "title": "ので", "level": "N4"}},
        {"source": "bunpro", "evidence": {"subject_type": "vocabulary", "title": "学生", "level": "N5"}},
        {"source": "bunpro", "evidence": {"subject_type": "vocabulary", "title": "王子", "level": "N5"}},
    ]
    assert n5_weaknesses(allowed + excluded + bunpro, {"学生"}, {"本"}) == allowed + [bunpro[0], bunpro[2]]


def test_study_weaknesses_removes_raw_adapter_fields():
    from trainer.mcp_client import study_weaknesses
    result = study_weaknesses([{"source": "wanikani", "evidence": {
        "subject_id": 123, "subject_type": "kanji", "characters": "本",
        "meanings": ["Book"], "percentage_correct": 72, "reading_incorrect": 4}}])
    assert result == [{"source": "wanikani", "target": "本", "kind": "kanji",
                       "meanings": ["Book"], "accuracy": 72}]


def test_n5_targeting_balances_sources_and_kinds():
    from trainer.mcp_client import n5_weaknesses
    items = [
        *({"source": "bunpro", "evidence": {"subject_type": "grammar", "title": f"g{i}", "level": "N5"}}
          for i in range(8)),
        *({"source": "bunpro", "evidence": {"subject_type": "vocabulary", "title": "学生", "level": "N5"}}
          for _ in range(5)),
        *({"source": "wanikani", "evidence": {"subject_type": "kanji", "characters": "本"}}
          for _ in range(5)),
    ]
    result = n5_weaknesses(items, {"学生"}, {"本"})
    assert len(result) == 9
    assert {(x["source"], x["evidence"]["subject_type"]) for x in result} == {
        ("bunpro", "grammar"), ("bunpro", "vocabulary"), ("wanikani", "kanji")}
