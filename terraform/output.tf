output "app_name" {
  value = data.aws_elastic_beanstalk_application.hhc_client_app.name
}

output "app_ver" {
  value = aws_elastic_beanstalk_application_version.default.name
}

output "env_name" {
  value = aws_elastic_beanstalk_environment.hhc_client_app.name
}
