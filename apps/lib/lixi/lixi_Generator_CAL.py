# Python Imports
import datetime, time
from dateutil.parser import parse
import logging
from io import StringIO
from xml.dom import minidom
from random import randint

# Django Imports
from django.conf import settings
from django.core.files.storage import default_storage

# Third-party Imports
from lxml import etree as ElementTree


# Local Imports


class LixiXMLGenerator:
    # Lixi generator for Reverse Mortgage loans
    # This class builds LIXI XML based on paramaters and paramater lists passed to it

    def __init__(self, lixiSettings, productionData, submissionID, applicationID, commentStr, localFile):
        # Create basic structure of LIXI file usine lxml

        self.outputLog = ""
        self.commentStr = commentStr
        self.LIXI_SETTINGS = lixiSettings

        self.__logging("LIXI Header Creation")

        # Package
        self.root = ElementTree.Element('Package', nsmap=self.LIXI_SETTINGS['ns_map_'], ProductionData=productionData,
                                        UniqueID=submissionID)

        # -Content
        self.content = ElementTree.SubElement(self.root, 'Content')

        # --Application
        self.application = ElementTree.SubElement(self.content, 'Application', ProductionData=productionData,
                                                  UniqueID=applicationID)
        self.localFile = localFile

        # -Instructions
        self.instructions = ElementTree.SubElement(self.root, 'Instructions')
        self.applicationInstructions = ElementTree.SubElement(self.instructions, 'ApplicationInstructions')
        self.submit = ElementTree.SubElement(self.applicationInstructions, 'Submit', AssessmentType="Full",
                                             IsAccountVariation="No", IsResubmission="No")

        # -Publisher
        self.publisher = ElementTree.SubElement(self.root, 'Publisher', CompanyName="HouseholdCapital",
                                                LIXICode='LIXILIXI',
                                                Email='lendingservices@householdcapital.com',
                                                PublishedDateTime=self.__getTimeStamp())

        # -Recipient
        self.recipient = ElementTree.SubElement(self.root, 'Recipient', Description='AMAL', LIXICode='LIXILIXI')

        # -SchemaVersion
        self.schemaversion = ElementTree.SubElement(self.root, 'SchemaVersion', LIXITransactionType="CAL",
                                                    LIXIVersion=self.LIXI_SETTINGS['LIXI_VERSION_CAL'])

    def populateElements(self, srcDict):

        # Address
        self.__logging("Generating Address Element")
        try:
            self.address = ElementTree.SubElement(self.application, 'Address',
                                                  dict(AustralianPostCode=srcDict['Prop.Postcode__c'],
                                                       AustralianState=srcDict['Prop.state'],
                                                       Country='AU', Suburb=srcDict['Prop.Suburb_City__c'],
                                                       Type='Standard', UniqueID="HHC-" + srcDict['Prop.Id'],
                                                       GNAF_ID=srcDict['Prop.gnafId']))

            streetDict = dict(
                StreetNumber=str(srcDict['Prop.numberFirst']),
                StreetName=srcDict['Prop.streetName'],
                StreetType=srcDict['Prop.streetType'])

            if srcDict['Prop.streetType'] == None:
                #Street Type may be none - remove
                streetDict.pop('StreetType')

            self.standardAddress = ElementTree.SubElement(self.address, 'Standard', streetDict)

            if srcDict['Prop.flatNumber'] != "None":
                self.standardAddress.set("Unit", srcDict['Prop.flatNumber'])

            if srcDict['Prop.buildingName'] != "None":
                self.standardAddress.set("BuildingName", srcDict['Prop.buildingName'])

            # Comment
            self.detailedcomment = ElementTree.SubElement(self.application, 'DetailedComment',
                                                          ContextDescription="Description")
            self.comment = ElementTree.SubElement(self.detailedcomment, 'Comment')
            self.comment.text = self.commentStr
            self.detailedcomment = ElementTree.SubElement(self.application, 'DetailedComment',
                                                          ContextDescription="Remoteness")
            self.comment = ElementTree.SubElement(self.detailedcomment, 'Comment')
            self.comment.text = srcDict['Prop.Remoteness']
        except:
            self.__logging("# Address Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # Insurance
        try:
            self.__logging("Generating Insurance Elements")

            self.insurance = ElementTree.SubElement(self.application, 'Insurance',
                                                    dict(ExpiryDate=str(srcDict['Prop.Insurance_Expiry_Date__c']),
                                                         InsuredAmount=str(srcDict['Prop.Minimum_Insurance_Value__c']),
                                                         PolicyNumber=srcDict['Prop.Policy_Number__c'],
                                                         OtherInsurerName=srcDict['Prop.Insurer__c'],
                                                         UniqueID="INS-" + srcDict['Prop.Policy_Number__c']
                                                         ))
        except:
            self.__logging("#Insurance Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # Loan Details
        try:
            self.__logging("Generating Loan Elements")
            self.loanDetail = ElementTree.SubElement(self.application, 'LoanDetails', dict(
                EstimatedSettlementDate=srcDict['Loan.Loan_Settlement_Date__c'],
                OriginatorReferenceID="HHC-" + srcDict['LoanObject.LoanNumber'],
                ProductCode='21001259', ProductName='HHC\HHC - Household Capital Longevity Variable IO Loan',
                LoanType='Reverse Mortgage',
                AmountRequested=str(int(round(srcDict['Loan.Total_Household_Loan_Amount__c'], 0))),
                ProposedAnnualInterestRate=str(srcDict['Loan.Interest_Rate__c'])))
        except:
            self.__logging("# Loan Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # - Commission
        try:
            self.__logging("Generating Commission Elements")
            self.commission = ElementTree.SubElement(self.loanDetail, "Commission", dict(Trail='0', ))
        except:
            self.__logging("# Commission Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # -EquityRelease
        try:
            self.__logging("Generating Equity Release Elements")
            self.equityRelease = ElementTree.SubElement(self.loanDetail, "EquityRelease",
                                                        dict(ProtectedEquity=srcDict["Loan.Protected_Equity__c"],
                                                             ProtectedEquityPercentage=srcDict[
                                                                 "Loan.Protected_Equity_Percent__c"]))
        except:
            self.__logging("# Equity Release Error")
            return {'status': "Error", 'responseText': self.outputLog}

        try:
            self.__logging("Generating Purpose Elememts")
            self.lendingPurpose = ElementTree.SubElement(self.loanDetail, "LendingPurpose", dict(
                ABSLendingPurposeCode=srcDict["Purp" + str(1) + ".ABSCode"],
                LenderCode=srcDict["Purp" + str(1) + ".Category__c"],
                Description=srcDict["Purp" + str(1) + ".Intention__c"],
                PurposeAmount=str(int(round(srcDict['Loan.Total_Household_Loan_Amount__c'], 0)))))

            # -Loan Purpose
            self.loanPurpose = ElementTree.SubElement(self.loanDetail, "LoanPurpose",
                                                      dict(NCCPStatus="Regulated",
                                                           PrimaryPurpose=srcDict["Purp.PrimaryPurpose"]))
        except:
            self.__logging("# Purposes Error")
            return {'status': "Error", 'responseText': self.outputLog}

        try:
            self.__logging("Generating Rate Composition Elements")
            # -Term
            self.rateComposition = ElementTree.SubElement(self.loanDetail, "RateComposition",
                                                          dict(OriginatorMargin=str(srcDict["Loan.OriginatorMargin"])))
            # -Term
            self.loanTerm = ElementTree.SubElement(self.loanDetail, "Term",
                                                   dict(InterestType="Variable", PaymentType="Interest Capitalised",
                                                        PaymentTypeDuration="1", PaymentTypeUnits="Months",
                                                        TotalTermDuration="480",
                                                        TotalTermType="Total Term", TotalTermUnits="Months",
                                                        InterestTypeUnits="Months"))
        except:
            self.__logging("# Rate Composition Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # Applicants
        for i in range(int(srcDict["Brwr.Number"])):

            try:
                self.__logging("Generating Borrower-" + str(i + 1) + ' Elements')
                self.personapplicant = ElementTree.SubElement(self.application, "PersonApplicant",
                                                              dict(ApplicantType="Borrower", DateOfBirth=srcDict[
                                                                  "Brwr" + str(i + 1) + ".Birthdate__c"],
                                                                   Gender=srcDict["Brwr" + str(i + 1) + ".Gender__c"],
                                                                   MaritalStatus=srcDict[
                                                                       "Brwr" + str(i + 1) + ".MaritalStatus"],
                                                                   PrimaryApplicant=srcDict[
                                                                       "Brwr" + str(i + 1) + ".PrimaryApplicant"],
                                                                   ResidencyStatus=srcDict[
                                                                       "Brwr" + str(i + 1) + ".ResidencyStatus"],
                                                                   UniqueID="HHC-" + srcDict[
                                                                       "Brwr" + str(i + 1) + ".Id"]))

                self.Contact = ElementTree.SubElement(self.personapplicant, "Contact")
                self.currentaddress = ElementTree.SubElement(self.Contact, "CurrentAddress",
                                                             dict(x_MailingAddress="HHC-" + srcDict['Prop.Id'],
                                                                  x_ResidentialAddress="HHC-" + srcDict['Prop.Id']))

                if srcDict["Brwr" + str(i + 1) + ".Email"] != None:
                    self.emailaddress = ElementTree.SubElement(self.Contact, "EmailAddress",
                                                               Email=srcDict["Brwr" + str(i + 1) + ".Email"])

                if srcDict["Brwr" + str(i + 1) + ".Phone"] != None:
                    self.homephone = ElementTree.SubElement(self.Contact, "HomePhone", dict(
                        AustralianDialingCode=str(srcDict["Brwr" + str(i + 1) + ".Phone"])[:2],
                        Number=str(srcDict["Brwr" + str(i + 1) + ".Phone"])[-8:]))

                if srcDict["Brwr" + str(i + 1) + ".MobilePhone"] != None:
                    self.mobilephone = ElementTree.SubElement(self.Contact, "Mobile", dict(
                        AustralianDialingCode=str(srcDict["Brwr" + str(i + 1) + ".MobilePhone"])[:2],
                        Number=str(srcDict["Brwr" + str(i + 1) + ".MobilePhone"])[-8:]))

                self.personname = ElementTree.SubElement(self.personapplicant, "PersonName",
                                                         dict(FirstName=srcDict["Brwr" + str(i + 1) + ".FirstName"],
                                                              NameTitle=srcDict["Brwr" + str(i + 1) + ".NameTitle"],
                                                              Surname=srcDict["Brwr" + str(i + 1) + ".LastName"]))

                ##Power of Attorney

                if srcDict["POA.Number"] >= (i + 1):
                    # You can only have one POA per applicant in LIXI
                    self.POA = ElementTree.SubElement(self.personapplicant, "PowerOfAttorney",
                                                      dict(x_POAHolder="POA-" + srcDict['POA' + str(i + 1) + '.Id']))
            except:
                self.__logging("# Borrower Error")
                return {'status': "Error", 'responseText': self.outputLog}

        try:
            self.__logging("Generating Valuation Elements")
            # Real Estate Asset
            self.realEstateAsset = ElementTree.SubElement(self.application, 'RealEstateAsset',
                                                          dict(PrimaryPurpose='Owner Occupied',
                                                               PrimaryUsage='Residential',
                                                               PropertyID="HHC-" + srcDict['Prop.Id'],
                                                               Status='Established',
                                                               x_Address="HHC-" + srcDict['Prop.Id']))

            self.valuation = ElementTree.SubElement(self.realEstateAsset, 'EstimatedValue',
                                                    dict(Value=str(int(srcDict['Prop.Home_Value_FullVal__c'])),
                                                         ValuedDate=str(
                                                             self.__parseDate(srcDict['Prop.Last_Valuation_Date__c'])),
                                                         x_Valuer=str(srcDict['Prop.Valuer__c']).replace(" ", "")))

            self.reInsurance = ElementTree.SubElement(self.realEstateAsset, 'Insurance',
                                                      x_Insurance="INS-" + srcDict['Prop.Policy_Number__c'])

            # self.residential = ElementTree.SubElement(self.realEstateAsset, 'Residential',
            #                                          Type=srcDict['Prop.LixiPropertyType'])

            self.residential = ElementTree.SubElement(self.realEstateAsset, 'PropertyType',
                                                      CategoryTypeName=srcDict['Prop.LixiPropertyType'])

            # Related Company (Valuer)
            self.relatedCompany = ElementTree.SubElement(self.application, 'RelatedCompany',
                                                         dict(CompanyName=srcDict['Prop.Valuer__c'],
                                                              UniqueID=str(srcDict['Prop.Valuer__c']).replace(" ", "")))
            self.relatedCompanyContact = ElementTree.SubElement(self.relatedCompany, "Contact")
            self.valuerContact = ElementTree.SubElement(self.relatedCompanyContact, "ContactPerson",
                                                        dict(Role="Valuer", x_ContactPerson="HHC-" + srcDict[
                                                            'Prop.Valuer_Name__c'].replace(" ", "")))

        except:
            self.__logging("# Valuation Error")
            return {'status': "Error", 'responseText': self.outputLog}

        try:
            self.__logging("Generating Related Party Elements")
            # Related Person (POA)
            for i in range(int(srcDict["POA.Number"])):
                self.relatedPerson = ElementTree.SubElement(self.application, 'RelatedPerson',
                                                            dict(DateOfBirth=srcDict[
                                                                "POA" + str(i + 1) + ".Birthdate__c"],
                                                                 UniqueID="POA-" + srcDict['POA' + str(i + 1) + ".Id"]))

                self.relatedPersonContact = ElementTree.SubElement(self.relatedPerson, "Contact", dict(
                    x_Address="POA-" + srcDict['POA' + str(i + 1) + ".Id"]))

                if srcDict["POA" + str(i + 1) + ".Email"] != None:
                    self.relatedPersonContact.set("Email", srcDict["POA" + str(i + 1) + ".Email"])

                if srcDict["POA" + str(i + 1) + ".Phone"] != None:
                    self.homephone = ElementTree.SubElement(self.relatedPersonContact, "HomePhone", dict(
                        AustralianDialingCode=str(srcDict["POA" + str(i + 1) + ".Phone"])[:2],
                        Number=str(srcDict["POA" + str(i + 1) + ".Phone"])[-8:]))

                if srcDict["POA" + str(i + 1) + ".MobilePhone"] != None:
                    self.mobilephone = ElementTree.SubElement(self.relatedPersonContact, "Mobile", dict(
                        AustralianDialingCode=str(srcDict["POA" + str(i + 1) + ".MobilePhone"])[:2],
                        Number=str(srcDict["POA" + str(i + 1) + ".MobilePhone"])[-8:]))

                self.relatedPersonName = ElementTree.SubElement(self.relatedPerson, "PersonName",
                                                                dict(FirstName=srcDict[
                                                                    'POA' + str(i + 1) + ".FirstName"],
                                                                     Surname=srcDict['POA' + str(i + 1) + ".LastName"]))

            # Related Person (Valuer)
            self.relatedPersonValuer = ElementTree.SubElement(self.application, 'RelatedPerson',
                                                              dict(UniqueID="HHC-" + srcDict['Prop.Valuer_Name__c']))
            self.relatedNameValuer = ElementTree.SubElement(self.relatedPersonValuer, 'PersonName',
                                                            dict(FirstName=srcDict['Prop.Valuer_Firstname'],
                                                                 Surname=srcDict['Prop.Valuer_Surname']))

        except:
            self.__logging("# Related Party Error")
            return {'status': "Error", 'responseText': self.outputLog}

        try:
            self.__logging("Generating Sales Channel Elements")

            # Sales Channel Asset
            logging.info("         LIXI Sales Channel")

            self.salesChannel = ElementTree.SubElement(self.application, 'SalesChannel')

            if srcDict['Loan.Distribution_Partner_Contact__c'] != None:
                self.Referrer = ElementTree.SubElement(self.salesChannel, 'Company',
                                                       dict(CompanyName=srcDict['Dist.Name'],
                                                            UniqueID="HHC-" + srcDict['Dist.AccountId']))

                self.Introducer = ElementTree.SubElement(self.salesChannel, 'Introducer',
                                                         dict(ContactName=srcDict['Dist.FirstName'] + " " + srcDict[
                                                             'Dist.LastName'],
                                                              IntroducerID="HHC-" + srcDict['Dist.Id']))

            self.LoanWriter = ElementTree.SubElement(self.salesChannel, 'LoanWriter',
                                                     dict(FirstName=srcDict['User.FirstName'],
                                                          Surname=srcDict['User.LastName'],
                                                          UniqueID="HHC-" + srcDict['User.Id']))
        except:
            self.__logging("# Sales Channel Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # Summary
        self.__logging("Generating Establishmemt Fee Elements")
        try:
            self.Summary = ElementTree.SubElement(self.application, 'Summary')

            self.Fee = ElementTree.SubElement(self.Summary, 'Fee', dict(Type='Establishment Fee'))
            self.FeePercentage = ElementTree.SubElement(self.Fee, 'Percentage',
                                                        dict(Rate=str(srcDict['Opp.Establishment_Fee_Percent__c'])))
        except:
            self.__logging("# Establishmemt Fee Error")
            return {'status': "Error", 'responseText': self.outputLog}

        self.__logging("Lixi Element Population Successful")

        return {'status': "Ok", 'responseText': self.outputLog}

    def CreateFile(self):

        try:
            self.__logging("Creating Lixi File")
            self.outputLog = ""

            ElementTree.tostring(self.root)
            baseTree = ElementTree.ElementTree(self.root)  # wrap it in an ElementTree instance

            # Use minidom to beautify the xml (humnan readable)
            treeString = minidom.parseString(ElementTree.tostring(self.root)).toprettyxml()
            prettyTree = ElementTree.ElementTree(ElementTree.fromstring(treeString))

            # Write to targetfile
            prettyTree.write(self.localFile, encoding='utf-8', xml_declaration=False)
            self.localFile.flush()
        except:
            self.__logging("# Could not generate file")
            return {'status': "Error", 'responseText': self.outputLog}

        self.__logging("File Created")
        return {'status': "Ok", 'responseText': self.outputLog}

    def ValidateXML(self, xmlFilename, xmlSchemaFilename):

        self.outputLog = ""
        try:
            self.__logging("Checking schema")
            # open and read schema file
            with open(settings.BASE_DIR + xmlSchemaFilename, 'r',  encoding='utf-8') as schema_file:
                schema_to_check = schema_file.read()

            # open and read xml file
            with default_storage.open(xmlFilename, 'r') as xml_file:
                xml_to_check = xml_file.read()

            xmlschema_doc = ElementTree.parse(StringIO(schema_to_check))
            xmlschema = ElementTree.XMLSchema(xmlschema_doc)

            # parse xml
            doc = ElementTree.parse(StringIO(xml_to_check))
            self.__logging("XML well formed, syntax ok.")

        # check for file IO error
        except IOError as err:
            self.__logging("# XML Valiation I/O Error")
            self.__logging(str(err))
            return {'status': "Error", 'responseText': self.outputLog}

        # check for XML syntax errors
        except ElementTree.XMLSyntaxError as err:
            self.__logging("# XML Syntax Error")
            self.__logging(str(err))
            return {'status': "Error", 'responseText': self.outputLog}

        except:
            logging.exception("# Unknown XML Error")
            self.__logging("# Unknown XML Error")
            return {'status': "Error", 'responseText': self.outputLog}

        # validate against schema

        self.__logging("Schema Validation")
        try:
            xmlschema.assertValid(doc)
            self.__logging("XML valid, schema validation ok")
            return {'status': "Ok", 'responseText': self.outputLog}

        except ElementTree.DocumentInvalid as err:
            self.__logging("# Schema Validation Error")
            self.__logging(str(err))

            return {'status': "Error", 'responseText': self.outputLog}

        except:
            self.__logging("# Unknown Schema Validation Error")
            return {'status': "Error", 'responseText': self.outputLog}

    # UTILITY FUNCTIONS

    def __getTimeStamp(self):
        utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
        utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
        return datetime.datetime.now().replace(tzinfo=datetime.timezone(offset=utc_offset)).replace(
            microsecond=0).isoformat()

    def __parseDate(self, srcDate):
        parsedDate = parse(srcDate).strftime('%Y-%m-%d')
        return parsedDate

    def __logging(self, string):
        self.outputLog += string + "\r\n"
