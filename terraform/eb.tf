#########################################################
#                                                       #
#                     ROUTE53 Record                    #
#                                                       #
#########################################################
resource "aws_route53_record" "www" {
  name    = "${var.web_domain != "" ? var.web_domain : local.full_name}.${data.aws_ssm_parameter.public_hosted_zone_name.value}"
  zone_id = data.aws_ssm_parameter.public_hosted_zone_id.value
  type    = "A"
  alias {
    name                   = aws_elastic_beanstalk_environment.hhc_client_app.cname
    zone_id                = data.aws_elastic_beanstalk_hosted_zone.current.id
    evaluate_target_health = true
  }
}


#########################################################
#                                                       #
#                         BUCKET                        #
#                                                       #
#########################################################
resource "aws_s3_bucket" "bucket" {
  bucket        = "hhc-${local.full_name}-${var.environment}"
  force_destroy = var.nuke_s3

  tags = local.common_tags
}

resource "aws_s3_bucket" "bucket_static" {
  bucket        = "hhc-${local.full_name}-${var.environment}-static"
  force_destroy = var.nuke_s3
  acl           = "public-read"
  cors_rule {
    allowed_headers = ["Authorization"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = [
      "https://${var.web_domain != "" ? var.web_domain : local.full_name}.${data.aws_ssm_parameter.public_hosted_zone_name.value}*",
      "https://www.householdcapital.app*",
      "https://householdcapital.app*"
    ]
    max_age_seconds = 3000
  }

  tags = local.common_tags
}

resource "aws_s3_bucket_policy" "s3_bucket_policy_static_media" {
  bucket = aws_s3_bucket.bucket_static.bucket

  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::${aws_s3_bucket.bucket_static.bucket}/static/*"
            ],
            "Principal":"*",
            "Condition": {
                "StringLike": {
                    "aws:Referer": [
                        "https://${var.web_domain != "" ? var.web_domain : local.full_name}.${data.aws_ssm_parameter.public_hosted_zone_name.value}*",
                        "https://www.${var.web_domain != "" ? var.web_domain : local.full_name}.${data.aws_ssm_parameter.public_hosted_zone_name.value}*",
                        "https://www.householdcapital.app*",
                        "https://householdcapital.app*"
                    ]
                }
            }
        },
         {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${aws_s3_bucket.bucket_static.bucket}/media/profileImages/*"
        }
    ]
}
POLICY
}

resource "aws_s3_bucket_object" "deployment_package" {
  bucket = aws_s3_bucket.bucket.id
  key    = "package/package-${timestamp()}.zip"
  source = "../package.zip"

  tags = local.common_tags
}

#########################################################
#                                                       #
#                         EB                            #
#                                                       #
#########################################################
resource "aws_elastic_beanstalk_environment" "hhc_client_app" {
  name                = local.full_name
  application         = data.aws_elastic_beanstalk_application.hhc_client_app.name
  solution_stack_name = "64bit Amazon Linux 2018.03 v2.10.4 running Python 3.6"
  version_label       = aws_elastic_beanstalk_application_version.default.name

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = var.instance_type
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.elb_profile.name
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "REDIS_ENDPOINT"
    value = join(
      ", ",
      [for node in aws_elasticache_cluster.redis_cache.cache_nodes : join(":", [node.address, node.port])]
    )
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "RDS_DATABASE"
    value     = aws_db_instance.rds_env_instance.name
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "S3_BUCKET"
    value     = aws_s3_bucket.bucket.bucket
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "S3_BUCKET_STATIC"
    value     = aws_s3_bucket.bucket_static.bucket
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "RDS_HOSTNAME"
    value     = aws_db_instance.rds_env_instance.address
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "RDS_PORT"
    value     = aws_db_instance.rds_env_instance.port
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "STORAGE"
    value     = "AWS"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "ENV"
    value     = var.environment
  }
  setting {
    namespace = "aws:ec2:vpc"
    name      = "AssociatePublicIpAddress"
    value     = true
  }

  setting { # ec2 scaling group
    namespace = "aws:ec2:vpc"
    name      = "Subnets"
    value     = join(", ", data.aws_subnet_ids.public.ids)
  }

  setting { # load balancer
    namespace = "aws:ec2:vpc"
    name      = "ELBSubnets"
    value     = join(", ", data.aws_subnet_ids.public.ids)
  }

  setting {
    namespace = "aws:ec2:vpc"
    name      = "VPCId"
    value     = data.aws_vpc.main.id
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "SecurityGroups"
    value     = aws_security_group.web_sg.id
  }
  setting {
    namespace = "aws:elb:policies"
    name      = "ConnectionSettingIdleTimeout"
    value     = 600
  }

  setting {
    namespace = "aws:elb:listener:443"
    name      = "SSLCertificateId"
    value     = data.aws_ssm_parameter.cert_arn.value
  }
  setting {
    namespace = "aws:elb:listener:443"
    name      = "ListenerProtocol"
    value     = "HTTPS"
  }
  setting {
    namespace = "aws:elb:listener:443"
    name      = "InstancePort"
    value     = 80
  }

  # single instance 
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = 1
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = 1
  }

  depends_on = [aws_elastic_beanstalk_application_version.default]

  tags = merge(local.common_tags, { "Name" = local.full_name })
}

resource "aws_elastic_beanstalk_application_version" "default" {
  name        = "${local.full_name}-${uuid()}"
  application = data.aws_elastic_beanstalk_application.hhc_client_app.name
  description = "application version created by terraform"
  bucket      = aws_s3_bucket.bucket.id
  key         = aws_s3_bucket_object.deployment_package.id

  tags = merge(local.common_tags, { "Name" = "${local.full_name}-${uuid()}" })
}
