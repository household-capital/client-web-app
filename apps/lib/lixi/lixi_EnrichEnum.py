# Python Imports
import csv
import logging
import requests
import json

# Django Imports
from django.conf import settings

# Local Application Imports
from apps.lib.api_Mappify import apiMappify


class EnrichEnum:
    ABS_LendingCodes = {"Top Up": "ABS-247", "Give": "ABS-249", "Live": "ABS-237", "Care": "ABS-249",
                        "Refinance": "ABS-133"}
    PrimaryPurpose = {"Top Up": "Investment Non Residential", "Give": "Personal", "Live": "Personal",
                      "Care": "Personal", "Refinance": "Owner Occupied"}
    CountryCodes = {'Afghanistan': 'AF', 'Åland Islands': 'AX', 'Albania': 'AL', 'Algeria': 'DZ',
                    'American Samoa': 'AS', 'Andorra': 'AD', 'Angola': 'AO', 'Anguilla': 'AI', 'Antarctica': 'AQ',
                    'Antigua and Barbuda': 'AG', 'Argentina': 'AR', 'Armenia': 'AM', 'Aruba': 'AW', 'Australia': 'AU',
                    'Austria': 'AT', 'Azerbaijan': 'AZ', 'Bahamas': 'BS', 'Bahrain': 'BH', 'Bangladesh': 'BD',
                    'Barbados': 'BB', 'Belarus': 'BY', 'Belgium': 'BE', 'Belize': 'BZ', 'Benin': 'BJ', 'Bermuda': 'BM',
                    'Bhutan': 'BT', 'Bolivia, Plurinational State of': 'BO', 'Bonaire, Sint Eustatius and Saba': 'BQ',
                    'Bosnia and Herzegovina': 'BA', 'Botswana': 'BW', 'Bouvet Island': 'BV', 'Brazil': 'BR',
                    'British Indian Ocean Territory': 'IO', 'Brunei Darussalam': 'BN', 'Bulgaria': 'BG',
                    'Burkina Faso': 'BF', 'Burundi': 'BI', 'Cambodia': 'KH', 'Cameroon': 'CM', 'Canada': 'CA',
                    'Cape Verde': 'CV', 'Cayman Islands': 'KY', 'Central African Republic': 'CF', 'Chad': 'TD',
                    'Chile': 'CL', 'China': 'CN', 'Christmas Island': 'CX', 'Cocos (Keeling) Islands': 'CC',
                    'Colombia': 'CO', 'Comoros': 'KM', 'Congo': 'CG', 'Congo, the Democratic Republic of the': 'CD',
                    'Cook Islands': 'CK', 'Costa Rica': 'CR', "Côte d'Ivoire": 'CI', 'Croatia': 'HR', 'Cuba': 'CU',
                    'Curaçao': 'CW', 'Cyprus': 'CY', 'Czech Republic': 'CZ', 'Denmark': 'DK', 'Djibouti': 'DJ',
                    'Dominica': 'DM', 'Dominican Republic': 'DO', 'Ecuador': 'EC', 'Egypt': 'EG', 'El Salvador': 'SV',
                    'Equatorial Guinea': 'GQ', 'Eritrea': 'ER', 'Estonia': 'EE', 'Ethiopia': 'ET',
                    'Falkland Islands (Malvinas)': 'FK', 'Faroe Islands': 'FO', 'Fiji': 'FJ', 'Finland': 'FI',
                    'France': 'FR', 'French Guiana': 'GF', 'French Polynesia': 'PF',
                    'French Southern Territories': 'TF', 'Gabon': 'GA', 'Gambia': 'GM', 'Georgia': 'GE',
                    'Germany': 'DE', 'Ghana': 'GH', 'Gibraltar': 'GI', 'Greece': 'GR', 'Greenland': 'GL',
                    'Grenada': 'GD', 'Guadeloupe': 'GP', 'Guam': 'GU', 'Guatemala': 'GT', 'Guernsey': 'GG',
                    'Guinea': 'GN', 'Guinea-Bissau': 'GW', 'Guyana': 'GY', 'Haiti': 'HT',
                    'Heard Island and McDonald Islands': 'HM', 'Holy See (Vatican City State)': 'VA', 'Honduras': 'HN',
                    'Hong Kong': 'HK', 'Hungary': 'HU', 'Iceland': 'IS', 'India': 'IN', 'Indonesia': 'ID',
                    'Iran, Islamic Republic of': 'IR', 'Iraq': 'IQ', 'Ireland': 'IE', 'Isle of Man': 'IM',
                    'Israel': 'IL', 'Italy': 'IT', 'Jamaica': 'JM', 'Japan': 'JP', 'Jersey': 'JE', 'Jordan': 'JO',
                    'Kazakhstan': 'KZ', 'Kenya': 'KE', 'Kiribati': 'KI', "Korea, Democratic People's Republic of": 'KP',
                    'Korea, Republic of': 'KR', 'Kuwait': 'KW', 'Kyrgyzstan': 'KG',
                    "Lao People's Democratic Republic": 'LA', 'Latvia': 'LV', 'Lebanon': 'LB', 'Lesotho': 'LS',
                    'Liberia': 'LR', 'Libya': 'LY', 'Liechtenstein': 'LI', 'Lithuania': 'LT', 'Luxembourg': 'LU',
                    'Macao': 'MO', 'Macedonia, the Former Yugoslav Republic of': 'MK', 'Madagascar': 'MG',
                    'Malawi': 'MW', 'Malaysia': 'MY', 'Maldives': 'MV', 'Mali': 'ML', 'Malta': 'MT',
                    'Marshall Islands': 'MH', 'Martinique': 'MQ', 'Mauritania': 'MR', 'Mauritius': 'MU',
                    'Mayotte': 'YT', 'Mexico': 'MX', 'Micronesia, Federated States of': 'FM',
                    'Moldova, Republic of': 'MD', 'Monaco': 'MC', 'Mongolia': 'MN', 'Montenegro': 'ME',
                    'Montserrat': 'MS', 'Morocco': 'MA', 'Mozambique': 'MZ', 'Myanmar': 'MM', 'Namibia': 'NA',
                    'Nauru': 'NR', 'Nepal': 'NP', 'Netherlands': 'NL', 'New Caledonia': 'NC', 'New Zealand': 'NZ',
                    'Nicaragua': 'NI', 'Niger': 'NE', 'Nigeria': 'NG', 'Niue': 'NU', 'Norfolk Island': 'NF',
                    'Northern Mariana Islands': 'MP', 'Norway': 'NO', 'Oman': 'OM', 'Pakistan': 'PK', 'Palau': 'PW',
                    'Palestine, State of': 'PS', 'Panama': 'PA', 'Papua New Guinea': 'PG', 'Paraguay': 'PY',
                    'Peru': 'PE', 'Philippines': 'PH', 'Pitcairn': 'PN', 'Poland': 'PL', 'Portugal': 'PT',
                    'Puerto Rico': 'PR', 'Qatar': 'QA', 'Réunion': 'RE', 'Romania': 'RO', 'Russian Federation': 'RU',
                    'Rwanda': 'RW', 'Saint Barthélemy': 'BL', 'Saint Helena, Ascension and Tristan da Cunha': 'SH',
                    'Saint Kitts and Nevis': 'KN', 'Saint Lucia': 'LC', 'Saint Martin (French part)': 'MF',
                    'Saint Pierre and Miquelon': 'PM', 'Saint Vincent and the Grenadines': 'VC', 'Samoa': 'WS',
                    'San Marino': 'SM', 'Sao Tome and Principe': 'ST', 'Saudi Arabia': 'SA', 'Senegal': 'SN',
                    'Serbia': 'RS', 'Seychelles': 'SC', 'Sierra Leone': 'SL', 'Singapore': 'SG',
                    'Sint Maarten (Dutch part)': 'SX', 'Slovakia': 'SK', 'Slovenia': 'SI', 'Solomon Islands': 'SB',
                    'Somalia': 'SO', 'South Africa': 'ZA', 'South Georgia and the South Sandwich Islands': 'GS',
                    'South Sudan': 'SS', 'Spain': 'ES', 'Sri Lanka': 'LK', 'Sudan': 'SD', 'Suriname': 'SR',
                    'Svalbard and Jan Mayen': 'SJ', 'Swaziland': 'SZ', 'Sweden': 'SE', 'Switzerland': 'CH',
                    'Syrian Arab Republic': 'SY', 'Taiwan, Province of China': 'TW', 'Tajikistan': 'TJ',
                    'Tanzania, United Republic of': 'TZ', 'Thailand': 'TH', 'Timor-Leste': 'TL', 'Togo': 'TG',
                    'Tokelau': 'TK', 'Tonga': 'TO', 'Trinidad and Tobago': 'TT', 'Tunisia': 'TN', 'Turkey': 'TR',
                    'Turkmenistan': 'TM', 'Turks and Caicos Islands': 'TC', 'Tuvalu': 'TV', 'Uganda': 'UG',
                    'Ukraine': 'UA', 'United Arab Emirates': 'AE', 'United Kingdom': 'GB', 'United States': 'US',
                    'United States Minor Outlying Islands': 'UM', 'Uruguay': 'UY', 'Uzbekistan': 'UZ', 'Vanuatu': 'VU',
                    'Venezuela, Bolivarian Republic of': 'VE', 'Viet Nam': 'VN', 'Virgin Islands, British': 'VG',
                    'Virgin Islands, U.S.': 'VI', 'Wallis and Futuna': 'WF', 'Western Sahara': 'EH', 'Yemen': 'YE',
                    'Zambia': 'ZM', 'Zimbabwe': 'ZW'}
    StateShortCode = {'Victoria': 'VIC', "New South Wales": 'NSW', "Queensland": 'QLD', "Tasmania": 'TAS',
                      "South Australia": 'SA', "Western Australia": 'WA', "Northern Territory": 'NT',
                      "Australian Capital Territory": 'ACT'}

    REMOTENESS_FILE = '/apps/lib/lixi/Remoteness/hhc_Remoteness.csv'

    def __init__(self, srcDict):
        self.loanDict = srcDict
        self.outputLog = ""

    def enrich(self):
        result = self.__propertyEnrich()
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': self.outputLog}

        result = self.__lixiEnum()
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': self.outputLog}

        return {'status': "Ok", 'data': self.loanDict}

    def __propertyEnrich(self):

        # Utilises external API to parse and enrich the address from PSMA’s G-NAF dataset (via mappify)

        self.__logging("Enriching Property Information")

        mappify = apiMappify()

        result = mappify.setAddress({"streetAddress": self.loanDict['Prop.Street_Address__c'],
                                     "suburb": self.loanDict['Prop.Suburb_City__c'],
                                     "postcode": self.loanDict['Prop.Postcode__c'],
                                     "state": self.__enumState(self.loanDict['Prop.State__c'])})

        if result['status'] != 'Ok':
            self.__logging(result['responseText'])
            return {'status': "Error"}

        result = mappify.checkPostalAddress()

        if result['status'] == 'Error':
            self.__logging(result['responseText'])
            return {'status': "Error"}

        addressDict = result["result"]

        self.loanDict['Prop.buildingName'] = str(addressDict['buildingName'])
        self.loanDict['Prop.flatNumber'] = str(addressDict['flatNumber'])
        self.loanDict['Prop.numberFirst'] = addressDict['numberFirst']
        self.loanDict['Prop.streetName'] = self.__firstCap(addressDict['streetName'])
        self.loanDict['Prop.streetType'] = self.__firstCap(addressDict['streetType'])
        self.loanDict['Prop.suburb'] = self.__firstCap(addressDict['suburb'])
        self.loanDict['Prop.gnafId'] = addressDict['gnafId']
        self.loanDict['Prop.streetAddress'] = addressDict['streetAddress']
        self.loanDict['Prop.state'] = addressDict['state']

        return {'status': "Ok"}

    def __lixiEnum(self):

        try:
            self.__logging("Enumerating LIXI Property Type")

            # remove spaces from Identifiers
            self.loanDict['Prop.Policy_Number__c']=self.loanDict['Prop.Policy_Number__c'].replace(" ","")

            firstname, surname = self.loanDict['Prop.Valuer_Name__c'].split(" ", 1)
            self.loanDict['Prop.Valuer_Firstname']=firstname
            self.loanDict['Prop.Valuer_Surname'] = surname
            self.loanDict['Prop.Valuer_Name__c']=self.loanDict['Prop.Valuer_Name__c'].replace(" ", "")

            # propertyType
            if self.loanDict['Prop.flatNumber'] != "None":
                self.loanDict['Prop.LixiPropertyType'] = 'Apartment Unit Flat'
            else:
                self.loanDict['Prop.LixiPropertyType'] = 'Fully Detached House'

            self.__logging("Enumerating LIXI ABS Purposes")
            # Purposes
            # Look up ABS and Primary Purpose using associated dictionaries
            maxval = 0

            for i in range(int(self.loanDict['Purp.NoPurposes'])):
                self.loanDict["Purp" + str(i + 1) + ".ABSCode"] = self.ABS_LendingCodes[
                    self.loanDict["Purp" + str(i + 1) + ".Category__c"]]

                if self.loanDict["Purp" + str(i + 1) + ".Amount__c"] > maxval:
                    maxval = self.loanDict["Purp" + str(i + 1) + ".Amount__c"]
                    self.loanDict["Purp.PrimaryPurpose"] = self.PrimaryPurpose[
                        self.loanDict["Purp" + str(i + 1) + ".Category__c"]]

            self.__logging("Enumerating LIXI Phone Numbers, Country Codes, Residency")

            # Phone Numbers,  Country Codes, Residency

            result = self.ContactEnumeration("Brwr")
            if result['status'] != "Ok":
                self.__logging("# Enumeration Error")
                return {'status': "Error"}

            if int(self.loanDict["POA.Number"]) > 0:
                result = self.ContactEnumeration("POA")
                if result['status'] != "Ok":
                    self.__logging("# Enumeration Error")
                    return {'status': "Error"}

            self.__logging("Enumerating LIXI Protected Equity")

            # Protected Equity
            if self.loanDict["Loan.Protected_Equity_Percent__c"] == "None" or self.loanDict[
                "Loan.Protected_Equity_Percent__c"] == "0":
                self.loanDict["Loan.Protected_Equity__c"] = "No"
            else:
                self.loanDict["Loan.Protected_Equity__c"] = "Yes"

            # Remoteness
            self.__logging("Enumerating Remoteness")
            self.reader = csv.reader(open(settings.BASE_DIR + self.REMOTENESS_FILE, 'r'))
            self.remoteDict = dict(self.reader)
            self.loanDict["Prop.Remoteness"] = self.remoteDict[self.loanDict["Prop.Postcode__c"]]

            return {'status': "Ok"}

        except:
            self.__logging("# Enumeration Error")
        return {'status': "Error"}

    def ContactEnumeration(self, prefix):
        try:
            for i in range(int(self.loanDict[prefix + ".Number"])):

                self.__logging("Contact Enumeration - " + prefix + ".Number." + str(i))

                if self.loanDict[prefix + str(i + 1) + ".Phone"] != None:
                    self.loanDict[prefix + str(i + 1) + ".Phone"] = str(
                        self.loanDict[prefix + str(i + 1) + ".Phone"]).replace("+61", "0").replace(" ", "")

                if self.loanDict[prefix + str(i + 1) + ".MobilePhone"] != None:
                    self.loanDict[prefix + str(i + 1) + ".MobilePhone"] = str(
                        self.loanDict[prefix + str(i + 1) + ".MobilePhone"]).replace("+61", "0").replace(" ", "")

                if self.loanDict[prefix + str(i + 1) + ".Permanent_Resident__c"] == "Yes":
                    self.loanDict[prefix + str(i + 1) + ".ResidencyStatus"] = "Permanently in Australia"
                else:
                    self.loanDict[prefix + str(i + 1) + ".ResidencyStatus"] = "Non Resident"

                if prefix == "Brwr":
                    if i == 0:
                        self.loanDict[prefix + str(i + 1) + ".PrimaryApplicant"] = "Yes"
                    else:
                        self.loanDict[prefix + str(i + 1) + ".PrimaryApplicant"] = "No"

                # NameTitle - Strip dot
                self.loanDict[prefix + str(i + 1) + ".NameTitle"] = \
                    self.loanDict[prefix + str(i + 1) + ".Salutation"].replace(".","")

                self.loanDict[prefix + str(i + 1) + ".MaritalStatus"] = \
                        self.loanDict[prefix + str(i + 1) + ".Marital_Status__c"].replace(".","")

            return {"status": "Ok"}
        except:
            return {'status': "Error"}

    # UTILITY FUNCTIONS

    def __firstCap(self, inputString):
        if inputString:
            newString = ''
            wordList = inputString.split()
            for word in wordList:
                newWord = word.lower()
                newString += newWord.capitalize() + ' '
            return newString.rstrip()

    def __enumState(self, strState):
        if len(strState) < 4:
            return strState.upper()
        else:
            return self.StateShortCode[self.__firstCap(strState)]

    def __logging(self, string):
        self.outputLog += string + "\r\n"
