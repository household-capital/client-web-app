resource "aws_iam_instance_profile" "elb_profile" {
  name = "elb_profile-${var.environment}-${var.instance}-client-app"
  role = aws_iam_role.elb.name
}

resource "aws_iam_policy" "cloudwatchpolicy" {
  name        = "ec2-cloud-watch-policy-${var.environment}-${var.instance}"
  path        = "/"
  description = "IAM policy for cloudwatch"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "cloudwatch:PutMetricData",
        "ec2:DescribeTags"
      ],
      "Effect": "Allow",
      "Resource": [
        "*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role" "elb" {
  name = "${var.environment}-${var.instance}-elb-ec2-role-client-app"

  assume_role_policy = <<EOF
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "elb-cloudwatch" {
  role       = aws_iam_role.elb.name
  policy_arn = aws_iam_policy.cloudwatchpolicy.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-ebweb" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.AWSElasticBeanstalkWebTier.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-s3" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.AmazonS3FullAccess.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-docker" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.AWSElasticBeanstalkMulticontainerDocker.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-worker" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.AWSElasticBeanstalkWorkerTier.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-secrets" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.SecretsManagerReadWrite.arn
}

resource "aws_iam_role_policy_attachment" "ses-attach-policy" {
  role       = aws_iam_role.elb.name
  policy_arn = data.aws_iam_policy.AmazonSESFullAccess.arn
}
