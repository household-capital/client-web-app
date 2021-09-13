variable "function" {
  description = "Name of the business function"
  type        = string
}

variable "application" {
  description = "Name of the application"
  type        = string
}

variable "instance" {
  description = "Name of the application instance"
  type        = string
}

variable "nuke_s3" {
  type        = bool
  description = "Flag to whether s3 should be force deleted"
  default     = false
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "n_shards" {
  type        = number
  description = "Number of shards for cluster"
  default     = 2
}

variable "replica_nodes" {
  type        = number
  description = "Number of replica nodes in a shard"
  default     = 1
}

variable "cache_port" {
  type        = number
  description = "Port of elasticache"
  default     = 6379 # redis port
}

variable "cache_node_type" {
  type        = string
  description = "Cache node type"
  default     = "cache.t3.medium"
}

variable "web_domain" {
  type        = string
  description = "Webdomain"
  default     = ""
}

variable "instance_type" {
  type        = string
  description = "Instance type"
  default     = "t3.small"
}
