output "app_url" {
  value = nonsensitive("https://${aws_route53_record.www.name}")
}
