terraform {
  required_version = ">= 1.15.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 6.48.0"
    }
  }
}

provider "aws" {
    region = var.aws_region
    access_key = var.minio_access_key
    secret_key = var.minio_secret_key

    skip_credentials_validation = true
    skip_metadata_api_check = true
    skip_requesting_account_id = true

    s3_use_path_style = true
    endpoints {
        s3 = var.minio_endpoint
    }
}

resource "aws_s3_bucket" "minio_media_storage" {
    bucket = var.minio_bucket_name
    
    tags = {
      Name = "${var.project_name}-${var.environment}-media-storage"
      Environment = var.environment
      Project = var.project_name
      ManagedBy = "terraform"
    }
}