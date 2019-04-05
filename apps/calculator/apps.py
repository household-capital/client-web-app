#Django Imports
from django.apps import AppConfig

# Application registration - must also be included in SETTINGS list of applications
class CalculatoryConfig(AppConfig):
    name = 'calculator'

# APP NOTES

# NOTE - this application is currently called from an external iFrame and clickjacking and csrf protections have been
# overriden using decorators in the View

# This app provides an Household Loan calculator to be used on Household Capital's website. The calculator
# seeks to capture the user's email for lead generation purposes

# There are two views:
# - an input page which captures basic details in order to confirm enquiry; and
# - an output page which renders results and seeks to capture the user's email

# The calculator:
# - databases all post information (regardless of whether email provided)
# - the record is updated on the output page
# - has a single data model (WebCalculator)
# - passes a UID parameter to navigate to the output page
# - renders each form manually (not using form or crispy form} to achieve GUI effects
# - main GUI main effect was to replace check box and radio buttons with images (via css)
# - captures the HTTP referrer as a hidden input to the form
# - redirects based on the HTTP referrer

# Dependencies:
# - two views and two templates
# - custom CSS
# - static HHC icon images (including transfer images)
# - utilises the LoanValidation class (lib) for validation including postcode.csv
# - utilises the Enum class for model choicefield enumeration
