# Python Imports
import os

# Django Imports
from django.conf import settings

# Third Party Imports
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions

# Local Application Imports
from .serialisers import EnquirySeraliser
from apps.enquiry.models import Enquiry


# VIEWS

class StatusAPIView(CreateModelMixin,ListAPIView):
    #List view with create
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser

    def get_queryset(self):
        qs = Enquiry.objects.all()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

    def post(self, request, *args, **kwargs):
        return self.create(request, *args,**kwargs)


#class StatusAPIDetailView(DestroyModelMixin,UpdateModelMixin,RetrieveAPIView):
class StatusAPIDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser
    lookup_field = 'enqUID'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args,**kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# ----------
class APIListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser

    def get_queryset(self):
        qs = Enquiry.objects.all()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class APICreateView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser

    # def perform_create(self, serializer):


class APIDetailView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser
    lookup_field = 'enqUID'


class APIUpdateView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser
    lookup_field = 'enqUID'

class APIDeleteView(DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySeraliser
    lookup_field = 'enqUID'