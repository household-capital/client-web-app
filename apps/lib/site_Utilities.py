# Python Imports
import requests
import os

# Django Imports
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

# Third-party Imports
from api2pdf import Api2Pdf

# Local Application Imports
from apps.lib.site_Logging import write_applog


class pdfGenerator():
    # Wrapper utility for pdf API

    def __init__(self, pdfID):
        self.a2p_client = Api2Pdf(os.getenv('API2PDF_KEY'))
        self.pdfUrl = ""
        self.pdfContents = None
        self.pdfID = pdfID

    def createPdfFromUrl(self, sourceURL, pdfDescription, targetFileName):

        self.pdfUrl = ""
        try:
            sourceUrl = sourceURL

            # Make API request to Api2Pdf
            options = {'preferCSSPageSize': True, 'marginBottom': 0, 'marginLeft': 0, 'marginRight': 0, 'marginTop': 0,
                       'paperWidth': 8.27, 'paperHeight': 11.69}

            api_response = self.a2p_client.HeadlessChrome.convert_from_url(sourceUrl,
                                                                           file_name=pdfDescription,
                                                                           **options)
            if api_response.result['success']:
                write_applog("INFO", 'pdfGenerator', 'createPdf', "Api2Pdf success: " + self.pdfID)

            else:
                write_applog("ERROR", 'pdfGenerator', 'createPdf', "Api2Pdf failure: " + self.pdfID + "-"
                             + str(api_response))

                return {'False', "API Returned Error"}

        except:
            write_applog("ERROR", 'pdfGenerator', 'createPdf', "Presumed timeout error: " + self.pdfID)

            return {'False', "API Error"}

        self.pdfUrl = api_response.result['pdf']

        responseObj = requests.get(self.pdfUrl, verify=False, stream=True)
        responseObj.raw.decode_content = True

        try:
            with open(targetFileName, 'wb') as fileWriter:
                for chunk in responseObj.iter_content(chunk_size=128):
                    fileWriter.write(chunk)
                fileWriter.close()
                write_applog("INFO", 'pdfGenerator', 'createPdf', "Summary Report Saved: " + self.pdfID)

            localfile = open(targetFileName, 'rb')
            self.pdfContents = localfile.read()

        except:
            write_applog("ERROR", 'pdfGenerator', 'createPdf',
                         "Failed to save Summary Report: " + self.pdfID)

            return {'False', "Could not save"}

        return {'True', "File saved"}

    def emailPdf(self, template_name, email_context, subject, from_email, to, bcc, text_content, attachFilename):
        try:
            html = get_template(template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc])
            msg.attach_alternative(html_content, "text/html")
            msg.attach(attachFilename, self.pdfContents, 'application/pdf')
            msg.send()
            return True
        except:
            write_applog("ERROR", 'pdfGenerator', 'emailPdf',
                "Failed to email Summary Report:" + self.pdfID)
            return False


    def getContent(self):
        return self.pdfContents
