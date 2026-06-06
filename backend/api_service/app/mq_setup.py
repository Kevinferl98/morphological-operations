import pika
from my_observability import get_logger
from app.config import config

logger = get_logger(__name__)

def setup_rabbitmq_topology(channel: pika.adapters.blocking_connection.BlockingChannel):
    try:
        channel.exchange_declare(
            exchange=config.DLX_NAME,
            exchange_type="direct",
            durable=True
        )

        channel.queue_declare(
            queue=config.DLQ_NAME,
            durable=True
        )

        channel.queue_bind(
            exchange=config.DLX_NAME,
            queue=config.DLQ_NAME,
            routing_key=config.DLQ_NAME
        )

        queue_args = {
            "x-dead-letter-exchange": config.DLX_NAME,
            "x-dead-letter-routing-key": config.DLQ_NAME
        }

        channel.queue_declare(
            queue=config.QUEUE_NAME,
            durable=True,
            arguments=queue_args
        )
        channel.basic_qos(prefetch_count=1)
        logger.info(f"RabbitMQ topology successfully initialized (Queue: {config.QUEUE_NAME})")

    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ topology: {e}")
        raise e