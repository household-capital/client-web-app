

#########################################################
#                                                       #
#                     ROUTE53 Record                    #
#                                                       #
#########################################################

resource "aws_route53_record" "www" {
  name    = var.web_domain
  zone_id = data.aws_route53_zone.route53zone.zone_id
  type    = "A"
  alias {
    name    = "${aws_elastic_beanstalk_environment.hhc_client_app.cname}"
    zone_id = "${data.aws_elastic_beanstalk_hosted_zone.current.id}"
    evaluate_target_health = true 
  }
}


#########################################################
#                                                       #
#                         BUCKET                        #
#                                                       #
#########################################################
resource "aws_s3_bucket" "bucket" {
    bucket = "hhc-client-app-${var.environment}"
    force_destroy = var.nuke_s3
}

resource "aws_s3_bucket" "bucket_static" {
    bucket = "hhc-client-app-static-${var.environment}"
    force_destroy = var.nuke_s3
    acl    = "public-read"
    cors_rule {
        allowed_headers = ["Authorization"]
        allowed_methods = ["GET", "HEAD"]
        allowed_origins = [
          "https://${var.web_domain}.${var.route53_name}*", # annoyingly aws bucket name is passed to env so cant directly use record_name53 attribute here
          "https://www.householdcapital.app*",
          "https://householdcapital.app*"
        ]
        max_age_seconds = 3000
  }
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
                        "https://${var.web_domain}.${var.route53_name}*",
                        "https://www.${var.web_domain}.${var.route53_name}*",
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
}

#########################################################
#                                                       #
#                         EB                            #
#                                                       #
#########################################################
resource "aws_elastic_beanstalk_environment" "hhc_client_app" {
  name                = "${var.environment}-HHC-client-app"
  application         = data.aws_elastic_beanstalk_application.hhc_client_app.name
  solution_stack_name = "64bit Amazon Linux 2018.03 v2.9.15 running Python 3.6"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "InstanceType"
    value = "t3.small" # t3.small
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "IamInstanceProfile"
    value = aws_iam_instance_profile.elb_profile.name
  }
  setting {
     name      = "EC2KeyName"
     namespace = "aws:autoscaling:launchconfiguration"
     value     = var.ec2_keypair_name
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "REDIS_ENDPOINT"
    value = join(
        ", ", 
        [for node in aws_elasticache_cluster.redis_cache.cache_nodes:join(":", [node.address, node.port])]
    )
  } # use terraform for loop
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "RDS_DATABASE"
    value = "${aws_db_instance.rds_env_instance.name}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "S3_BUCKET"
    value = "${aws_s3_bucket.bucket.bucket}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "S3_BUCKET_STATIC"
    value = "${aws_s3_bucket.bucket_static.bucket}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "RDS_HOSTNAME"
    value = "${aws_db_instance.rds_env_instance.address}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "RDS_PORT"
    value = "${aws_db_instance.rds_env_instance.port}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "STORAGE"
    value = "AWS"
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "ENV"
    value = var.environment
  }
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name = "AWS_DEPLOY_PROFILE"
    value = var.profile
  }
  setting {
    namespace = "aws:ec2:vpc"
    name = "AssociatePublicIpAddress"
    value = true
  }

  setting { # ec2 scaling group
    namespace = "aws:ec2:vpc"
    name = "Subnets"
    value = join(", ", data.aws_subnet_ids.public.ids)
    # value = "subnet-0b339b651c1ecff89"
  }
  
  setting { # load balancer
    namespace = "aws:ec2:vpc"
    name = "ELBSubnets"
    # value = join(", ", data.aws_subnet_ids.storage.ids)
    value = join(", ", data.aws_subnet_ids.public.ids)
  }

  setting { 
    namespace = "aws:ec2:vpc"
    name = "VPCId"
    value = data.aws_vpc.main.id
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "SecurityGroups"
    value = aws_security_group.web_sg.id
  }
  setting {
    namespace = "aws:elb:policies"
    name = "ConnectionSettingIdleTimeout"
    value = 600
  }

  setting {
    namespace = "aws:elb:listener:443"
    name = "SSLCertificateId"
    value = data.aws_acm_certificate.ssl_cert.arn
  }
  setting {
    namespace = "aws:elb:listener:443"
    name = "ListenerProtocol"
    value = "HTTPS"
  }
  setting {
    namespace = "aws:elb:listener:443"
    name = "InstancePort"
    value = 80
  }

  # single instance 
  setting {
    namespace = "aws:autoscaling:asg"
    name = "MinSize"
    value = 1
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name = "MaxSize"
    value = 1
  }

}
# current terraform support for eb env and eb versions cannot be linked using any resources available
# only possible through the aws cli.
resource "null_resource" "update-elb-env-with-code" {
  triggers = {
    always_run = "${timestamp()}"
  }
  provisioner "local-exec" {
    command = "aws elasticbeanstalk update-environment --profile ${var.profile} --region ap-southeast-2 --application-name ${data.aws_elastic_beanstalk_application.hhc_client_app.name} --version-label ${aws_elastic_beanstalk_application_version.default.name} --environment-name ${aws_elastic_beanstalk_environment.hhc_client_app.name}"
  }
  depends_on = [aws_elastic_beanstalk_environment.hhc_client_app]
}

resource "aws_elastic_beanstalk_application_version" "default" {
  name        = "hhcclientapp-${var.environment}-${uuid()}"
  application = data.aws_elastic_beanstalk_application.hhc_client_app.name
  description = "application version created by terraform"
  bucket      = "${aws_s3_bucket.bucket.id}"
  key         = "${aws_s3_bucket_object.deployment_package.id}"
}
