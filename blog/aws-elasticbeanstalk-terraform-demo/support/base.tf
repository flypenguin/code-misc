terraform {
  backend "local" {
    path = ".terraform/terraform.tfstate"
  }
}

provider "archive" {}

provider "aws" {
  region = "eu-central-1"
}
