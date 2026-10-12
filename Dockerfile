FROM python:3.14-slim

# Copy uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set Python and uv environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Create unprivileged user (UID 3000 to match web-tech-tw conventions)
RUN useradd -u 3000 -m recv

WORKDIR /app
RUN chown -R 3000:3000 /app

# Cache dependency installation layer
COPY --chown=3000:3000 pyproject.toml uv.lock ./

USER 3000

# Install dependencies into virtualenv without copying project source code yet
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source files
COPY --chown=3000:3000 . ./

# Install project into virtualenv
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
