locals {
  bucket_name = "${var.project_prefix}-${var.bucket_name}"
}


resource "aws_kms_key" "this" {
  description = "terraform state encryption key"
}


# from here:
# https://jessicagreben.medium.com/how-to-terraform-locking-state-in-s3-2dc9a5665cb6

# terraform state file setup
# create an S3 bucket to store the state file in
resource "aws_s3_bucket" "this" {
  bucket = local.bucket_name

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "S3 Remote Terraform State Store"
  }
}


resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}


resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.this.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.this.arn
      sse_algorithm     = "aws:kms"
    }
  }
}


resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
  ignore_public_acls      = true
}


# create a dynamodb table for locking the state file
resource "aws_dynamodb_table" "this" {
  name           = var.dynamo_db_lock_table_name
  hash_key       = "LockID"
  read_capacity  = 20
  write_capacity = 20

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "DynamoDB Terraform State Lock Table"
  }
}


resource "local_file" "backend_tf" {
  content = templatefile("backend.tf.tmpl", {
    full_bucket_name          = local.bucket_name
    state_file_name           = var.state_file_name
    dynamo_db_lock_table_name = var.dynamo_db_lock_table_name
    aws_region                = var.aws_region
  })
  filename        = "${path.module}/backend.tf"
  file_permission = "0644"
}
