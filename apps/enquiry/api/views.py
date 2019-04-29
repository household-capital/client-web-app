#Python Imports
import os

# Django Imports
from django.conf import settings

# Third Party Imports
from rest_framework.generics import ListAPIView,CreateAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

# Local Application Imports
from .serialisers import EnquirySeraliser
from apps.enquiry.models import Enquiry

# VIEWS

class APIView(APIView ):
    permission_classes = []
    authentication_classes = []

    def get(self, request, format=None):
        qs=Enquiry.objects.all()
        serialiser=EnquirySeraliser(qs,many=True)
        return Response(serialiser.data)

class APIListView(ListAPIView ):
    permission_classes = []
    authentication_classes = []
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser

    def get_queryset(self):
        qs=Enquiry.objects.all()
        query=self.request.GET.get('q')
        if query:
            qs=qs.filter(name__icontains=query)
        return qs


class APICreateView(CreateAPIView):
    permission_classes = []
    authentication_classes = []
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser

    #def perform_create(self, serializer):


class APIDetailView(RetrieveAPIView):
    permission_classes = []
    authentication_classes = []
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser
    lookup_field = 'pk'