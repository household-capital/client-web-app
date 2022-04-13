import datetime, logging, json, traceback, re
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # <-- Here

from apps.calculator.models import WebCalculator, WebContact
from apps.enquiry.util import updateCreatePartnerEnquiry, assign_enquiry_leads
from apps.lib.site_Utilities import cleanPhoneNumber, cleanValuation, calcAge, parse_api_names, raiseTaskAdminError
from apps.lib.site_Enums import (
    marketingTypesEnum, 
    directTypesEnum, 
    stateTypesEnum, 
    productTypesEnum,
    propensityChoicesReverseDict,
    marketingReferrerDict,
    enquiryStagesEnum,
    dwellingTypesEnum,
    loanTypesEnum,
    caseStagesEnum,
    PRE_MEETING_STAGES,
    purposeCategoryEnum,
    purposeIntentionEnum,
    clientSexEnum
)
from apps.lib.site_Logging import write_applog
from apps.enquiry.exceptions import MissingRequiredFields
from apps.enquiry.util import find_auto_campaign
from apps.case.assignment import _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP
from apps.settings.models import GlobalSettings
from apps.calculator.util import convert_calc, ProcessingError
from apps.case.assignment import find_auto_assignee, auto_assign_leads, assign_lead
from apps.enquiry.models import Enquiry
from apps.case.models import LoanPurposes
from config.celery import app 

logger = logging.getLogger('myApps')

REQUIRED_FIELDS = [
    'last',
    'postcode',
    'grading',
    'stream'
]

OR_FIELDS = [
    'phone',
    'email'
]

WEB_SOURCES = [
    "WEBSITE_LEAD", 
    "WEBSITE_CALC", 
    "WEBSITE_CONTACT",
    "WEBSITE_PRE_QUAL" ,
    "WEB_VISA"   
]

