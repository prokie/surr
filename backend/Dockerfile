FROM python:3.14-slim

# Prevents Python from writing .pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE=1

# Prevents Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Python deps and app
COPY pyproject.toml ./
COPY src ./src
COPY README.md ./
COPY logging.json ./
COPY uv.lock ./
RUN uv sync --locked --no-dev

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "surr.main:app", "--host", "0.0.0.0", "--port", "8000","--workers", "4"]