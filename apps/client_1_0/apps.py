# Django Imports
from django.apps import AppConfig


class LandingConfig(AppConfig):
    name = 'client_1.0'


# APP NOTES

# This app provides a client interface guiding the client through a Household Loan and
# capturing choices and consents in the Loan model (Client extension in Case.Models)
# The pdf rendering required separate templates which need to maintained in addition to GUI templates

# Views:
# - there are multiple views for rendering information and capturing choices
# - navigation is provided via a menu bard fixed at the bottom of views
# - rendering is achieved using templates and forms plus some javascript

# The app:
# - entry is via the Case app (only)
# - databases all Loan (client and model setting) data
# - requires consents and objective confirmations
# - validates the loan through the process (Loan Validation)
# - provides projections (Loan Projections)
# - produces a pdf summary which is rendered by a third-party API and stored in the model
# - renders the pdf summary and emails the pdf

# Dependencies
# - the app has no model - it utilises Case.Models
# - utilises Api2Pdf to render the Summary document using UID (using headless Chrome)
# - utilises Sendgrid for email
