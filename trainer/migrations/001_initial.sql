CREATE TABLE IF NOT EXISTS grammar (
 id TEXT PRIMARY KEY, category TEXT NOT NULL, title_it TEXT NOT NULL, title_en TEXT NOT NULL,
 description_it TEXT NOT NULL, description_en TEXT NOT NULL, pattern TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sentences (
 id TEXT PRIMARY KEY, grammar_id TEXT NOT NULL REFERENCES grammar(id),
 prompt_it TEXT, prompt_en TEXT, refs TEXT NOT NULL, attribution TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exercises (
 id TEXT PRIMARY KEY, sentence_id TEXT NOT NULL REFERENCES sentences(id),
 language TEXT NOT NULL, prompt TEXT NOT NULL, refs TEXT NOT NULL,
 mode TEXT NOT NULL, context TEXT NOT NULL DEFAULT '[]', created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
 id INTEGER PRIMARY KEY, exercise_id TEXT NOT NULL UNIQUE REFERENCES exercises(id),
 answer TEXT NOT NULL, result TEXT NOT NULL, quality INTEGER NOT NULL,
 hinted INTEGER NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
 sentence_id TEXT PRIMARY KEY REFERENCES sentences(id), repetitions INTEGER NOT NULL,
 interval_days INTEGER NOT NULL, ease REAL NOT NULL, due REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS journal (
 grammar_id TEXT PRIMARY KEY REFERENCES grammar(id), observations TEXT NOT NULL,
 updated_at REAL NOT NULL, resolved INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK (id = 1), value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS kanji (literal TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vocabulary (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS n5_vocab (term TEXT PRIMARY KEY, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS n5_kanji (literal TEXT PRIMARY KEY, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources (name TEXT PRIMARY KEY, data TEXT NOT NULL, imported_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_created ON attempts(created_at);
CREATE INDEX IF NOT EXISTS sentences_grammar ON sentences(grammar_id);
