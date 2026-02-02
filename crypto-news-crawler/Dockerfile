# Python crawler image
FROM python:3.11-slim

# Prevent Python buffering logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, useful if Playwright rendered fetch is enabled)
# Uncomment if you plan to use ENABLE_RENDERED_FETCH=1 frequently
# RUN apt-get update && apt-get install -y \
#     libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
#     libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
#     libpango-1.0-0 libcairo2 libasound2 libxshmfence1 fonts-liberation \
#   && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Optional: install Playwright browsers ahead of time for rendered fetch
# RUN python -m playwright install

# Copy app source and env
COPY app ./app
COPY .env ./.env

# Default command: run all crawlers
CMD ["python", "-m", "app.scripts.run_all_crawlers"]
