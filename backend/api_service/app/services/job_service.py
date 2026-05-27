import uuid
import logging
import json
from app.services.redis_client import RedisClient
from app.services.minio_client import MinioClient
from app.services.rabbitmq_publisher import RabbitMQPublisher
from app.exceptions import BadRequestError, NotFoundError
from app.schemas.job import MorphologicalParams

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, redis: RedisClient, publisher: RabbitMQPublisher, minio_client: MinioClient):
        self.redis = redis
        self.publisher = publisher
        self.minio_client = minio_client

    def generate_upload_params(self, extensions: str = "png"):
        filename = f"{uuid.uuid4()}.{extensions}"
        url = self.minio_client.generate_presigned_upload_url(filename)
        return url, filename

    def create_job(self, image_key: str, params: MorphologicalParams):
        try:
            self.minio_client.head_object(image_key)
        except Exception:
            raise BadRequestError("Uploaded image not found")

        job_id = str(uuid.uuid4())
        job_key = f"job:{job_id}"

        job_data = {
            "status": "pending",
            "image_key": image_key,
            "params": params.model_dump(),
            "result": None,
            "error": None
        }

        self.redis.create_job(job_key, job_data)
        self.publisher.publish_job(job_id)

        logger.info("Job %s created", job_id)
        return job_id

    def get_job(self, job_id):
        job_key = f"job:{job_id}"
        job_data_raw = self.redis.get_job(job_key)
        if not job_data_raw:
            raise NotFoundError(f"Job {job_id} not found")
        
        job_data = json.loads(job_data_raw)

        if job_data.get("status") == "done" and job_data.get("result_key"):
            job_data["result_url"] = self.minio_client.generate_presigned_download_url(job_data["result_key"])
        return job_data