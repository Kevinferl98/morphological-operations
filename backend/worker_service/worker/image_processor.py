from worker.utils.image_io import load_image_from_bytes, encode_image
from worker.domain import morphological_operations as morph
from worker.exceptions import ValidationError, BadRequestError
from my_observability import get_logger

logger = get_logger(__name__)

def process_job_logic(job_id, redis_client, minio_client):
    job = redis_client.get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in Redis")
        return
    
    try:
        output_key = _execute_operation(
            job_id=job_id,
            image_key=job["image_key"],
            params=job["params"],
            minio_client=minio_client
        )

        job.update({
            "status": "done",
            "result_key": output_key,
            "error": None
        })
    except Exception as e:
        logger.exception(f"Processing failed for job {job_id}")
        job.update({
            "status": "error",
            "error": str(e)
        })

    redis_client.update_job(job_id, job)

def _execute_operation(job_id: str, image_key: str, params: dict, minio_client):
    image_bytes = minio_client.get_bytes(image_key)
    image = load_image_from_bytes(image_bytes)
    
    image_type = morph.classify_image_array(image)
    if image_type == morph.ImageType.UNDEFINED:
        raise ValidationError("Unsupported image type")
    
    try:
        struct_element = morph.create_structuring_element(
            params["shape"], 
            (int(params["sizeX"]), int(params["sizeY"]))
        )
        result = morph.execute_operation(
            params["operation"], image, struct_element, image_type
        )
    except KeyError as e:
        raise BadRequestError(f"Missing parameter: {e}")
        
    result_bytes = encode_image(result)
    output_key = f"jobs/{job_id}/output.png"
    minio_client.put_bytes(output_key, result_bytes)

    return output_key