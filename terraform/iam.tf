resource "aws_iam_instance_profile" "elb_profile" {
  name = "elb_profile-${var.environment}-${var.instance}-client-app"
  role = aws_iam_role.elb.name

  tags = merge(local.common_tags, { "Name" = "elb_profile-${var.environment}-${var.instance}-client-app" })
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

  tags = merge(local.common_tags, { "Name" = "ec2-cloud-watch-policy-${var.environment}-${var.instance}" })
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

  tags = merge(local.common_tags, { "Name" = "${var.environment}-${var.instance}-elb-ec2-role-client-app" })
}

resource "aws_iam_role_policy_attachment" "elb-cloudwatch" {
  role       = aws_iam_role.elb.name
  policy_arn = aws_iam_policy.cloudwatchpolicy.arn
}

resource "aws_iam_role_policy_attachment" "elb-attach-ebweb" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

resource "aws_iam_role_policy_attachment" "elb-attach-s3" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "elb-attach-docker" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker"
}

resource "aws_iam_role_policy_attachment" "elb-attach-worker" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier"
}

resource "aws_iam_role_policy_attachment" "elb-attach-secrets" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

resource "aws_iam_role_policy_attachment" "ses-attach-policy" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}

resource "aws_iam_role_policy_attachment" "elb-session-manager" {
  role       = aws_iam_role.elb.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
