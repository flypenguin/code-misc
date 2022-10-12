#
# basically, you only NEED to change this.
#

variable "project_prefix" {
  description = "a project prefix"
  default     = "i-was-too-stupid-to-change-this"
}


#
# this can be left alone.
#

variable "bucket_name" {
  default = "terraform-states"
}

variable "aws_region" {
  default = "eu-central-1"
}

variable "state_file_name" {
  default = "terraform-state-setup.tfstate"
}

variable "dynamo_db_lock_table_name" {
  default = "terraform-state-lock"
}
