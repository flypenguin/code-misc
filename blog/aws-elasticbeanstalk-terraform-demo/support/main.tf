resource "aws_s3_bucket" "ebs_test_config_bucket" {
  # ENTER YOUR BUCKET NAME HERE.
  bucket = "${var.bucket_name}"
}
