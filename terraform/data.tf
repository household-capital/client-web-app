data "aws_elastic_beanstalk_application" "hhc_client_app" {
  name = "Client-App-Test"
}

data "aws_iam_policy" "AWSElasticBeanstalkWebTier" {
  arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

data "aws_iam_policy" "AmazonS3FullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

data "aws_iam_policy" "AWSElasticBeanstalkMulticontainerDocker" {
  arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker"
}

data "aws_iam_policy" "AWSElasticBeanstalkWorkerTier" {
  arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier"
}

data "aws_iam_policy" "SecretsManagerReadWrite" {
  arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

data "aws_iam_policy" "AmazonSESFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
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

data "aws_acm_certificate" "ssl_cert" {
  domain   = "*.${var.route53_name}"
  statuses = ["ISSUED"]
}
