import json
import os
import pika
from my_observability import get_logger
from app.mq_setup import setup_rabbitmq_topology

logger = get_logger(__name__)

DEFAULT_RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DEFAULT_QUEUE_NAME = "image_jobs"

class RabbitMQPublisher:
    def __init__(self, amqp_url = None, queue_name = None, connection_factory = None):
        self.amqp_url = amqp_url or DEFAULT_RABBITMQ_URL
        self.queue_name = queue_name or DEFAULT_QUEUE_NAME

        self._connection_factory = connection_factory or pika.BlockingConnection

        self.connection = None
        self.channel = None

    def _ensure_connection(self):
        if self.connection is None or self.connection.is_closed:
            params = pika.URLParameters(self.amqp_url)
            self.connection = self._connection_factory(params)
            self.channel = self.connection.channel()
            setup_rabbitmq_topology(self.channel)

    def publish_job(self, job_id):
        self._ensure_connection()
        message = json.dumps({"job_id": job_id})

        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.info("Published job %s to RabbitMQ", job_id)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()