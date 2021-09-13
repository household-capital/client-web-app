"""
**Purpose**
    * online customer journey and application form process

**Approach**
    * entry point from website calculator
    * api creates application object and returns encoded url for the website redirect
    * application journey commenced on redirect
    * uses SMS 2FA to resume and sign application

**Key journey components**
    * login details (resume application link sent)
    * personal details
    * product details
    * projections (emails Loan Summary)
    * application information
    * declarations and signing (sms pin)
    * next steps email
    * document loading functionality

.. note:: Current journeys are **Income** and **Contingency 20K** only

   The two journeys share some many views, but some of the steps are omitted.  The navigation is currently hard-coded in the view logic.
   There is a differential journey and next-steps for applications that are calculated to be ``low-lvr``

"""

from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    name = 'apps.application'
