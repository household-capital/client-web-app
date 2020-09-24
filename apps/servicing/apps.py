"""
Purpose
 - to prototype initial servicing functionality
 - provides a range of servicing functionality using a Facility model, which is built from SF Loan Object data
 - key client facing functionality includes additional drawdown and annual review (one-time link access)
 - key internal functionality includes creating loan variations

 Most functionality is expected to be migrated to Salesforce.

 It will be important to be able to continue to create Loan Variations (with data sourced
 from Salesforce Loan Objects)
"""

from django.apps import AppConfig


class ServicingConfig(AppConfig):
    name = 'servicing'




