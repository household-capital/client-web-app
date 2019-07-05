#Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.CalcStartView.as_view()),
    path('start', views.CalcStartView.as_view(), name='calcStart'),
    path('results/<uuid:uid>', views.CalcResultsView.as_view(), name='calcResults'),
    path('results/calcOutputAge/<uuid:uid>', views.CalcOutputAge.as_view(), name='calcOutputAge'),
    path('results/calcOutputPostcode/<uuid:uid>', views.CalcOutputPostcode.as_view(), name='calcOutputPostcode'),

    path('calcList', views.CalcListView.as_view(), name='calcList'),
    path('calcSpam/<uuid:uid>', views.CalcMarkSpam.as_view(), name='calcSpam'),
    path('calcCreateEnquiry/<uuid:uid>', views.CalcCreateEnquiry.as_view(), name='calcCreateEnquiry'),
    path('calcSummaryNewPdf/<uuid:uid>', views.CalcSummaryNewPdf.as_view(), name='calcSummaryNewPdf'),

    path('contact', views.WebContactView.as_view(), name='webContact'),
    path('contactList', views.ContactListView.as_view(), name='contactList'),
    path('contactDetail/<uuid:uid>', views.ContactDetailView.as_view(), name='contactDetail'),
    path('contactAction/<uuid:uid>', views.ContactActionView.as_view(), name='contactAction'),
    path('contactDelete/<uuid:uid>', views.ContactDeleteView.as_view(), name='contactDelete'),

    path('test/<uuid:uid>', views.Test.as_view(), name='test'),

]



