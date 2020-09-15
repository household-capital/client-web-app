resource "aws_security_group" "db_sg" {
  name        = "clientapp-db-security-${var.environment}"
  description = "Client App Terraform DB security group - ${var.environment}"
  vpc_id      = data.aws_vpc.main.id

  tags = {
    Name = "clientapp-database-${var.environment}"
  }

  # Inbound
  ingress {
    protocol        = "tcp"
    from_port       = 5432	
    to_port         = 5432	
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
}


resource "aws_security_group" "elastic_cache" {
  name        = "clientapp-ec-${var.environment}"
  description = "Client App Terraform DB ec group - ${var.environment}"
  vpc_id      = data.aws_vpc.main.id

  tags = {
    Name = "clientapp-database-${var.environment}"
  }

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
}


resource "aws_security_group" "web_sg" {
  name        = "clientapp-web-security-${var.environment}"
  description = "Client App Terraform EC2 security group - ${var.environment}"
  vpc_id      = data.aws_vpc.main.id

  tags = {
    Name = "clientapp-web-security-${var.environment}"
  }

  ingress { # SSH access
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = ["0.0.0.0/0"]
  }

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
}