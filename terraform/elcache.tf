
resource "aws_elasticache_cluster" "redis_cache" {
  cluster_id           = "${var.environment}-clientapp-cluster"
  engine               = "redis"
  node_type            = var.cache_node_type 
  num_cache_nodes      = 1 # 1 in redis 
  parameter_group_name = "default.redis5.0"
  engine_version       = "5.0.6"
  port                 = var.cache_port
  security_group_ids = [
    aws_security_group.elastic_cache.id
  ]
  subnet_group_name = "public"
  tags = {
    Name = "Client-App-Cache"
  } 
}
