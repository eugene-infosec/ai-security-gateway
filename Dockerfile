# AI Security Gateway (local demo container)
FROM python:3.12-slim

WORKDIR /app

# Small container sanity defaults
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies first for better Docker layer caching
COPY requirements-runtime.txt requirements-dev.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements-runtime.txt -r requirements-dev.txt

# Copy application
COPY app ./app

EXPOSE 8000

# Local-mode runtime (reviewer-friendly)
ENV AUTH_MODE=headers
ENV ALLOW_INSECURE_HEADERS=true

# Keep logs clean: rely on your structured JSON logs, not uvicorn access logs
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
