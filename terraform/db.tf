resource "aws_db_instance" "rds_env_instance" {

  # lifecycle {
  #   prevent_destroy = true
  # }

  deletion_protection    = (var.environment == "prod") 
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "12.4"
  instance_class         = "db.t3.small"
  storage_encrypted      = true
  name                   = "clientapp${var.environment}"
  username               = jsondecode(data.aws_secretsmanager_secret_version.db_creds.secret_string)["Username"]
  password               = jsondecode(data.aws_secretsmanager_secret_version.db_creds.secret_string)["Password"]
  parameter_group_name   = "default.postgres12"
  vpc_security_group_ids = [aws_security_group.db_sg.id]   # Security Group
  # db_subnet_group_name   = var.storage_subnet_group  # Subnet Group
  db_subnet_group_name =  aws_db_subnet_group.db_subnet_group.id # "awseb-e-mdegjcpmbn-stack-awsebrdsdbsubnetgroup-tgen5assryx2"
  multi_az               = true
  identifier             = "clientapp-db-${var.environment}"
  publicly_accessible    = var.environment != "prod" 

  # RDS Maintenance (1:00am - 3:00am AEDT Monday nights)
  maintenance_window          = "Sun:14:00-Sun:16:00" # UTC
  allow_major_version_upgrade = false
  auto_minor_version_upgrade  = true
  apply_immediately           = true

  # Automatic Backups (3:00am to 6:00am AEDT Every day) 
  backup_window               = "16:00-19:00" # must be outside maintenance window.
  skip_final_snapshot         = true
  backup_retention_period     = var.environment == "andrew" ? 35 : 0 # !!!!!!! change to prod when working
}

resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "clientapp-db-subnet-group-${var.environment}"
  subnet_ids = data.aws_subnet_ids.public.ids

  tags =  { "Name" = "clientapp-db-subnet-group-${var.environment}" }
}