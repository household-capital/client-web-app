provider "aws" {
    profile = var.profile
    region = "ap-southeast-2"
}

terraform {
  backend "s3" {}
}