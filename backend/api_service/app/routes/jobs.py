import logging
from fastapi import APIRouter, Depends, status
from app.schemas.job import UploadUrlResponse, JobCreateResponse, JobCreateRequest, JobStatusResponse
from app.dependencies import get_job_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Image Processing Jobs"])

@router.get(
    "/upload_url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Request image upload URL"
)
def get_upload_url(job_service = Depends(get_job_service)):
    url, filename = job_service.generate_upload_params()
    return UploadUrlResponse(upload_url=url, image_key=filename)

@router.post(
    "/",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new processing job",
    responses={
        400: {"description": "The requested image_key was not found."},
        422: {"description": "Payload validation failed."}
    }
)
def create_job(job_create: JobCreateRequest, job_service = Depends(get_job_service)):
    job_id = job_service.create_job(
        image_key=job_create.image_key,
        params=job_create.params
    )
    return JobCreateResponse(job_id=job_id)

@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch current job details",
    responses={
        404: {"description": "The requested Job ID does not exist"},
        422: {"description": "Invalid Job ID format."}
    }
)
def get_job(job_id: str, job_service = Depends(get_job_service)):
    job = job_service.get_job(job_id)
    return JobStatusResponse.from_job(job)