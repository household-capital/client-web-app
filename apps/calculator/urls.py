#Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'calculator'

urlpatterns = [
    path('start', views.CalcStartView.as_view(), name='calcStart'),
    path('results/<uuid:uid>', views.CalcResultsView.as_view(), name='calcResults'),

    path('calcList', views.CalcListView.as_view(), name='calcList'),
    path('calcSpam/<uuid:uid>', views.CalcMarkSpam.as_view(), name='calcSpam'),
    path('calcSendSummary/<uuid:uid>', views.CalcSendSummary.as_view(), name='calcSendSummary'),
    path('calcOutputAge/<uuid:uid>', views.CalcOutputAge.as_view(), name='calcOutputAge'),
    path('calcOutputPostcode/<uuid:uid>', views.CalcOutputPostcode.as_view(), name='calcOutputPostcode'),
    path('calcSummaryNewPdf/<uuid:uid>', views.CalcSummaryNewPdf.as_view(), name='calcSummaryNewPdf'),

    path('contact', views.WebContactView.as_view(), name='webContact'),
    path('contactList', views.ContactListView.as_view(), name='contactList'),
    path('contactDetail/<uuid:uid>', views.ContactDetailView.as_view(), name='contactDetail'),
    path('contactAction/<uuid:uid>', views.ContactActionView.as_view(), name='contactAction'),
    path('contactDelete/<uuid:uid>', views.ContactDeleteView.as_view(), name='contactDelete'),


    #Old urls - decommission
    path('', views.InputView.as_view(), name='calcInput'),
    path('input', views.InputView.as_view(), name='calcInput'),
    path('input/<uuid:uid>', views.InputView.as_view(), name='calcInputItem'),
    path('output/<uuid:uid>/', views.OutputView.as_view(), name='calcOutput'),
    path('calcSummaryPdf/<uuid:uid>', views.CalcSummaryPdfView.as_view(), name='calcSummaryPdf'),
    path('calcSendDetail/<uuid:uid>', views.CalcSendDetails.as_view(), name='calcSendDetails'),
    path('test/<uuid:uid>', views.Test.as_view(), name='test'),


]



