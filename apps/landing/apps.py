"""
Purpose:

- Provide a basic dashboard landing page with summary stats
    - summary data is created using timeseries queries on underlying models
    - data is passed via context
    - jquery is used to render using chartjs
- For non-Household users redirect to relevant partner/broker functionality

"""


#Django Imports
from django.apps import AppConfig


class LandingConfig(AppConfig):
    name = 'landing'

