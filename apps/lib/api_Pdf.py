'''Wrapper utility for pdf API '''
# Python Imports
import requests
import os

# Django Imports
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


# Third-party Imports
from api2pdf import Api2Pdf

# Local Application Imports
from apps.lib.site_Logging import write_applog


class pdfGenerator():
    """API2PDF API Wrapper - HTML to PDF Conversion"""

    def __init__(self, pdfID):
        self.a2p_client = Api2Pdf(os.getenv('API2PDF_KEY'))
        self.pdfUrl = ""
        self.pdfContents = None
        self.pdfID = pdfID
        self.pdf_options = {'preferCSSPageSize': True, 'marginBottom': 0, 'marginLeft': 0, 'marginRight': 0, 'marginTop': 0,
                                      'paperWidth': 8.27, 'paperHeight': 11.69}

    def _processAPIResult(self, api_response, targetFileName):
        if api_response.result['success']:
            write_applog("INFO", 'pdfGenerator', 'createPdf', "Api2Pdf success: " + self.pdfID)
        else:
            write_applog("ERROR", 'pdfGenerator', 'createPdf', "Api2Pdf failure: " + self.pdfID + "-" + str(api_response))
            return {False, "API Returned Error"}

        self.pdfUrl = api_response.result['pdf']

        responseObj = requests.get(self.pdfUrl, verify=False, stream=True)
        responseObj.raw.decode_content = True

        default_storage.delete(targetFileName)
        self.savePdf(targetFileName,responseObj)

        write_applog("INFO", 'pdfGenerator', 'createPdf', "Summary Report Saved: " + self.pdfID)
        localfile = default_storage.open(targetFileName, 'rb')
        self.pdfContents = localfile.read()

        return {True, "File saved"}

    def createPdfFromUrl(self, sourceURL, pdfDescription, targetFileName):
        self.pdfUrl = ""
        try:
            # Make API request to Api2Pdf
            write_applog("INFO", 'pdfGenerator', 'createPdf', "Api2Pdf submitted: " + self.pdfID)

            api_response = self.a2p_client.HeadlessChrome.convert_from_url(
                sourceURL, file_name=pdfDescription, **self.pdf_options
            )
        except:
            write_applog("ERROR", 'pdfGenerator', 'createPdf', " Presumed timeout error: " + self.pdfID, is_exception=True)
            return {False, "API Error"}

        return self._processAPIResult(api_response, targetFileName)

    def createPdfFromHTML(self, html, pdfDescription, targetFileName):
        try:
            # Make API request to Api2Pdf
            write_applog("INFO", 'pdfGenerator', 'createPdf', "Api2Pdf submitted: " + self.pdfID)

            api_response = self.a2p_client.HeadlessChrome.convert_from_html(
                html, file_name=pdfDescription, **self.pdf_options
            )
        except:
            write_applog("ERROR", 'pdfGenerator', 'createPdf', "Presumed timeout error: " + self.pdfID, is_exception=True)
            return {False, "API Error"}

        return self._processAPIResult(api_response, targetFileName)

    def mergePdfs(self, urlList, pdfDescription, targetFileName):

        try:
            api_response = self.a2p_client.merge(list_of_urls=urlList, inline_pdf=False, file_name=pdfDescription)

            if api_response.result['success']:
                write_applog("INFO", 'pdfGenerator', 'mergePdfs', "Api2Pdf success: " + self.pdfID)

            else:
                write_applog("ERROR", 'pdfGenerator', 'mergePdfs', "Api2Pdf failure: " + self.pdfID + "-"
                             + str(api_response))

                return {'False', "API Returned Error"}

        except:
            write_applog("ERROR", 'pdfGenerator', 'mergePdfs', "Presumed timeout error: " + self.pdfID, is_exception=True)

            return {'False', "API Error"}

        self.pdfUrl = api_response.result['pdf']

        responseObj = requests.get(self.pdfUrl, verify=False, stream=True)
        responseObj.raw.decode_content = True

        default_storage.delete(targetFileName)
        try:
            self.savePdf(targetFileName, responseObj)
            write_applog("INFO", 'pdfGenerator', 'mergePdfs', "Merged PDF Saved: " + self.pdfID)

            localfile = default_storage.open(targetFileName, 'rb')
            self.pdfContents = localfile.read()

        except:
            write_applog("ERROR", 'pdfGenerator', 'mergePdfs',
                         "Failed to save Merged Pdfs: " + self.pdfID, is_exception=True)

            return {'False', "Could not save"}

        return {'True', "File saved"}

    def emailPdf(self, template_name, email_context, subject, from_email, to, bcc, text_content, attachFilename):
        '''Email PDF using provided template and context'''
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
                         "Failed to email Summary Report:" + self.pdfID, is_exception=True)
            return False

    def getContent(self):
        return self.pdfContents

    def savePdf(self, targetFileName, responseObj):
        """Creates file locally before saving to default_storage"""

        localFile = NamedTemporaryFile(delete=True)

        for chunk in responseObj.iter_content(chunk_size=128):
            localFile.write(chunk)
            localFile.flush()

        default_storage.save(targetFileName, localFile)

        localFile.close()
        return