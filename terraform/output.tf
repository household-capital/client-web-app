output "app_url" {
  value = "https://${aws_route53_record.www.name}"
}
