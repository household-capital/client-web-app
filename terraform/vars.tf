variable nuke_s3 {
  type = bool
  description = "Flag to whether s3 should be force deleted"
  default = false
}

variable "environment" {
  type = string
  description = "Environment name"
}

variable "ec2_keypair_name" {
  type = string
  description = "EC2 Key pair name"
}

# variable "storage_subnet_group" {
#   type = string
#   description = "RDS subnet storage group"
# }

variable "n_shards" {
  type = number
  description = "Number of shards for cluster"
}

variable "replica_nodes" {
  type = number
  description = "Number of replica nodes in a shard"
}

variable "cache_port" {
  type = number
  description = "Port of elasticache"
  default = 6379 # redis port
}

variable "cache_node_type" {
  type = string
  description = "Cache node type"
  default = "cache.t3.medium" 
}

variable "profile" {
  type = string 
  description = "AWS Acc to use to deploy"
  default = "devel"
}

variable "web_domain" {
  type = string
  description = "Webdomain"
}

variable "route53_name" {
  type = string
  description = "Route53 Hosted Zone Name"
}