import asyncio
import hmac
import json
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from trainer.ai import AIClient, AIError, endpoint_url
from trainer.db import connect, initialize
from trainer.grading import deterministic, sm2
from trainer.mcp_client import all_weaknesses, n5_weaknesses, study_weaknesses
from trainer.models import AnswerRequest, ExerciseRequest, Settings

logger = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"
# shortcut: one user and one worker, move limiter and sessions to shared storage before scaling.
requests_window: list[float] = []
credentials: dict[str, float] = {}
weakness_cache: dict = {"items": [], "unavailable": []}
ai_lock = asyncio.Lock()


def authentication_enabled():
    return bool(os.getenv("APP_PASSWORD", ""))


@asynccontextmanager
async def lifespan(app):
    password = os.getenv("APP_PASSWORD", "")
    if password and (len(password) < 16 or password.startswith("replace-")):
        raise RuntimeError("APP_PASSWORD must contain at least 16 characters")
    endpoint_url(os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"))
    initialize()
    yield


app = FastAPI(title="JLPT Bun Dojo", lifespan=lifespan, docs_url=None, redoc_url=None,
              openapi_url=None)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({"detail": "invalid_input"}, status_code=422)


@app.exception_handler(AIError)
async def ai_error(request, exc):
    logger.warning("AI request failed: code=%s", str(exc))
    return JSONResponse({"detail": str(exc)}, status_code=502)


@app.middleware("http")
async def security(request: Request, call_next):
    if request.headers.get("content-length", "0").isdigit() and int(
        request.headers.get("content-length", "0")
    ) > 8192:
        return JSONResponse({"detail": "input_too_large"}, status_code=413)
    if request.url.path.startswith("/api/"):
        if request.method != "GET" and request.headers.get("x-trainer-request") != "1":
            return JSONResponse({"detail": "invalid_origin"}, status_code=403)
        origin = request.headers.get("origin")
        expected = os.getenv("APP_ORIGIN", "http://localhost:8000")
        if origin and origin != expected:
            return JSONResponse({"detail": "invalid_origin"}, status_code=403)
        if authentication_enabled() and request.url.path != "/api/login":
            cookie = request.cookies.get("trainer_session", "")
            if credentials.get(cookie, 0) < time.time():
                return JSONResponse({"detail": "authentication_required"}, status_code=401)
        if request.method != "GET":
            now = time.time()
            requests_window[:] = [t for t in requests_window if t > now - 60]
            if len(requests_window) >= 20:
                return JSONResponse({"detail": "rate_limited"}, status_code=429)
            requests_window.append(now)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 8192:
                return JSONResponse({"detail": "input_too_large"}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers.update({
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                                   "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
                                   "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "microphone=(), camera=(), geolocation=()",
        "X-Frame-Options": "DENY", "Cache-Control": "no-store",
    })
    if os.getenv("COOKIE_SECURE", "false").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@app.post("/api/login")
async def login(request: Request):
    try:
        data = await request.json()
    except ValueError:
        raise HTTPException(422, "invalid_input") from None
    password = data.get("password") if isinstance(data, dict) else None
    expected = os.getenv("APP_PASSWORD", "")
    if not isinstance(password, str) or not expected or not hmac.compare_digest(
        password.encode(), expected.encode()
    ):
        raise HTTPException(401, "invalid_credentials")
    now = time.time()
    for key in list(credentials):
        if credentials[key] < now:
            del credentials[key]
    if len(credentials) >= 50:
        credentials.pop(next(iter(credentials)))
    token = secrets.token_urlsafe(32)
    credentials[token] = now + 12 * 3600
    response = JSONResponse({"ok": True})
    response.set_cookie("trainer_session", token, httponly=True, samesite="strict", max_age=43200,
                        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true")
    return response


@app.post("/api/logout")
async def logout(request: Request):
    credentials.pop(request.cookies.get("trainer_session", ""), None)
    response = JSONResponse({"ok": True})
    response.delete_cookie("trainer_session")
    return response


def load_settings():
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE id=1").fetchone()
        secrets_rows = dict(db.execute("SELECT name,value FROM provider_secrets"))
    values = json.loads(row[0]) if row else dict(
        generation_provider=os.getenv("GENERATION_PROVIDER", "openai"),
        evaluation_provider=os.getenv("EVALUATION_PROVIDER", "openai"),
        generation_model=os.getenv("GENERATION_MODEL", "local-model"),
        evaluation_model=os.getenv("EVALUATION_MODEL", "local-model"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"))
    values.setdefault("openai_base_url", os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"))
    values.update({
        "openai_api_key": secrets_rows.get("openai_api_key", os.getenv("OPENAI_API_KEY", "")),
        "openrouter_api_key": secrets_rows.get("openrouter_api_key", os.getenv("OPENROUTER_API_KEY", "")),
    })
    return Settings.model_validate(values)


@app.get("/api/settings")
async def settings():
    return {"settings": load_settings(), "authentication_enabled": authentication_enabled(), "providers": {
        "openai_key_configured": bool(load_settings().openai_api_key),
        "openrouter_key_configured": bool(load_settings().openrouter_api_key),
        "mcp_configured": bool(os.getenv("BUNPRO_MCP_COMMAND") or os.getenv("WANIKANI_MCP_COMMAND")),
    }}


@app.put("/api/settings")
async def save_settings(value: Settings):
    try:
        endpoint_url(value.openai_base_url)
    except ValueError:
        raise HTTPException(422, "invalid_endpoint") from None
    with connect() as db:
        if value.category and not db.execute("SELECT 1 FROM grammar WHERE category=?", (value.category,)).fetchone():
            raise HTTPException(422, "invalid_category")
        db.execute("INSERT INTO settings VALUES (1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value",
                   (value.model_dump_json(),))
        for name in ("openai_api_key", "openrouter_api_key"):
            secret = getattr(value, name)
            if secret:
                db.execute("INSERT INTO provider_secrets VALUES (?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                           (name, secret))
    return {"ok": True}


@app.get("/api/grammar")
async def grammar_list():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM grammar ORDER BY id")]


@app.post("/api/mcp/sync")
async def mcp_sync():
    if not load_settings().mcp_enabled:
        raise HTTPException(409, "mcp_disabled")
    async with ai_lock:
        result = await all_weaknesses()
        weakness_cache.update(result)
    return result


@app.post("/api/exercises")
async def exercise(value: ExerciseRequest):
    config = load_settings()
    if value.generate and value.mode not in {"new", "targeted"}:
        raise HTTPException(422, "generation_requires_new")
    with connect() as db:
        params: list = []
        where = ""
        if value.category:
            where = " AND g.category=?"
            params.append(value.category)
        if value.mode in {"review", "cram"}:
            sql = ("SELECT s.* FROM sentences s JOIN grammar g ON g.id=s.grammar_id "
                   "JOIN reviews r ON r.sentence_id=s.id WHERE 1=1" + where)
            if value.mode == "review":
                sql += " AND r.due<=?"
                params.append(time.time())
            sql += " ORDER BY r.due LIMIT 1"
        else:
            sql = ("SELECT s.* FROM sentences s JOIN grammar g ON g.id=s.grammar_id "
                   "WHERE s.id NOT LIKE 'generated-%'" + where + " ORDER BY RANDOM() LIMIT 1")
        row = db.execute(sql, params).fetchone()
        if row is None:
            raise HTTPException(404, "no_exercises")
        sentence = dict(row)
        grammar = dict(db.execute("SELECT * FROM grammar WHERE id=?", (sentence["grammar_id"],)).fetchone())
    context = weakness_cache["items"] if config.mcp_enabled and value.mode == "targeted" else []
    if value.mode == "targeted" and not context:
        raise HTTPException(409, "sync_weaknesses_first")
    refs = json.loads(sentence["refs"])
    prompt = sentence[f"prompt_{value.language}"]
    if not prompt or value.generate or value.mode == "targeted":
        with connect() as db:
            vocab = {r[0] for r in db.execute("SELECT term FROM n5_vocab")}
            kanji = {r[0] for r in db.execute("SELECT literal FROM n5_kanji")}
        if value.mode == "targeted":
            context = study_weaknesses(n5_weaknesses(context, vocab, kanji))
            if not context:
                raise HTTPException(409, "no_n5_weaknesses")
        async with ai_lock:
            generated = await AIClient(config).generate(value.language, grammar, context,
                reference=refs if not prompt and not value.generate and value.mode != "targeted" else None,
                difficulty=value.difficulty, allowed_kanji="".join(sorted(kanji)),
                allowed_vocabulary=sorted(vocab))
        prompt, refs = generated.prompt, generated.references
        if any(deterministic(ref, refs, vocab, kanji, grammar["pattern"])["findings"] for ref in refs):
            logger.warning("Generation rejected by N5 checks after adapter validation")
            raise HTTPException(422, "generated_outside_dataset")
        sentence["id"] = "generated-" + secrets.token_hex(12)
        sentence["attribution"] = "AI-generated; unreviewed"
        with connect() as db:
            db.execute("INSERT INTO sentences VALUES (?,?,?,?,?,?)", (
                sentence["id"], grammar["id"], prompt if value.language == "it" else None,
                prompt if value.language == "en" else None, json.dumps(refs), "AI-generated; unreviewed"))
    eid = secrets.token_hex(16)
    with connect() as db:
        db.execute("INSERT INTO exercises(id,sentence_id,language,prompt,refs,mode,context,created_at) VALUES (?,?,?,?,?,?,?,?)", (
            eid, sentence["id"], value.language, prompt, json.dumps(refs), value.mode,
            json.dumps(context), time.time()))
    return {"id": eid, "prompt": prompt, "grammar": grammar, "language": value.language,
            "difficulty": value.difficulty, "weaknesses": context, "attribution": sentence["attribution"]}


@app.get("/api/exercises/{exercise_id}/hint")
async def hint(exercise_id: str):
    with connect() as db:
        row = db.execute("SELECT refs FROM exercises WHERE id=?", (exercise_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "not_found")
    with connect() as db:
        db.execute("UPDATE exercises SET hinted=1 WHERE id=?", (exercise_id,))
    return {"references": json.loads(row[0])}


@app.post("/api/answers")
async def answer(value: AnswerRequest):
    if not value.answer.strip():
        raise HTTPException(422, "invalid_input")
    async with ai_lock:
        with connect() as db:
            existing = db.execute("SELECT result FROM attempts WHERE exercise_id=?", (value.exercise_id,)).fetchone()
            if existing:
                return json.loads(existing[0])
            row = db.execute("SELECT e.*, s.grammar_id FROM exercises e JOIN sentences s "
                             "ON s.id=e.sentence_id WHERE e.id=?", (value.exercise_id,)).fetchone()
            if row is None:
                raise HTTPException(404, "not_found")
            e = dict(row)
            grammar = dict(db.execute("SELECT * FROM grammar WHERE id=?", (e["grammar_id"],)).fetchone())
            vocab = {r[0] for r in db.execute("SELECT term FROM n5_vocab")}
            kanji = {r[0] for r in db.execute("SELECT literal FROM n5_kanji")}
        checks = deterministic(value.answer, json.loads(e["refs"]), vocab, kanji, grammar["pattern"])
        evaluation = await AIClient(load_settings()).evaluate(e["language"], e["prompt"], value.answer,
                                                              grammar, checks)
        hard_errors = [f for f in checks["findings"] if f["severity"] == "error"]
        accepted = evaluation.accepted and not hard_errors
        score = min(evaluation.scores.model_dump().values())
        quality = min(2, score // 20) if not accepted else max(3, min(5, score // 20))
        used_hint = bool(value.hinted or e["hinted"])
        if used_hint:
            quality = min(quality, 2)
        result = {"checks": checks, "ai": evaluation.model_dump(), "accepted": accepted,
                  "grammar": grammar, "weaknesses": json.loads(e["context"]), "quality": quality}
        now = time.time()
        with connect() as db:
            db.execute("INSERT INTO attempts(exercise_id,answer,result,quality,hinted,created_at) VALUES (?,?,?,?,?,?)",
                       (e["id"], value.answer, json.dumps(result), quality, used_hint, now))
            if e["mode"] != "cram":
                old = db.execute("SELECT * FROM reviews WHERE sentence_id=?", (e["sentence_id"],)).fetchone()
                state = sm2(quality, old["repetitions"], old["interval_days"], old["ease"]) if old else sm2(quality)
                due = now + state["interval_days"] * 86400
                db.execute("INSERT INTO reviews VALUES (?,?,?,?,?) ON CONFLICT(sentence_id) DO UPDATE SET "
                           "repetitions=excluded.repetitions, interval_days=excluded.interval_days, "
                           "ease=excluded.ease, due=excluded.due", (e["sentence_id"], *state.values(), due))
                result["next_review"] = due
            if not accepted or evaluation.suggestions or hard_errors:
                db.execute("INSERT INTO journal VALUES (?,?,?,0) ON CONFLICT(grammar_id) DO UPDATE SET "
                           "observations=excluded.observations, updated_at=excluded.updated_at, resolved=0",
                           (grammar["id"], json.dumps(result), now))
            db.execute("UPDATE attempts SET result=? WHERE exercise_id=?", (json.dumps(result), e["id"]))
    return result


@app.get("/api/history")
async def history():
    with connect() as db:
        return [dict(r) for r in db.execute(
            "SELECT a.*,e.prompt,e.language,s.grammar_id FROM attempts a JOIN exercises e ON e.id=a.exercise_id "
            "JOIN sentences s ON s.id=e.sentence_id ORDER BY a.created_at DESC LIMIT 100")]


@app.get("/api/journal")
async def journal():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT j.*,g.title_it,g.title_en FROM journal j "
                                          "JOIN grammar g ON g.id=j.grammar_id ORDER BY j.updated_at DESC")]


@app.post("/api/journal/{grammar_id}/resolve")
async def resolve(grammar_id: str):
    with connect() as db:
        db.execute("UPDATE journal SET resolved=1 WHERE grammar_id=?", (grammar_id,))
    return {"ok": True}


@app.get("/api/stats")
async def stats():
    with connect() as db:
        rows = db.execute("SELECT a.*,s.grammar_id FROM attempts a JOIN exercises e ON e.id=a.exercise_id "
                          "JOIN sentences s ON s.id=e.sentence_id").fetchall()
        total_grammar = db.execute("SELECT COUNT(*) FROM grammar").fetchone()[0]
        due = db.execute("SELECT COUNT(*) FROM reviews WHERE due<=?", (time.time(),)).fetchone()[0]
        sources = [dict(r) for r in db.execute("SELECT * FROM sources")]
    count = len(rows)
    axes = {key: 0.0 for key in ("grammar", "vocabulary", "register", "coverage", "independence", "recall")}
    groups: dict = {}
    for row in rows:
        result = json.loads(row["result"])
        for key in ("grammar", "vocabulary", "register"):
            axes[key] += result["ai"]["scores"][key] / count
        axes["independence"] += (0 if row["hinted"] else 100) / count
        group = groups.setdefault(row["grammar_id"], {"attempts": 0, "accepted": 0})
        group["attempts"] += 1
        group["accepted"] += int(result["accepted"])
    # Recall measures successful scheduled review attempts, excluding new practice and cram.
    with connect() as db:
        scheduled = db.execute("SELECT a.quality FROM attempts a JOIN exercises e ON e.id=a.exercise_id "
                               "WHERE e.mode='review'").fetchall()
    axes["recall"] = 100 * sum(r[0] >= 3 for r in scheduled) / len(scheduled) if scheduled else 0
    axes["coverage"] = 100 * len(groups) / max(1, total_grammar)
    return {"attempts": count, "due": due, "axes": axes, "grammar": groups, "sources": sources,
            "weaknesses": weakness_cache}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
