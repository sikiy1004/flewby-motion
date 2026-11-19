# ローカル PC / VPS（Oracle Cloud Always Free 等）で動かす場合のイメージ
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git curl cron tzdata nodejs npm \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Asia/Tokyo PYTHONUNBUFFERED=1 AUTOPILOT_HOME=/app
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[edge]" && python -m playwright install --with-deps chromium
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci --no-audit --no-fund && npx remotion browser ensure
COPY . .
COPY scripts/crontab /etc/cron.d/autopilot
RUN chmod 0644 /etc/cron.d/autopilot
CMD ["sh", "-c", "printenv | grep -v '^_' > /etc/environment && cron -f"]
