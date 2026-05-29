import pytest
from fastapi.testclient import TestClient
from unittest.mock import create_autospec
from app.exceptions import BadRequestError, NotFoundError
from app.main import app
from app.dependencies import get_job_service
from app.schemas.job import MorphologicalParams
from app.services.job_service import JobService

@pytest.fixture
def job_service_mock():
    return create_autospec(JobService, instance=True)

@pytest.fixture
def client(job_service_mock):
    app.dependency_overrides[get_job_service] = lambda: job_service_mock

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def test_get_upload_url_success(client, job_service_mock):
    job_service_mock.generate_upload_params.return_value = ("http://upload-url", "image.png")

    response = client.get("/jobs/upload_url")

    assert response.status_code == 200
    assert response.json() == {
        "upload_url": "http://upload-url",
        "image_key": "image.png"
    }
    job_service_mock.generate_upload_params.assert_called_once()

def test_create_job_success(client, job_service_mock):
    job_service_mock.create_job.return_value = "job-123"
    params = {
        "operation": "dilate",
        "shape": "rect",
        "sizeX": 3,
        "sizeY": 3
    }
    payload = {
        "image_key": "image.png",
        "params": params
    }

    response = client.post("/jobs/", json=payload)

    assert response.status_code == 202
    assert response.json() == {"job_id": "job-123"}

    job_service_mock.create_job.assert_called_once_with(
        image_key="image.png",
        params=MorphologicalParams(operation="dilate", shape="rect", sizeX=3, sizeY=3)
    )

def test_create_job_raises_400_if_image_key_missing_in_storage(client, job_service_mock):
    job_service_mock.create_job.side_effect = BadRequestError("Uploaded image not found")
    payload = {
        "image_key": "missing.png",
        "params": {"operation": "dilate", "shape": "rect", "sizeX": 3, "sizeY": 3}
    }

    response = client.post("/jobs/", json=payload)

    assert response.status_code == 400
    assert "Uploaded image not found" in response.text

def test_create_job_raises_422_on_invalid_payload_validation(client):
    invalid_payload = {}

    response = client.post("/jobs/", json=invalid_payload)

    assert response.status_code == 422

def test_get_job_success(client, job_service_mock):
    job_service_mock.get_job.return_value = {
        "status": "done",
        "image_key": "image.png",
        "result_url": "http://download",
    }

    response = client.get("/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert response.json()["result_url"] == "http://download"
    job_service_mock.get_job.assert_called_once_with("job-123")

def test_get_job_raises_404_if_job_id_does_not_exist(client, job_service_mock):
    job_service_mock.get_job.side_effect = NotFoundError("Job job-404 not found")

    response = client.get("/jobs/job-404")

    assert response.status_code == 404
    assert "Job job-404 not found" in response.text