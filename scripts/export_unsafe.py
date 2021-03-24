from apps.case.models import Case
from apps.enquiry.models import Enquiry
from apps.lib.hhc_LoanValidator import LoanValidator



'''
exclude:
any enquiry where it or it's duplicates:
1) have a "do not market"
2) fail a soft eligibility check...
3) were marked as inelligible in stage/status field
4) are in a bad "stage" or actioned

scp 'ec2-user@3.106.126.206:*.csv' .
'''



def bucket_up(enquiries):
    i = 1
    buckets = {}
    
    for e in enquiries:
        found_buckets = []
        for id, bucket in buckets.items():
            if (e.email and (e.email.lower() in bucket['emails'])) or (e.phoneNumber and (e.phoneNumber in bucket['phones'])):
                found_buckets.append(id)
        
        i = new_id = i + 1
        emails = set([e.email.lower()]) if e.email else set()
        phones = set([e.phoneNumber]) if e.phoneNumber else set()
        enquiries = [e]

        if found_buckets:
            for old_id in found_buckets:
                old_bucket = buckets.pop(old_id)
                emails.update(old_bucket['emails'])
                phones.update(old_bucket['phones'])
                enquiries.extend(old_bucket['enquiries'])
        
        new_bucket = {
            'emails' : emails,
            'phones': phones,
            'enquiries' : enquiries,
        }
        
        buckets[new_id] = new_bucket
    
    return list(buckets.values())


def write_file(name, buckets):
    with open(name, 'w', newline='') as csvfile:
        for bucket in buckets:
            done = []
            for e in bucket['enquiries']:
                if (e.email and (e.email not in done)):
                    done.append(e.email)
                    csvfile.write(e.email + "\n")


def is_DNM(enquiry):
    cases = Case.objects.filter(enqUID=enquiry.enqUID).all()
    if len(cases):
        return any([case.lossdata.doNotMarket for case in cases])
    else:
        return enquiry.doNotMarket


def do_not_market(buckets):
    write_file('donotmarket.csv', [
        x for x in buckets
        if any([is_DNM(e) for e in x['enquiries']])
    ])


def has_basic_data(enquiry):
    data = enquiry.__dict__

    postcode = data.get('postcode')
    age_1 = data.get('age_1')

    if not postcode:
        return False

    if not age_1:
        return False

    return True


def validate_basic(enquiry):
    '''
    if not enough data, try soft check that 60+ and live in eligible postcode
    else do full eligibility check
    '''

    data = enquiry.__dict__
    validator = LoanValidator(data)

    postcode = data.get('postcode')
    age_1 = data.get('age_1')
    age_2 = data.get('age_2')

    if postcode:
        pcode_status = validator.checkPostcode(postcode)
        if pcode_status == "Refer":
            if not enquiry.referPostcodeStatus:
                return False
        elif pcode_status != "Valid":
            return False

    if age_1 and (age_1 < 60):
        return False

    if age_2 and (age_2 < 60):
        return False

    return True


def validate_full(enquiry):
    '''
    if not enough data, try soft check that 60+ and live in eligible postcode
    else do full eligibility check
    '''

    data = enquiry.__dict__
    validator = LoanValidator(data)
    validation = validator.validateLoan()

    return (validation['status'] == 'Ok') or (validation.get('responseText') == 'Insufficient data')


def inelligible_missing_basic_data(buckets):
    write_file('inelligible_missing_basic_data.csv', [
        x for x in buckets
        if not all([has_basic_data(e) for e in x['enquiries']])
    ])


def inelligible_failed_basic(buckets):
    write_file('inelligible_failed_basic.csv', [
        x for x in buckets
        if not all([validate_basic(e) for e in x['enquiries']])
    ])


def inelligible_failed_full(buckets):
    write_file('inelligible_failed_full.csv', [
        x for x in buckets
        if not all([validate_full(e) for e in x['enquiries']])
    ])


def inelligible_status(buckets):
    write_file('inelligible_status.csv', [
        x for x in buckets
        if any([e.enquiryStage == 9 for e in x['enquiries']])
    ])

GOOD_STAGES = [
    1, # GENERAL_INFORMATION
    2, # BROCHURE_SENT
    3, # SUMMARY_SENT
    7, # DUPLICATE
    8, # FUTURE_CALL
    9, # DID_NOT_QUALIFY
    11, # FOLLOW_UP_NO_ANSWER
    12, # FOLLOW_UP_VOICEMAIL
    13, # INITIAL_NO_ANSWER
    14, # NVN_EMAIL_SENT
    15, # MORE_TIME_TO_THINK
]

BAD_STAGES = [
    4, # DISCOVERY_MEETING
    5, # LOAN_INTERVIEW
    6, # LIVE_TRANSFER
    10, # NOT_PROCEEDING
]


def bad_stage(buckets):
    write_file('bad_stage.csv', [
        x for x in buckets
        if any([
            (e.enquiryStage in BAD_STAGES) or (e.actioned == -1)
            for e in x['enquiries']])
    ])


def run():
    all_enquiries = Enquiry.objects.all()
    asd = bucket_up(all_enquiries)
    do_not_market(asd)
    inelligible_missing_basic_data(asd)
    inelligible_failed_basic(asd)
    inelligible_failed_full(asd)
    inelligible_status(asd)
    bad_stage(asd)

run()


