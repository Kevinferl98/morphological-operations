variable "aws_region" {
  type = string
  default = "us-east-1"
  description = "AWS region"
}

variable "minio_access_key" {
  type = string
  sensitive = true
  description = "MinIO access key"
}

variable "minio_secret_key" {
  type = string
  sensitive = true
  description = "MinIO secret key"
}

variable "minio_endpoint" {
  type        = string
  description = "MinIO endpoint"
  default     = "http://localhost:9000"
}

variable "minio_bucket_name" {
  type        = string
  description = "Bucket name to create"
  default     = "images"
}

variable "project_name" {
  type = string
  default = "morphological-operations"
  description = "Project name used for tags"
}

variable "environment" {
  type = string
  default = "dev"
}