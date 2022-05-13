#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'calendly'

urlpatterns = [

    # Externally Exposed Views
    #path('webhook', views.CalendlyWebhook.as_view(), name='webhook'),
    path('meetings', views.MeetingList.as_view(), name='meetings'),

 ]

