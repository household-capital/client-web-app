#Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'calculator'

urlpatterns = [

    path('calcList', views.CalcListView.as_view(), name='calcList'),
    path('calcCreateEnquiry/<uuid:uid>', views.CalcCreateEnquiry.as_view(), name='calcCreateEnquiry'),
    path('calcDelete/<uuid:uid>', views.CalcDeleteView.as_view(), name='calcDelete'),
    path('calcSummaryNewPdf/<uuid:uid>', views.CalcSummaryNewPdf.as_view(), name='calcSummaryNewPdf'),

    path('contactList', views.ContactListView.as_view(), name='contactList'),
    path('contactDetail/<uuid:uid>', views.ContactDetailView.as_view(), name='contactDetail'),
    path('contactAction/<uuid:uid>', views.ContactActionView.as_view(), name='contactAction'),
    path('contactDelete/<uuid:uid>', views.ContactDeleteView.as_view(), name='contactDelete'),
    path('contactConvert/<uuid:uid>', views.ContractConvertView.as_view(), name = 'contactConvert')

]



