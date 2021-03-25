#Django Imports
from django.apps import AppConfig

# Application registration - must also be included in SETTINGS list of applications
class LandingConfig(AppConfig):
    name = 'apps.enquiry'

    def ready(self):
        import apps.enquiry.signals


# APP NOTES
# This app managers the 'enquiry' workflow - including customer email communication - based on the original Eligibility app

# The app:
# - creates a queue list of all calculator interactions where the client has left their email
# - allows the user to selects ownership of calculator items
# - creates an enquiry object and emails a summary of the interaction (pdf) to the client using a client-friendly template
# - allows the user to enters basic information on an enquiry detail view
# - enables a client friendly summary email and document (similar to the calculator collateral) can be sent to the client
# - enable a more basic enquiry summary to be sent to the user.
# - enables a case to be created from an enquiry.
# - lists all enquiries (from all sources).  Users can search and then navigate to the relevant enquiry detail page
# - Future use - will provide enquiry/queue functionality for other lead sources (e.g., third parties)

#The main views are:
# - a ListView of existing enquiries
# - a Calculator Queue ListView
# - a DetailView of an individual enquiry (new or existing)

# The model:
# - Enquiry Model - cut down version of the Case model (stand-alone)

# Dependencies:
# - templates - split into Calculator, Document and Email folders
# - utilises the LoanValidation class (lib) for validation including postcode.csv
# - utilises the Enum class for model choicefield enumeration (lib)
# - utilises the pdf generation and send functions (lib)
# - uses Crispy Forms
# - uses custom tags (case_tags)




