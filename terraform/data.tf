data "aws_elastic_beanstalk_application" "hhc_client_app" {
  name = "Client-App-Test"
}

data "aws_secretsmanager_secret" "db_creds" {
  name = "${var.environment}/clientapp/db-cred"
}

data "aws_secretsmanager_secret_version" "db_creds" {
  secret_id = data.aws_secretsmanager_secret.db_creds.id
}

data "aws_vpc" "main" {
  state = "available"
  tags = {
    Name = "aws-controltower-VPC"
  }
}

data "aws_subnet_ids" "public" {
  vpc_id = data.aws_vpc.main.id
  tags = {
    Network = "Public"
  }
}
data "aws_subnet_ids" "private" {
  vpc_id = data.aws_vpc.main.id
  tags = {
    Network = "Private"
  }
}
data "aws_subnet_ids" "restricted" {
  vpc_id = data.aws_vpc.main.id
  tags = {
    Network = "Restricted"
  }
}

data "aws_elastic_beanstalk_hosted_zone" "current" {}

data "aws_route53_zone" "route53zone" {
  name = var.route53_name
}

data "aws_ssm_parameter" "cert_arn" {
  name = "/infra/wildcart-cert-arn"
}
