import pytest
import json
import pika
from unittest.mock import MagicMock
from app.services.rabbitmq_publisher import RabbitMQPublisher

TEST_URL = "amqp://test-broker:5672/"
TEST_QUEUE = "test_image_jobs"

@pytest.fixture
def mock_channel():
    return MagicMock()

@pytest.fixture
def mock_connection(mock_channel):
    conn = MagicMock()
    conn.channel.return_value = mock_channel
    conn.is_closed = False
    return conn

@pytest.fixture
def mock_connection_factory(mock_connection):
    return MagicMock(return_value=mock_connection)

@pytest.fixture
def publisher(mock_connection_factory):
    return RabbitMQPublisher(
        amqp_url=TEST_URL,
        queue_name=TEST_QUEUE,
        connection_factory=mock_connection_factory
    )

def test_ensure_connection_establishes_new_connection_if_none(publisher, mock_connection_factory, mock_connection):
    publisher._ensure_connection()

    mock_connection_factory.assert_called_once()
    mock_connection.channel.assert_called_once()
    assert publisher.connection == mock_connection

def test_ensure_connection_reconnects_if_connection_is_closed(publisher, mock_connection_factory, mock_connection):
    old_connection = MagicMock()
    old_connection.is_closed = True
    publisher.connection = old_connection

    publisher._ensure_connection()

    mock_connection_factory.assert_called_once()
    assert publisher.connection == mock_connection

def test_ensure_connection_reuses_active_connection(publisher, mock_connection_factory, mock_connection):
    publisher.connection = mock_connection
    publisher.channel = MagicMock()

    publisher._ensure_connection()

    mock_connection_factory.assert_not_called()
    mock_connection.channel.assert_not_called()

def test_publish_job_successfully_sends_persistent_json_message(publisher, mock_channel):
    job_id = "job-123"
    expected_body = json.dumps({"job_id": job_id})

    publisher.publish_job(job_id)

    mock_channel.basic_publish.assert_called_once_with(
        exchange="",
        routing_key=TEST_QUEUE,
        body=expected_body,
        properties=pika.BasicProperties(delivery_mode=2)
    )

def test_close_safely_terminates_active_connection(publisher, mock_connection):
    publisher.connection = mock_connection
    mock_connection.is_closed = False

    publisher.close()

    mock_connection.close.assert_called_once()

def test_close_does_nothing_if_connection_already_closed(publisher, mock_connection):
    publisher.connection = mock_connection
    mock_connection.is_closed = True

    publisher.close()

    mock_connection.close.assert_not_called()