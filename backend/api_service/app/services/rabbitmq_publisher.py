import json
import logging
import os
import pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "image_jobs"

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None

    def _ensure_connection(self):
        if self.connection is None or self.connection.is_closed:
            params = pika.URLParameters(RABBITMQ_URL)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

    def publish_job(self, job_id):
        self._ensure_connection()
        message = json.dumps({"job_id": job_id})
        self.channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.info("Published job %s to RabbitMQ", job_id)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()