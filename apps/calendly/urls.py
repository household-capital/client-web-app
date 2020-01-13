#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'calendly'

urlpatterns = [

    path('webhook', views.CalendlyWebhook.as_view(), name='webhook'),

 ]

