CREATE TABLE IF NOT EXISTS provider_secrets (
 name TEXT PRIMARY KEY CHECK (name IN ('openai_api_key', 'openrouter_api_key')),
 value TEXT NOT NULL
);
