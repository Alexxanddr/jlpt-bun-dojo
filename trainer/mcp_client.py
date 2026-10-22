import asyncio
import json
import os
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient(ABC):
    @abstractmethod
    async def weaknesses(self) -> list[dict]: ...


class StdioMCPClient(MCPClient):
    """Only administrator-configured executables; model output cannot select tools or commands."""

    def __init__(self, source: str, session_factory=ClientSession, transport_factory=stdio_client):
        if source not in {"bunpro", "wanikani"}:
            raise ValueError("Unknown MCP source")
        self.source = source
        self.session_factory = session_factory
        self.transport_factory = transport_factory

    async def weaknesses(self):
        prefix = self.source.upper()
        command = os.getenv(f"{prefix}_MCP_COMMAND", "")
        if not command:
            return []
        args = json.loads(os.getenv(f"{prefix}_MCP_ARGS", "[]"))
        if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
            raise ValueError("MCP args must be a JSON string array")
        env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", f"{prefix}_API_TOKEN") if k in os.environ}
        params = StdioServerParameters(command=command, args=args, env=env)
        async with asyncio.timeout(25), AsyncExitStack() as stack:
            # Do not forward server stderr: third-party processes may log credentials.
            sink = stack.enter_context(open(os.devnull, "w"))
            streams = await stack.enter_async_context(self.transport_factory(params, errlog=sink))
            session = await stack.enter_async_context(self.session_factory(
                streams[0], streams[1], read_timeout_seconds=timedelta(seconds=20)))
            await session.initialize()
            if self.source == "bunpro":
                result = await session.call_tool("get_weak_items", {"limit": 15})
            else:
                result = await session.call_tool("list_review_statistics", {"percentages_less_than": 80})
            if result.isError:
                raise ValueError("MCP tool failed")
            texts = [c.text for c in result.content if c.type == "text"]
            raw = "\n".join(texts)
            if len(raw) > 131072:
                raise ValueError("MCP response too large")
            items = extract_weaknesses(json.loads(raw), self.source)
            if self.source == "wanikani":
                for item in items[:10]:
                    subject_id = item["evidence"].get("subject_id")
                    if not isinstance(subject_id, int) or subject_id <= 0:
                        continue
                    detail = await session.call_tool("get_resource", {"resource": "subjects", "id": subject_id})
                    if detail.isError:
                        continue
                    content = "\n".join(c.text for c in detail.content if c.type == "text")
                    if len(content) > 32768:
                        continue
                    subject = json.loads(content)
                    subject_type = subject.get("object")
                    if subject_type in {"kanji", "vocabulary", "kana_vocabulary", "radical"}:
                        item["evidence"]["subject_type"] = subject_type
                    subject = subject.get("data", subject)
                    if isinstance(subject, dict):
                        for key in ("slug", "characters"):
                            if isinstance(subject.get(key), str):
                                item["evidence"][key] = subject[key][:200]
                        meanings = subject.get("meanings", [])
                        item["evidence"]["meanings"] = [m["meaning"][:200] for m in meanings[:5]
                            if isinstance(m, dict) and isinstance(m.get("meaning"), str)]
            return items


def extract_weaknesses(data, source):
    """Retain bounded factual fields, with no HTML or externally supplied links."""
    found: list[dict] = []
    allowed = (
        "id", "subject_id", "slug", "title", "meaning", "grammar_point", "level", "type",
        "accuracy", "times_studied", "estimated_misses", "percentage_correct", "reading_correct",
        "meaning_correct", "reading_incorrect", "meaning_incorrect",
    )

    if source == "bunpro" and isinstance(data, dict):
        for group, kind in (("grammar", "grammar"), ("vocab", "vocabulary")):
            values = data.get(group, [])
            if not isinstance(values, list):
                continue
            for value in values[:15]:
                if not isinstance(value, dict):
                    continue
                fields = {k: value[k] for k in allowed
                          if k in value and isinstance(value[k], (str, int, float))}
                if isinstance(fields.get("title"), str):
                    fields["subject_type"] = kind
                    found.append({"source": source, "evidence": fields})
        return found

    def visit(value, depth=0):
        if depth > 8 or len(found) >= 30:
            return
        if isinstance(value, list):
            for item in value[:500]:
                visit(item, depth + 1)
        elif isinstance(value, dict):
            fields = {k: value[k] for k in allowed
                      if k in value and isinstance(value[k], (str, int, float))}
            if any(k in fields for k in ("subject_id", "slug", "title", "grammar_point")):
                found.append({"source": source, "evidence": fields})
            for key, item in value.items():
                if key not in fields:
                    visit(item, depth + 1)
    visit(data)
    return found


async def all_weaknesses():
    results = await asyncio.gather(*(StdioMCPClient(s).weaknesses() for s in ("bunpro", "wanikani")),
                                   return_exceptions=True)
    return {"items": [item for result in results if isinstance(result, list) for item in result],
            "unavailable": [name for name, result in zip(("bunpro", "wanikani"), results)
                            if isinstance(result, BaseException)]}


def n5_weaknesses(items: list[dict], vocabulary: set[str], kanji: set[str]) -> list[dict]:
    eligible = []
    for item in items:
        evidence = item["evidence"]
        if item["source"] == "bunpro":
            kind = evidence.get("subject_type")
            level = str(evidence.get("level", "")).upper().replace("JLPT", "").strip()
            if (kind == "grammar" and level in {"N5", "5"}) or (
                kind == "vocabulary" and evidence.get("title") in vocabulary
            ):
                eligible.append(item)
            continue
        term = evidence.get("characters") or evidence.get("slug")
        kind = evidence.get("subject_type")
        if (kind == "kanji" and term in kanji) or (
            kind in {"vocabulary", "kana_vocabulary"} and term in vocabulary
        ):
            eligible.append(item)
    selected = []
    counts: dict[tuple[str, str], int] = {}
    for item in eligible:
        key = (item["source"], str(item["evidence"].get("subject_type", "item")))
        if counts.get(key, 0) < 3:
            selected.append(item)
            counts[key] = counts.get(key, 0) + 1
    return selected[:10]


def study_weaknesses(items: list[dict]) -> list[dict]:
    """Expose compact study facts to the model and UI, not adapter payloads."""
    result = []
    for item in items:
        evidence = item["evidence"]
        target = evidence.get("characters") or evidence.get("slug") or evidence.get("grammar_point") or evidence.get("title")
        if not isinstance(target, str) or not target:
            continue
        result.append({
            "source": item["source"], "target": target,
            "kind": evidence.get("subject_type", "grammar" if item["source"] == "bunpro" else "item"),
            "meanings": evidence.get("meanings", [evidence["meaning"]] if evidence.get("meaning") else []),
            "accuracy": evidence.get("accuracy", evidence.get("percentage_correct")),
        })
    return result