class DataIngestion(APIView):
    permission_classes = (IsAuthenticated,)            
    
    def process_notes(self, json_payload): 
        write_applog(
            "INFO",
            "Enquiry API",
            "Process Payload", 
            "API Ingestion - Processing Notes"
        )
        marketing_source_value = json_payload['stream']
        is_social = marketing_source_value in [
            'LINKEDIN',
            'FACEBOOK',
            'FACEBOOK_INTERACTIVE',
            'FACEBOOK_CALCULATOR',
            'FACEBOOK_VISA'
        ]
        upload_type = 'SOCIAL' if is_social else 'PARTNER'
        enquiryString = "[# Updated from {} Upload #]".format(upload_type)
        enquiryString += "\r\n{}: {}".format(upload_type, marketing_source_value)
        enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
        if json_payload.get('origin_timestamp'):
            enquiryString += "\r\nCreate Date: {}".format(json_payload.get('origin_timestamp'))
        if json_payload.get('dob'):
            enquiryString += "\r\nCustomer Date of birth: {}".format(
                datetime.datetime.strptime(
                    json_payload.get('dob'),
                    '%m/%d/%Y'
                ).strftime('%d/%m/%Y')
            )
        if is_social: 
            if json_payload.get('month_of_birth', ''):
                enquiryString += "\r\nMonth of Birth: {}".format(
                    json_payload.get('month_of_birth', '')
                )
            if json_payload.get('age_status', ''):
                enquiryString += "\r\nYear of Birth: {}".format(
                    json_payload.get('age_status', '')
                )
            if json_payload.get('age_over_60'):
                enquiryString += "\r\nOver 60?: {}".format(
                    json_payload.get('age_over_60')
                )
            if json_payload.get('property_range'):
                enquiryString += "\r\nValuation: {}".format(
                    json_payload.get('property_range')
                )
        return enquiryString

    def process_website_entry(self, json_payload): 
        write_applog(
            "INFO",
            "Enquiry API",
            "Process Payload", 
            "API Ingestion - Website entry"
        )
        """
            contact form 
            {
                email: "rosy@rosytown.com.au",
                first: "Mark",
                grading: "A",
                last: "Rosendorff",
                phone: "0400000000",
                postcode: "3000",
                stream: "WEBSITE_CONTACT",
                uuid: "be59832d-6978-4cfa-bcf4-91a3d37c6feb"
            }
            {
                'first': 'asdasd', 
                'last': 'adasd', 
                'age_1': '66', 
                'phone': '0422880871',
                'email': 'frg5@g.com', 
                'postcode': '2460', 
                'grading': 'A', 
                'stream': 'WEBSITE_CONTACT', 
                'origin': 'contact | Contact Us', 
                'requestedCall': 0
            }


            gated resource
            {
                email: "rosy@rosytown.com.au",
                first: "Mark",
                grading: "A",
                last: "Rosendorff",
                phone: "0400000000",
                postcode: "3000",
                stream: "WEBSITE_LEAD",
                uuid: "be59832d-6978-4cfa-bcf4-91a3d37c6feb"
            }
            Calc widgets
            {
                'first': 'asdasd', 
                'last': 'asdasd', 
                'age1': 77, 
                'age2': 88, 
                'phone': '232323', 
                'email': 'asas@asas.com', 
                'postcode': 3000, 
                'property_type': 'house', 
                'property_value': 789000, 
                'marital_status': 'couple', 
                'grading': 'A', 
                'stream': 'WEBSITE_CALC', 
                'origin': 'home | Home Equity Calculator', 
                'requestedCall': 1,
                'utm_source': 'yourlifechoices',
                'utm_medium': 'web',
                'utm_campaign': 'website'
            }

        """
        marketing_source_value = json_payload['stream']
        propensity = propensityChoicesReverseDict.get(json_payload.get('grading'))
        if marketing_source_value == 'WEBSITE_CONTACT': 
            write_applog(
                "INFO",
                "Enquiry API",
                "Process Payload", 
                "API Ingestion - Webcontact"
            )
            # contact us 
            first , last, raw_name = parse_api_names(
                '' or json_payload['first'],
                '' or json_payload['last']
            )
            srcDict = {
                'firstname': first,
                'lastname': last,
                'origin_timestamp': datetime.datetime.utcnow(),
                'raw_name': raw_name,
                'email': json_payload['email'],
                'postcode': json_payload['postcode'],
                'message': json_payload['message'],
                'age_1': json_payload['age_1'],
                'submissionOrigin': json_payload['origin'],
                'origin_id': json_payload.get('origin_id'),
                'phone': cleanPhoneNumber(json_payload['phone']),
                'utm_source': json_payload.get('utm_source'),
                'utm_medium': json_payload.get('utm_medium'),
                'utm_campaign': json_payload.get('utm_campaign'),
            }

            web_obj = WebContact.objects.create(**srcDict)
            
        elif marketing_source_value == 'WEBSITE_LEAD':
            write_applog(
                "INFO",
                "Enquiry API",
                "Process Payload", 
                "API Ingestion - web lead"
            )
            first , last, raw_name = parse_api_names(
                '' or json_payload['first'],
                '' or json_payload['last']
            )
            enquiryNotes = '[# Website Enquiry #]'
            enquiryNotes += '\r\n' + json_payload['origin']
            if json_payload.get('what_describes_you'): 
                enquiryNotes += '\r\nDescription: ' + json_payload['what_describes_you']
            if json_payload.get('description') is not None:
                enquiryNotes += '\r\n' + 'Description: {}'.format(json_payload['description'])

            srcData = {
                'firstname': first,
                'lastname': last,
                'email': json_payload.get('email'),
                'age_1': json_payload['age_1'],
                'phoneNumber': cleanPhoneNumber(json_payload['phone']),
                'origin_timestamp': timezone.localtime(),
                
                'referrer': directTypesEnum.WEB_ENQUIRY.value,
                'enquiryStage': enquiryStagesEnum.BROCHURE_SENT.value,
                'enquiryNotes': enquiryNotes,
                'origin_id': json_payload.get('origin_id'),
                'submissionOrigin': json_payload['origin'],
                'propensityCategory': propensity,
                'utm_source': json_payload.get('utm_source'),
                'utm_medium': json_payload.get('utm_medium'),
                'utm_campaign': json_payload.get('utm_campaign'),
            }

            if json_payload.get('utm_source'):
                enquiryNotes += '\r\nutm_source: ' + json_payload['utm_source']
                srcData['enquiryNotes'] = enquiryNotes

                utm_source_to_marketing_source = {
                    'nationalseniors': marketingTypesEnum.NATIONAL_SENIORS.value,
                    'yourlifechoices': marketingTypesEnum.YOUR_LIFE_CHOICES.value,
                    'startsat60': marketingTypesEnum.STARTS_AT_60.value,
                }
                for utm_source_value, marketing_value in utm_source_to_marketing_source.items():
                    if utm_source_value == json_payload['utm_source']:
                        srcData['marketingSource'] = marketing_value

            try:
                web_obj = Enquiry.objects.create(**srcData)
            except:
                raise raiseTaskAdminError('Could not save "web enquiry" entry', json.dumps(srcData, cls=DjangoJSONEncoder))

        elif marketing_source_value == 'WEBSITE_PRE_QUAL':
            self.process_pre_qual(json_payload)
        elif marketing_source_value == 'WEB_VISA': 
            write_applog(
                "INFO",
                "Enquiry API",
                "Process Payload", 
                "API Ingestion - web visa"
            )
            first , last, raw_name = parse_api_names(
                '' or json_payload['first'],
                '' or json_payload['last']
            )
            enquiryNotes = '[# Website Enquiry #]'
            if json_payload.get('origin'):
                enquiryNotes += '\r\n' + json_payload['origin']
            if json_payload.get('description') is not None:
                enquiryNotes += '\r\n' + 'Description: {}'.format(json_payload['description'])
            srcData = {
                'firstname': first,
                'lastname': last,
                'email': json_payload.get('email'),
                'origin_timestamp': timezone.localtime(),
                'referrer': directTypesEnum.WEB_ENQUIRY.value,
                'enquiryStage': enquiryStagesEnum.GENERAL_INFORMATION.value,
                'enquiryNotes': enquiryNotes,
                'marketingSource':marketingTypesEnum.VISA.value,
                'origin_id': json_payload.get('origin_id'),
                'submissionOrigin': json_payload.get('origin'),
                'propensityCategory': propensity,
                'utm_source': json_payload.get('utm_source'),
                'utm_medium': json_payload.get('utm_medium'),
                'utm_campaign': json_payload.get('utm_campaign'),
            }
            if json_payload.get('phone'):
                srcData['phoneNumber'] = cleanPhoneNumber(json_payload['phone'])

            try:
                web_obj = Enquiry.objects.create(**srcData)
            except:
                raise raiseTaskAdminError('Could not save "web enquiry" entry', json.dumps(srcData, cls=DjangoJSONEncoder))

        else: 
            # build web_calc obj
            write_applog(
                "INFO",
                "Enquiry API",
                "Process Payload", 
                "API Ingestion - web calc"
            )
            first , last, raw_name = parse_api_names(
                '' or json_payload['first'],
                '' or json_payload['last']
            )
            is_couple = json_payload['marital_status'] == 'couple'
            if is_couple: 
                loan_type = loanTypesEnum.JOINT_BORROWER.value
            else: 
                loan_type = loanTypesEnum.SINGLE_BORROWER.value
            if json_payload['property_type'].lower() == 'house':
                prop_type = dwellingTypesEnum.HOUSE.value
            else: 
                prop_type = dwellingTypesEnum.APARTMENT.value
            
            srcDict = {
                'phoneNumber': cleanPhoneNumber(json_payload['phone']),
                'origin_timestamp': timezone.localtime(),
                'firstname': first,
                'lastname': last,
                'raw_name': raw_name,
                'age_1': json_payload['age_1'],
                'age_2': json_payload.get('age_2') if is_couple else None,
                'email': json_payload['email'],
                'productType': json_payload.get(
                    'productType', 
                    productTypesEnum.LUMP_SUM.value
                ),
                'streetAddress':json_payload.get('property_address'),
                'base_specificity': json_payload.get('unit'),
                'street_number': json_payload.get('street_number'),
                'street_name': json_payload.get('street_name'),
                "street_type": json_payload.get('street_type'),
                'suburb': json_payload.get('suburb'),
                'state': stateTypesEnum[json_payload.get('state')].value if json_payload.get('state') else None,
                'postcode': json_payload['postcode'],
                'valuation':json_payload['property_value'],
                'submissionOrigin': json_payload['origin'],
                'requestedCallback': bool(json_payload['requestedCall']),
                'dwellingType':prop_type  ,
                'origin_id': json_payload.get('origin_id'),
                'loanType': loan_type,
                'utm_source': json_payload.get('utm_source'),
                'utm_medium': json_payload.get('utm_medium'),
                'utm_campaign': json_payload.get('utm_campaign'),
            }
            try:
                web_obj = WebCalculator.objects.create(**srcDict)
            except BaseException as e:
                write_applog(
                    "ERROR",
                    "Enquiry API",
                    "Webcalc", 
                    "Could not save calculator entry"
                )
                raiseTaskAdminError("Could not save calculator entry", json.dumps(srcDict, cls=DjangoJSONEncoder))
                raise e
            proposed_owner = find_auto_assignee(
                referrer=directTypesEnum.WEB_CALCULATOR.value, email=web_obj.email, phoneNumber=web_obj.phoneNumber
            )
            if proposed_owner:
                try:
                    convert_calc(web_obj, proposed_owner)
                except Exception as e:
                    tb = traceback.format_exc()
                    raiseTaskAdminError(
                        "Failed to convert web calc - {}".format(str(web_obj.calcUID)),
                        tb
                    )

    def send_prequal_email(self, lead_obj):
        return False
    
    def process_pre_qual(self, json_payload):
        write_applog(
            "INFO",
            "Enquiry API",
            "Process Payload", 
            "API Ingestion - web pre qual lead"
        )
        first , last, raw_name = parse_api_names(
            '' or json_payload['first'],
            '' or json_payload['last']
        )
        enquiryNotes = '[# Website Enquiry #]'
        enquiryNotes += '\r\n' + json_payload['origin']
        if json_payload.get('description') is not None:
            enquiryNotes += '\r\n' + 'Description: {}'.format(json_payload['description'])
        is_couple = json_payload['marital_status'] == 'couple'
        if is_couple: 
            loan_type = loanTypesEnum.JOINT_BORROWER.value
        else: 
            loan_type = loanTypesEnum.SINGLE_BORROWER.value
       
        if json_payload['property_type'].lower() == 'house':
            prop_type = dwellingTypesEnum.HOUSE.value
        else: 
            prop_type = dwellingTypesEnum.APARTMENT.value
        
        srcDict = {
            'phoneNumber': cleanPhoneNumber(json_payload['phone']),
            'origin_timestamp': timezone.localtime(),
            'firstname': first,
            'lastname': last,
            'age_1': json_payload['age_1'],
            'age_2': json_payload.get('age_2') if is_couple else None,
            'email': json_payload['email'],
            'productType': json_payload.get(
                'productType', 
                productTypesEnum.LUMP_SUM.value
            ),
            'postcode': json_payload['postcode'],
            'valuation':json_payload['property_value'],
            'submissionOrigin': json_payload['origin'],
            'requestedCallback': json_payload.get('requestedCall', False),
            'dwellingType':prop_type ,
            'loanType': loan_type ,
            'referrer': directTypesEnum.WEB_PREQUAL.value,

            'streetAddress':json_payload.get('property_address'),
            'base_specificity': json_payload.get('unit'),
            'street_number': json_payload.get('street_number'),
            'street_name': json_payload.get('street_name'),
            "street_type": json_payload.get('street_type'),
            'suburb': json_payload.get('suburb'),
            'state': stateTypesEnum[json_payload.get('state')].value if json_payload.get('state') else None,
            'postcode': int(json_payload['postcode']) if json_payload.get('postcode') else None,
            'mortgageDebt': json_payload['mortgage'],
            'origin_id': json_payload.get('origin_id'),
            'propensityCategory':propensityChoicesReverseDict.get(json_payload.get('grading')),
            'utm_source': json_payload.get('utm_source'),
            'utm_medium': json_payload.get('utm_medium'),
            'utm_campaign': json_payload.get('utm_campaign'),
            'calcCare': json_payload.get('care'),
            'calcGive' : json_payload.get('give'),
            'calcLive': json_payload.get('live'),
            'calcTopUp': json_payload.get('top_up'),
            'calcRefi': json_payload.get('refinance')

        }
        enquiry_fields_captured = [
            'first',
            'last',
            'age_1',
            'age_2',
            'phone',
            'email',
            'property_address',
            'unit',
            'street_number',
            'street_name',
            'street_type',
            'suburb',
            'state',
            'postcode',
            'country',
            'property_type',
            'property_value',
            'property_owing',
            'mortgage',
            'stream',
            'grading',
            'origin',
            'utm_source',
            'utm_medium',
            'utm_campaign',
        ]
        head_doc = {
            x:y 
            for x,y in json_payload.items()
            if x not in enquiry_fields_captured
        }
        calc_list = ['calcCare','calcGive', 'calcLive', 'calcTopUp', 'calcRefi']
        srcDict['calcTotal'] = 0
        for purpose in calc_list:
            if srcDict.get(purpose):
                srcDict['calcTotal'] += srcDict.get(purpose)

        srcDict['head_doc'] = head_doc
        enquiry = Enquiry.objects.create(**srcDict)
        lead = enquiry.case
        if is_couple: 
            lead.firstname_2 = json_payload['first_2']
            lead.surname_2 = json_payload['last_2']
        lead_captured_fields = enquiry_fields_captured + [
            'first_2',
            'last_2',
            'top_up',
            'refinance',
            'live',
            'give',
            'care',
            'gender_1',
            'gender_2'
        ]
        if json_payload.get('gender_1'):
            lead.sex_1 = clientSexEnum.MALE.value if json_payload['gender_1'].lower() == 'male' else clientSexEnum.FEMALE.value
        if json_payload.get('gender_2'):
            lead.sex_2 = clientSexEnum.MALE.value if json_payload['gender_2'].lower() == 'male' else clientSexEnum.FEMALE.value
        
        lead.head_doc = {
            x:y 
            for x,y in json_payload.items()
            if x not in lead_captured_fields
        }
        in_pre_meet = caseStagesEnum(lead.caseStage).name in PRE_MEETING_STAGES
        lead.superAmount = json_payload.get('superannuation', 0)
        lead.pensionAmount = json_payload.get('pension', 0)
        if in_pre_meet:
            lead.caseStage = caseStagesEnum.SQ_PRE_QUAL.value

        lead.save()

        proposed_owner = find_auto_assignee(
            referrer=directTypesEnum.WEB_PREQUAL.value, 
            email=enquiry.email, 
            phoneNumber=enquiry.phoneNumber
        )
        
        if proposed_owner is None:
            auto_assign_leads([lead], notify=False)
        else:
            assign_lead(lead, proposed_owner, notify=False)
        
        lead.refresh_from_db()
        enquiry.user = lead.owner
        enquiry.save(should_sync=True)

        # send email?
        loan = lead.loan
        if in_pre_meet: 
            if json_payload.get('top_up'):
                amount = json_payload['top_up']
                lp, _ = LoanPurposes.objects.get_or_create(
                    loan=loan,
                    category=purposeCategoryEnum.TOP_UP.value,
                    intention=purposeIntentionEnum.INVESTMENT.value
                )
                lp.amount = amount
                lp.save()
            if json_payload.get('refinance'):
                amount = json_payload['refinance']
                lp, _ = LoanPurposes.objects.get_or_create(
                        loan=loan,
                        category=purposeCategoryEnum.REFINANCE.value,
                        intention=purposeIntentionEnum.MORTGAGE.value
                    )
                lp.amount = amount
                lp.save()
            if json_payload.get('live'):
                amount = json_payload['live']
                lp, _ = LoanPurposes.objects.get_or_create(
                        loan=loan,
                        category=purposeCategoryEnum.LIVE.value,
                        intention=purposeIntentionEnum.RENOVATIONS.value
                    )
                lp.amount = amount
                lp.save()

            if json_payload.get('give'):
                amount = json_payload['give']
                lp, _ = LoanPurposes.objects.get_or_create(
                        loan=loan,
                        category=purposeCategoryEnum.GIVE.value,
                        intention=purposeIntentionEnum.GIVE_TO_FAMILY.value
                    )
                lp.amount = amount
                lp.save()

            if json_payload.get('care'):
                amount = json_payload['care']
                lp, _ = LoanPurposes.objects.get_or_create(
                        loan=loan,
                        category=purposeCategoryEnum.CARE.value,
                        intention=purposeIntentionEnum.LUMP_SUM.value
                    )
                lp.amount = amount
                lp.save()
        if lead.owner and self.send_prequal_email(lead): 
            app.send_task(
                'Webcalc_gen_and_email_pre_ql',
                kwargs={
                    'caseUID': lead.caseUID
                }
            )


    def process_payload(self, json_payload):
        # basic payload format 
        """
            Lead ingestion basic payload structure 
            {
                "first": "Name",
                "last": "Surname",
                "phone": "0298765432",
                "mobile": "0401234567",
                "email": "user@email.com",
                "unit": "1",
                "street_number": "123",
                "street_name": "Main",
                "street_type": "St",
                "suburb": "Sydney",
                "state": "NSW",
                "postcode": 2000,
                "country": "Australia",
                "dob": "01/01/1970",
                "property_type": "strata",
                "property_value": 1000000,
                "property_owing": 200000,
                "marital_status": "single",
                "notes": "wanting to borrow about $200k in the next couple of months",
                "appointment": "1/02/2021 9:00 AM",
                "specialist": "Chris Moutzikis",
                "referred_by": "Luke Sharam",
                "postcode_type": True,
                "grading": "A",
                "stream" : "YOUR_LIFE_CHOICES",
                "origin" : "web page X",
                "origin_timestamp": "????????????????",
                "origin_id": "ASDASD-1ASDQ23-ZXCZCZ-1231",
            }
        """
        for req_field in REQUIRED_FIELDS: 
            if json_payload.get(req_field) is None: 
                raise MissingRequiredFields('Missing field: \'{}\''.format(req_field))
        meets_or_fields = any( 
            json_payload.get(req_field) 
            for req_field in OR_FIELDS
        )
        if not meets_or_fields:
            raise MissingRequiredFields('Missing OR field(s): \'{}\''.format(' or '.join(OR_FIELDS)))


        marketing_source_value = json_payload['stream']
        write_applog(
            "INFO",
            "Enquiry API",
            "API", 
            "API Ingestion - {}".format(marketing_source_value)
        )
        if marketing_source_value in WEB_SOURCES:
            self.process_website_entry(json_payload)
        else:
            write_applog(
                "INFO",
                "Enquiry API",
                "WebAPI", 
                "API Ingestion - Non website entry"
            )
            marketingSource = marketingTypesEnum[marketing_source_value].value
            
            firstname, lastname, name = parse_api_names(json_payload.get('first'), json_payload.get('last'))
            global_settings = GlobalSettings.load()

            payload = {
                'firstname': firstname,
                'lastname': lastname,
                #'phoneNumber': cleanPhoneNumber(json_payload['phone']),
                'postcode': json_payload.get('postcode'),
                'propensityCategory': propensityChoicesReverseDict.get(json_payload.get('grading')),
                'marketingSource': marketingSource,
                'email': json_payload.get('email'),
                'valuation':  cleanValuation(json_payload.get('property_value')),
                'age_1': calcAge(json_payload.get('dob')),
                'productType': productTypesEnum.LUMP_SUM.value,
                'referrer': directTypesEnum[marketingReferrerDict.get(marketing_source_value, "OTHER")].value,
                'base_specificity': json_payload.get('unit'),
                'street_number': json_payload.get('street_number'),
                'street_name': json_payload.get('street_name'),
                'street_type': json_payload.get('street_type'),
                'submissionOrigin': json_payload.get('origin'),
                #'origin_timestamp': json_payload.get('origin_timestamp'),
                'origin_id': json_payload.get('origin_id'),
                # 'user': integration_user,
                'marketing_campaign': find_auto_campaign(marketingSource),
                'utm_source': json_payload.get('utm_source'),
                'utm_medium': json_payload.get('utm_medium'),
                'utm_campaign': json_payload.get('utm_campaign'),
            }
            if json_payload.get('phone'):
                payload['phoneNumber'] = cleanPhoneNumber(json_payload['phone'])
            auto_assign_config = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP.get(marketingSource)
            if json_payload.get('state'): 
                payload['state'] = stateTypesEnum[json_payload['state']].value

            payload['enquiryNotes'] = self.process_notes(json_payload)
            if json_payload.get('notes'):
                payload['enquiryNotes'] += '\n' + json_payload.get('notes')

            enquiries_to_assign = []
            updateCreatePartnerEnquiry(payload, enquiries_to_assign)
            assign_enquiry_leads(enquiries_to_assign, force=True)

    def post(self, request):
        content = {'status': 'Success'}
        status = 200 
        json_payload = request.data
        write_applog(
            "INFO",
            "Enquiry API",
            "EnqAPI", 
            'API Ingestion Hit - Payload {}'.format(json.dumps(json_payload, cls=DjangoJSONEncoder))
        )
        try:
            self.process_payload(json_payload)
        except BaseException as e:
            tb = traceback.format_exc()

            raiseTaskAdminError(
                "API Ingestion Error",
                "{}\n\n\npayload={}".format(tb, json.dumps(json_payload))
            )
            logger.exception("Ingestion Error")
            
            if type(e) is MissingRequiredFields:
                content = {
                    'status': str(e)
                }
                status = 400 
            else: 
                status = 500 
                content = {
                    'status': 'Server error'
                }
        return Response(content, status=status)