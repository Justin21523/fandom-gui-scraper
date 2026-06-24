FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

COPY requirements-backend.txt /app/requirements-backend.txt
RUN pip install --no-cache-dir -r /app/requirements-backend.txt

COPY . /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AUTH_DISABLED=true \
    FANDOM_DEMO_MODE=true \
    FANDOM_DEMO_ROOT=/app/sample_data \
    ENABLE_FILE_EXPORT=true \
    DOWNLOAD_IMAGES=false

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
