provider "aws" {
    profile = "default"
    region = "ap-southeast-2"
}

terraform {
  backend "s3" {}
}