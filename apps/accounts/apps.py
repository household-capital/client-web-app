"""
    **Purpose**
    * extend the user model to include additional user profile information
    * extend the profile model to include third-party referrers
    * create a session log for all user authentications
    * cosmetic enhancements to standard user authentication forms

"""

#Django Imports
from django.apps import AppConfig

class ApplicatonConfig(AppConfig):
    name = 'accounts'

