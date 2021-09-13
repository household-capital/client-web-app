"""
Purpose:

- Expose the enquiry and case input screens to specific partners (as set up in User Model)
- Allow partners to log in, enter enquiries or cases (depending on profile) and view a list
  of outstanding items
- Users are validated and are creating actual Enquiries and Cases, but have restricted access
- This was more experimental / POC and hasn't been used extensively
"""


from django.apps import AppConfig

class ReferrerConfig(AppConfig):
    name = 'referrer'
