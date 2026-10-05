# Paso Seguro 5G · servidor de borde (CPU, sin GPU). Imagen para laptop Linux o para el MXIE.
#   docker build -t paso-seguro-borde:0.1 .
#   docker build --platform linux/amd64 -t paso-seguro-borde:0.1 .   # desde una Mac con chip Apple
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends libglib2.0-0 curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY static ./static
COPY config ./config
RUN mkdir -p /app/datos

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://127.0.0.1:8000/ping || exit 1
# Corre como root por simplicidad del hackatón (volúmenes y webcam USB sin líos de permisos).
# Con tableros abiertos (SSE) uvicorn esperaría para siempre al apagarse: máximo 3 s
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "3"]
