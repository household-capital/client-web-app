#Django Imports
from django.apps import AppConfig

# Application registration - must also be included in SETTINGS list of applications
class LandingConfig(AppConfig):
    name = 'case'


# APP NOTES

# This app provides case (lead and opportunity) management for the Household Distribution Team
# It is a simple ListView-DetailView set-up and provides the entry point to the Client Interface

# There main views are:
# - a ListView of existing cases (leads and opportunities)
# - a DetailView of an individual case (new or existing)
# - a case close Detail View to capture additional items when a case is closed
# - (currently) two views related to the webCalculator

# The app:
# - databases all case information (see model)
# - enables required information for the client meeting (including images) to be saved
# - captures relevant client information and validates based on inputs
# - provides navigation to the Client App (from the detail view)
# - enables cases to be closed, capturing additional information

# The model:
# - the entire client model is contained within the case app and shared with other apps (client app)
# - the model consists of:
#   - Case (the main client model) and three one-to-one (extended) models:
#     - Loan (loan details)
#     - Model Settings (economic details)
#     - Loss Data (additional loss information)
# - there is an additional FundDetails model that is used to capture fund images

# Dependencies:
# - templates - styling extends Site base templates
# - three main templates caseList, caseDetail, caseLoss
# - custom CSS
# - utilises the LoanValidation class (lib) for validation including postcode.csv
# - utilises the Enum class for model choicefield enumeration (lib)
# - significant use of Crispy Forms
# - utilises the pdf generation and send functions (lib)
# - uses custom tags (case_tags)


