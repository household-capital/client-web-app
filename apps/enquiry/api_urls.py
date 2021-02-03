from django.urls import path
from apps.enquiry import api_views

urlpatterns = [
    path('data_ingestion/', api_views.DataIngestion.as_view(), name="data_ingestion"),
    
]