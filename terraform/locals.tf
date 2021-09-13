locals {
  full_name = "${var.function}-${var.application}-${var.instance}"

  common_tags = {
    TaggingVersion = "1"
    Application    = var.application
    Product        = var.function
    Owner          = "technology"
    Data           = "none"
  }
}
