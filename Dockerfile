FROM ghcr.io/astral-sh/uv:0.11.26 AS uv
FROM python:3.12-slim AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python
FROM python:3.12-slim AS runtime
RUN groupadd --gid 10001 trainer && useradd --uid 10001 --gid trainer --no-create-home trainer
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY trainer ./trainer
COPY scripts ./scripts
RUN mkdir /data && chown 10001:10001 /data
ENV PATH="/app/.venv/bin:$PATH" DATABASE_PATH=/data/trainer.sqlite3 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "trainer.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers", "--limit-concurrency", "32"]

# Optional target with the published Bunpro/WaniKani stdio packages.
FROM node:22-bookworm-slim AS mcp-servers
ARG BUNPRO_MCP_VERSION=0.3.0
ARG WANIKANI_MCP_VERSION=0.1.4
RUN npm install --global "bunpro-mcp-server@${BUNPRO_MCP_VERSION}" "kani-mcp-server@${WANIKANI_MCP_VERSION}"
FROM runtime AS mcp
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
COPY --from=mcp-servers /usr/local/bin/node /usr/local/bin/node
COPY --from=mcp-servers /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=mcp-servers /usr/local/bin/bunpro-mcp-server /usr/local/bin/bunpro-mcp-server
COPY --from=mcp-servers /usr/local/bin/kani-mcp-server /usr/local/bin/kani-mcp-server
USER 10001:10001

FROM runtime AS default
