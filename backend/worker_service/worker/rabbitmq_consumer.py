import json
import pika
import time
from worker.config import config
from my_observability import get_logger

logger = get_logger(__name__)

class RabbitMQConsumer:
    def __init__(self, callback):
        self.callback = callback
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        while True:
            try:
                params = pika.URLParameters(config.RABBITMQ_URL)
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()

                self.channel.exchange_declare(
                    exchange=config.DLX_NAME,
                    exchange_type="direct",
                    durable=True
                )

                self.channel.queue_declare(
                    queue=config.DLQ_NAME,
                    durable=True
                )

                self.channel.queue_bind(
                    exchange=config.DLX_NAME,
                    queue=config.DLQ_NAME,
                    routing_key=config.DLQ_NAME
                )

                queue_args = {
                    "x-dead-letter-exchange": config.DLX_NAME,
                    "x-dead-letter-routing-key": config.DLQ_NAME
                }

                self.channel.queue_declare(
                    queue=config.QUEUE_NAME,
                    durable=True,
                    arguments=queue_args
                )
                
                self.channel.basic_qos(prefetch_count=1)
                break
            except pika.exceptions.AMQPConnectionError:
                logger.warning("RabbitMQ not available, trying in 5s...")
                time.sleep(5)

    def start(self):
        def on_message(ch, method, properties, body):
            try:
                payload = json.loads(body)
                job_id = payload.get("job_id")
                self.callback(job_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.exception("Fatal error processing message")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue=config.QUEUE_NAME, on_message_callback=on_message)
        logger.info(f"Worker listening on {config.QUEUE_NAME}")
        self.channel.start_consuming()

    def stop(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
