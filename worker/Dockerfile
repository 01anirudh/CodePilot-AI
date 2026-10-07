FROM python:3.11-slim

WORKDIR /app

# Install essential system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source code
COPY . .

# Run as non-root user for security
RUN useradd -m -u 1000 codepilot && chown -R codepilot:codepilot /app
USER codepilot

CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "-Q", "analysis,workflows,embeddings,celery", "--concurrency=2"]
