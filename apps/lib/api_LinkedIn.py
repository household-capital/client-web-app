#Python Imports
import html
import http.cookiejar as cookielib
import json
import os
import re
import urllib.request
import urllib.parse

#Third Party Imports
from bs4 import BeautifulSoup

#Application Imports
from apps.lib.site_Logging import write_applog

class LinkedInParser(object):

    cookie_filename = "cookies.txt"

    def __init__(self, login, password):
        """ Start up... """
        self.login = login
        self.password = password

        # Simulate browser with cookies enabled
        self.cj = cookielib.MozillaCookieJar(self.cookie_filename)
        if os.access(self.cookie_filename, os.F_OK):
            self.cj.load()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler(),
            urllib.request.HTTPHandler(debuglevel=0),
            urllib.request.HTTPSHandler(debuglevel=0),
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'))
        ]

        # Login
        self.isLoggedIn=self.loginPage()
        self.cj.save()

    def loadPage(self, url, data=None):
        """
        Utility function to load HTML from URLs
        """
        try:
            if data is not None:
                response = self.opener.open(url, data)
            else:
                response = self.opener.open(url)
            return ''.join([str(l) for l in response.readlines()])
        except Exception as e:
            return None

    def loadSoup(self, url, data=None):
        """
        Combine loading of URL, HTML, and parsing with BeautifulSoup
        """
        htmlStr = self.loadPage(url, data)
        soup = BeautifulSoup(htmlStr, "html5lib")
        return soup

    def loginPage(self):
        """
        Handle login. This should populate our cookie jar.
        """

        #Check whether logged-in first
        soup = self.loadSoup("https://www.linkedin.com/")
        title = str(soup.find('title').contents)

        if "Log In" in title:
            soup = self.loadSoup("https://www.linkedin.com/login")
            csrf = soup.find('input', {'name': "loginCsrfParam"})['value']
            login_data = urllib.parse.urlencode({
                'session_key': self.login,
                'session_password': self.password,
                'loginCsrfParam': csrf,
            }).encode('utf8')

            response=self.loadPage("https://www.linkedin.com/login-submit", login_data)
            if response==None:
                write_applog("ERROR", 'apiLinkedIn', 'loginPage', 'Could not login')
                return False
            else:
                write_applog("INFO", 'apiLinkedIn', 'loginPage', 'Logged in')
                return True

        return True

    def retrieveData(self, profileUrl):

        if not self.isLoggedIn:
            return None

        name = None
        title = None
        picUrl = None

        # Get Target URL data
        response = self.opener.open(profileUrl)

        htmlStr = html.unescape(''.join([str(l) for l in response.readlines()]))
        # Use BeautifulSoup to find relevant code tag
        soup = BeautifulSoup(htmlStr, "html5lib")
        try:
            content = soup.find('code', string=re.compile('fs_profile:')).contents
        except:
            return None

        # Load JSON data to dictionary
        content = str(content[0])
        content = content.replace("'b'", '').replace('\\n', '').strip()
        # note source is not JSON compliant - has hex escapes, therefore convert to unicode escapes
        content = content.replace("\\x", "\\u00")

        results = json.loads(content)

        #Get fs_profile:
        profileId=results['data']['*profile'].replace('profile','miniProfile')

        # Reference Profile dictionary item (find based on miniProfileId)
        profile_list = results['included']

        for profile in profile_list:
            if profile['entityUrn']==profileId:
                    name = profile["firstName"] + " " + profile["lastName"]
                    title = profile["occupation"]
                    try:
                        picUrl = profile["picture"]["rootUrl"] + \
                                 profile["picture"]['artifacts'][len(profile["picture"]['artifacts']) - 1][
                                     'fileIdentifyingUrlPathSegment']
                    except:
                        pass

        return {"name": name, "title": title, "picUrl": picUrl}

