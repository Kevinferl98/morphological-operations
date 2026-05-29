import pytest
import json
from unittest.mock import MagicMock
from app.services.redis_client import RedisClient

@pytest.fixture
def mock_redis_backend():
    return MagicMock()

@pytest.fixture
def redis_client(mock_redis_backend):
    return RedisClient(redis_instance=mock_redis_backend)

def test_create_job_successfully_stores_serialized_json(redis_client, mock_redis_backend):
    job_key = "job:123",
    job_data = {"status": "pending"}
    expected_ttl = 3600

    redis_client.create_job(job_key, job_data)

    mock_redis_backend.set.assert_called_once_with(
        job_key,
        json.dumps(job_data),
        ex=expected_ttl
    )

def test_get_job_returns_raw_bytes_when_key_exists(redis_client, mock_redis_backend):
    job_key = "job:123"
    mock_redis_backend.get.return_value = b'{"status": "done"}'

    result = redis_client.get_job(job_key)

    assert result == b'{"status": "done"}'
    mock_redis_backend.get.assert_called_once_with(job_key)

def test_get_job_returns_none_when_key_does_not_exist(redis_client, mock_redis_backend):
    job_key = "job:missing"
    mock_redis_backend.get.return_value = None

    result = redis_client.get_job(job_key)

    assert result is None
    mock_redis_backend.get.assert_called_once_with(job_key)