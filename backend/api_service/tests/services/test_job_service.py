import json
import pytest
from unittest.mock import patch, create_autospec
from app.services.minio_client import MinioClient
from app.services.rabbitmq_publisher import RabbitMQPublisher
from app.services.redis_client import RedisClient
from app.services.job_service import JobService
from app.exceptions import BadRequestError, NotFoundError
from app.schemas.job import MorphologicalParams

@pytest.fixture
def redis_mock():
    return create_autospec(RedisClient, instance=True)

@pytest.fixture
def publisher_mock():
    return create_autospec(RabbitMQPublisher, instance=True)

@pytest.fixture
def minio_mock():
    return create_autospec(MinioClient, instance=True)

@pytest.fixture
def job_service(redis_mock, publisher_mock, minio_mock):
    return JobService(redis_mock, publisher_mock, minio_mock)

def test_generate_upload_params(job_service, minio_mock):
    minio_mock.generate_presigned_upload_url.return_value = "http://upload-url"

    with patch("app.services.job_service.uuid.uuid4", return_value="1234"):
        url, filename = job_service.generate_upload_params("png")
    
    assert filename == "1234.png"
    assert url == "http://upload-url"

    minio_mock.generate_presigned_upload_url.assert_called_once_with("1234.png")

def test_create_job_success(job_service, redis_mock, publisher_mock, minio_mock):
    minio_mock.head_object.return_value = None
    params = MorphologicalParams(
        operation="dilate",
        shape="rect",
        sizeX=3,
        sizeY=3
    )

    with patch("app.services.job_service.uuid.uuid4", return_value="job-123"):
        job_id = job_service.create_job("image.png", params)
    
    assert job_id == "job-123"

    redis_mock.create_job.assert_called_once()

    args, kwargs = redis_mock.create_job.call_args
    job_key, job_data = args

    assert job_key == "job:job-123"
    assert job_data["status"] == "pending"
    assert job_data["image_key"] == "image.png"
    assert job_data["params"] == params.model_dump()
    assert job_data["result"] is None

    publisher_mock.publish_job.assert_called_once_with("job-123")

def test_create_job_image_not_found(job_service, minio_mock):
    minio_mock.head_object.side_effect = Exception("not found")

    with pytest.raises(BadRequestError):
        job_service.create_job("missing.pgn", {})

def test_get_job_success(job_service, redis_mock):
    job_data = {
        "status": "pending",
        "image_key": "img.png",
        "params": {},
        "result": None,
        "error": None
    }

    redis_mock.get_job.return_value = json.dumps(job_data)

    result = job_service.get_job("123")

    assert result["status"] == "pending"

    redis_mock.get_job.assert_called_once_with("job:123")

def test_get_job_with_result(job_service, redis_mock, minio_mock):
    job_data = {
        "status": "done",
        "image_key": "img.png",
        "params": {},
        "result_key": "result.png",
        "error": None
    }

    redis_mock.get_job.return_value = json.dumps(job_data)
    minio_mock.generate_presigned_download_url.return_value = "http://download"

    result = job_service.get_job("123")

    assert result["result_url"] == "http://download"

    minio_mock.generate_presigned_download_url.assert_called_once_with("result.png")

def test_get_job_not_found(job_service, redis_mock):
    redis_mock.get_job.return_value = None

    with pytest.raises(NotFoundError) as exc:
        job_service.get_job("missing")

    assert "Job missing not found" in str(exc.value)