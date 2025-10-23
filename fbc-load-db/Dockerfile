# Dockerfile.loader
FROM python:3.11-slim

# System deps used by entrypoint to fetch scrapers
RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates curl bash tar && \
    rm -rf /var/lib/apt/lists/*

# App files (bake these in!)
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy your orchestrator + helper
COPY main.py scraper.py /app/

# Copy the startup script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Where the scrapers will be placed at runtime
ENV SCRAPERS_DIR=/app/scrapers \
    BIG_REPO_URL="https://gitlab.com/OdinLimaye/cs373-fall-2025-55085_07.git" \
    SCRAPERS_PATH="scrapers" \
    SCRAPERS_REF="main" \
    FETCH_METHOD="sparse"

# Start-up: fetch scrapers then exec your app (entrypoint handles this)
ENTRYPOINT ["/entrypoint.sh"]
# Fallback cmd if you want to override
CMD ["python", "/app/main.py"]
