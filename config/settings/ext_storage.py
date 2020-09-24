from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """S3 Sub-class to create specific static files storage

    All static files in this app should be referenced using static_storage

    Note: default_acl = 'public-read' is does not appear to be setting file permissions to public as expected
    The required permissions were achieved using a bucket policy on the static folder

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                "Resource": ["arn:aws:s3:::householdcapital/static/*"]
            }
        ]
    }"""

    location = settings.AWS_STATIC_LOCATION
    default_acl = 'public-read'
    querystring_auth = False



class MediaStorage(S3Boto3Storage):
    """S3 Sub-class to create media files storage

    All media files in this app should be referenced using default_storage

    All media files are served with a signed url to enable access
    """
    location = settings.AWS_MEDIA_LOCATION
    default_acl = 'private'
    querystring_auth = True





