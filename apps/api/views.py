# Django Imports

from django.views.generic import  View

from apps.lib.api_Website import apiWebsite


class TEST(View):

    def get(self,request, *args, **kwargs):
        webAPI=apiWebsite()
        webAPI.openAPI()
        print(webAPI.getCalculatorQueue())