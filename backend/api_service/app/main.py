from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.jobs import router
from app.config import config
from my_observability import setup_observability, setup_fastapi_logging

INFRASTRUCTURE_LOGGERS = {
    "botocore": {"level": "INFO"},
    "boto3": {"level": "INFO"},
    "urllib3": {"level": "INFO"},
    "pika": {"level": "INFO"},
}

setup_observability(
    log_level=config.LOG_LEVEL,
    extra_loggers=INFRASTRUCTURE_LOGGERS
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

setup_fastapi_logging(app)