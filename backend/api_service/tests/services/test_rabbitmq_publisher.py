import pytest
import json
from unittest.mock import MagicMock, patch
from app.services.rabbitmq_publisher import RabbitMQPublisher

@pytest.fixture
def mock_channel():
    return MagicMock()

@pytest.fixture
def mock_connection(mock_channel):
    conn = MagicMock()
    conn.channel.return_value = mock_channel
    conn.is_closed = False
    return conn

def test_ensure_connection_creates_connection(mock_connection, mock_channel):
    with patch(
        "app.services.rabbitmq_publisher.pika.URLParameters"
    ) as mock_params, patch(
        "app.services.rabbitmq_publisher.pika.BlockingConnection",
        return_value=mock_connection
    ) as mock_conn:
        publisher = RabbitMQPublisher()
        publisher._ensure_connection()

    mock_params.assert_called_once()
    mock_conn.assert_called_once()

    mock_connection.channel.assert_called_once()

def test_ensure_connection_reuses_existing_connection(mock_connection):
    publisher = RabbitMQPublisher()
    publisher.connection = mock_connection
    publisher.channel = MagicMock()

    publisher._ensure_connection()

    mock_connection.channel.assert_not_called()

def test_publish_job(mock_connection, mock_channel):
    with patch(
        "app.services.rabbitmq_publisher.pika.BlockingConnection",
        return_value=mock_connection
    ), patch(
        "app.services.rabbitmq_publisher.pika.URLParameters"
    ):
        publisher = RabbitMQPublisher()
        publisher.publish_job("job-123")

    mock_channel.basic_publish.assert_called_once()

    args, kwargs = mock_channel.basic_publish.call_args

    assert kwargs["exchange"] == ""
    assert kwargs["routing_key"] == "image_jobs"

    payload = json.loads(kwargs["body"])
    assert payload["job_id"] == "job-123"

def test_close_closes_connection():
    conn = MagicMock()
    conn.is_closed = False

    publisher = RabbitMQPublisher()
    publisher.connection = conn

    publisher.close()

    conn.close.assert_called_once()