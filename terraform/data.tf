data "aws_elastic_beanstalk_application" "hhc_client_app" {
  name        = "HHC-Client-App"
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
  secret_id = "${data.aws_secretsmanager_secret.db_creds.id}"
}




data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["${var.vpc_name}"]       # insert value here
  }
}

data "aws_subnet_ids" "web" {
  vpc_id = data.aws_vpc.selected.id
  filter {
    name   = "tag:Layer"
    values = ["Web"]
  }
}

data "aws_subnet_ids" "storage" {
  vpc_id = data.aws_vpc.selected.id
  filter {
    name   = "tag:Layer"
    values = ["Storage"]
  }
}

