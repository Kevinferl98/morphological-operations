import signal
import sys
from worker.rabbitmq_consumer import RabbitMQConsumer
from worker.redis_client import RedisClient
from worker.image_processor import process_job_logic
from my_observability import setup_observability
from my_observability import get_logger
from worker.minio_client import MinioClient
from worker.config import config

logger = get_logger(__name__)

INFRASTRUCTURE_LOGGERS = {
    "botocore": {"level": "INFO"},
    "boto3": {"level": "INFO"},
    "urllib3": {"level": "INFO"},
    "pika": {"level": "INFO"},
}

def main():
    setup_observability(
        log_level=config.LOG_LEVEL,
        extra_loggers=INFRASTRUCTURE_LOGGERS
    )
    redis_client = RedisClient()
    minio_client = MinioClient()

    def on_message_received(job_id):
        process_job_logic(job_id, redis_client, minio_client)

    consumer = RabbitMQConsumer(callback=on_message_received)

    def stop_handler(sig, frame):
        logger.info("Shutdown signal received. Closing connections...")
        consumer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    consumer.start()

if __name__ == "__main__":
    main()