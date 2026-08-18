FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system packages in a single layer to reduce image size
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  libjpeg-dev \
  zlib1g-dev \
  libffi-dev \
  netcat-openbsd \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libglib2.0-0 \
  libgdk-pixbuf-2.0-0 \
  fontconfig \
  shared-mime-info \
  && rm -rf /var/lib/apt/lists/*

# Install uv (high-performance Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup --system cashevide && adduser --system --group cashevide

WORKDIR /app

# Dependency installation using uv
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system --no-cache . gunicorn

# Set up the entrypoint script for migrations and setup WITH ownership
COPY --chown=cashevide:cashevide ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy the rest of the application code WITH ownership
COPY --chown=cashevide:cashevide . .

RUN mkdir -p /app/staticfiles /app/media && \
  chown -R cashevide:cashevide /app/staticfiles /app/media

USER cashevide

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

# Default command for production using Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "5"]
