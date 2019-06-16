# Python Imports
import os

# Django Imports
from django.conf import settings
from django.shortcuts import get_object_or_404

# Third Party Imports
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions

# Local Application Imports
from .serialisers import EnquirySeraliser
from apps.enquiry.models import Enquiry


# VIEWS
#Single End Point

class StatusAPIView(CreateModelMixin,
                    RetrieveModelMixin,
                    UpdateModelMixin,
                    DestroyModelMixin,
                    ListAPIView):
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

    def get_object(self):
        request=self.request
        enqUID=request.GET.get('enqUID',None)
        qs=self.queryset
        obj=None
        if enqUID:
            obj = get_object_or_404(qs, enqUID=enqUID)
            self.check_object_permissions(request,obj)
        return obj

    def get (self, request, *args, **kwargs):
        enqUID=request.GET.get('enqUID',None)
        if enqUID:
            return self.retrieve(request, *args, **kwargs)
        return super(StatusAPIView,self).get(request, *args, **kwargs )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args,**kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args,**kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args,**kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


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