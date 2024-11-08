resource "aws_elasticache_cluster" "redis_cache" {
  cluster_id           = local.full_name
  engine               = "redis"
  node_type            = var.cache_node_type
  num_cache_nodes      = 1 # 1 in redis 
  parameter_group_name = "default.redis5.0"
  engine_version       = "5.0.6"
  port                 = var.cache_port

  security_group_ids = [aws_security_group.elastic_cache.id]
  subnet_group_name  = aws_elasticache_subnet_group.ec_subnet_group.name # "public"

  tags = merge(local.common_tags, { "Name" = local.full_name })
}

resource "aws_elasticache_subnet_group" "ec_subnet_group" {
  name        = local.full_name
  subnet_ids  = data.aws_subnet_ids.public.ids
  description = "Elastic cache subnet group ${var.instance}"

  tags = merge(local.common_tags, { "Name" = local.full_name })
}
