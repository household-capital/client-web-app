resource "aws_security_group" "db_sg" {
  name        = "${local.full_name}-db"
  description = "Client App DB security group - ${var.instance}"
  vpc_id      = data.aws_vpc.main.id

  # Inbound
  ingress {
    protocol        = "tcp"
    from_port       = 5432
    to_port         = 5432
    cidr_blocks     = []
    security_groups = [aws_security_group.web_sg.id]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound
  egress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { "Name" = "${local.full_name}-db" })
}

resource "aws_security_group" "elastic_cache" {
  name        = "${local.full_name}-ec"
  description = "Client App EC group - ${var.instance}"
  vpc_id      = data.aws_vpc.main.id

  # Inbound
  ingress {
    protocol        = "tcp"
    from_port       = var.cache_port
    to_port         = var.cache_port
    cidr_blocks     = []
    security_groups = [aws_security_group.web_sg.id]
  }

  # Outbound
  egress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { "Name" = "${local.full_name}-ec" })
}

resource "aws_security_group" "web_sg" {
  name        = "${local.full_name}-web"
  description = "Client App Web security group - ${var.instance}"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    protocol    = "icmp"
    from_port   = -1
    to_port     = -1
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 8000
    to_port     = 8000
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { "Name" = "${local.full_name}-web" })
}
