import pytest
from unittest.mock import MagicMock
from app.services.minio_client import MinioClient
from botocore.exceptions import ClientError

TEST_BUCKET = "test-bucket"

@pytest.fixture
def mock_boto_s3_client():
    return MagicMock()

@pytest.fixture
def minio_client(mock_boto_s3_client):
    return MinioClient(client=mock_boto_s3_client, bucket_name=TEST_BUCKET)

def test_generate_presigned_upload_url_success(minio_client, mock_boto_s3_client):
    mock_boto_s3_client.generate_presigned_url.return_value = "https://upload-url.local"

    result = minio_client.generate_presigned_upload_url("image.png", expires_in=1800)

    assert result == "https://upload-url.local"
    mock_boto_s3_client.generate_presigned_url.assert_called_once_with(
        "put_object",
        Params={"Bucket": TEST_BUCKET, "Key": "image.png"},
        ExpiresIn=1800
    )

def test_generate_presigned_download_url_success(minio_client, mock_boto_s3_client):
    mock_boto_s3_client.generate_presigned_url.return_value = "https://download-url.local"

    result = minio_client.generate_presigned_download_url("result.png", expires_in=3600)

    assert result == "https://download-url.local"

    mock_boto_s3_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={
            "Bucket": TEST_BUCKET,
            "Key": "result.png"
        },
        ExpiresIn=3600
    )

def test_head_object_success_when_object_exists(minio_client, mock_boto_s3_client):
    mock_boto_s3_client.head_object.return_value = {"ContentLength": 100}

    minio_client.head_object("existing.png")
    mock_boto_s3_client.head_object.assert_called_once_with(Bucket=TEST_BUCKET, Key="existing.png")

def test_head_object_raises_client_error_when_missing(minio_client, mock_boto_s3_client):
    error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
    mock_boto_s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")

    with pytest.raises(ClientError):
        minio_client.head_object("missing.png")