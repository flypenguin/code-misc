locals {
  bucket_name = "${project_prefix}-terraform-states"
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

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  # encryption we want ...
  server_side_encryption_configuration {
    rule {
      bucket_key_enabled = false

      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.this.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }

  tags = {
    Name = "S3 Remote Terraform State Store"
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
  name           = "terraform-state-lock"
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
