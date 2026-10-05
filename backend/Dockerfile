FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "python", "src/main.py"]
