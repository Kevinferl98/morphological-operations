FROM python:3.14-slim as builder

WORKDIR /worker

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENCV_VIDEOIO_PRIORITY_BACKEND=0 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /worker

RUN addgroup --system workergroup && adduser --system --group workeruser

COPY --from=builder /opt/venv /opt/venv

COPY . .

RUN chown -R workeruser:workergroup /worker

USER workeruser

CMD ["python", "-m", "worker.consumer"]