import os

class Config:
    ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t") or ENV == "development"
    TESTING = ENV == "testing"

    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    QUEUE_NAME = os.getenv("QUEUE_NAME", "image_jobs")
    DLX_NAME = os.getenv("DLX_NAME", "image_jobs_dlx")
    DLQ_NAME = os.getenv("DLQ_NAME", "image_jobs_dlq")
    
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    LOG_LEVEL = "DEBUG" if DEBUG else os.getenv("LOG_LEVEL", "INFO")

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "images")

    if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
        raise ValueError("MINIO_ROOT_USER and MINIO_ROOT_PASSWORD must be set in environment")

config = Config()