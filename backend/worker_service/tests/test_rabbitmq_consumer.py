import json
import pytest
from unittest.mock import MagicMock, patch
from worker.rabbitmq_consumer import RabbitMQConsumer

@pytest.fixture
def mock_pika():
    with patch("worker.rabbitmq_consumer.pika") as mock:
        yield mock

@pytest.fixture
def mock_config():
    with patch("worker.rabbitmq_consumer.config") as mock:
        mock.RABBITMQ_URL = "amqp://guest:guest@localhost/"
        mock.QUEUE_NAME = "test_queue"
        mock.DLX_NAME = "image_jobs_dlx"
        mock.DLQ_NAME = "image_jobs_dlq"
        yield mock

@pytest.fixture
def consumer(mock_pika, mock_config):
    callback = MagicMock()

    connection = MagicMock()
    channel = MagicMock()

    connection.channel.return_value = channel
    mock_pika.BlockingConnection.return_value = connection

    consumer = RabbitMQConsumer(callback)

    return consumer, callback, connection, channel

def test_connect_establishes_connection(mock_pika, mock_config):
    callback = MagicMock()

    connection = MagicMock()
    channel = MagicMock()

    connection.channel.return_value = channel
    mock_pika.BlockingConnection.return_value = connection

    consumer = RabbitMQConsumer(callback)

    assert consumer.connection == connection
    assert consumer.channel == channel

    queue_args = {
        "x-dead-letter-exchange": "image_jobs_dlx",
        "x-dead-letter-routing-key": "image_jobs_dlq"
    }

    channel.queue_declare.assert_any_call(
        queue=mock_config.QUEUE_NAME,
        durable=True,
        arguments=queue_args
    )

    channel.basic_qos.assert_called_once_with(prefetch_count=1)

def test_message_processing_success(consumer):
    consumer, callback, _, channel = consumer

    captured_callback = {}

    def fake_basic_consume(queue, on_message_callback):
        captured_callback["fn"] = on_message_callback

    channel.basic_consume.side_effect = fake_basic_consume

    consumer.start()

    on_message = captured_callback["fn"]

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag"

    body = json.dumps({"job_id": "123"}).encode()

    on_message(ch, method, None, body)

    callback.assert_called_once_with("123")
    ch.basic_ack.assert_called_once_with(delivery_tag="tag")

def test_message_processing_failure(consumer):
    consumer, callback, _, channel = consumer

    callback.side_effect = Exception("processing error")

    captured_callback = {}

    def fake_basic_consume(queue, on_message_callback):
        captured_callback["fn"] = on_message_callback

    channel.basic_consume.side_effect = fake_basic_consume

    consumer.start()

    on_message = captured_callback["fn"]

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag"

    body = json.dumps({"job_id": "123"}).encode()

    on_message(ch, method, None, body)

    ch.basic_nack.assert_called_once_with(delivery_tag="tag", requeue=False)


def test_stop_closes_connection(consumer):
    consumer, _, connection, _ = consumer

    connection.is_open = True

    consumer.stop()

    connection.close.assert_called_once()

def test_stop_does_nothing_if_connection_closed(consumer):
    consumer, _, connection, _ = consumer

    connection.is_open = False

    consumer.stop()

    connection.close.assert_not_called()