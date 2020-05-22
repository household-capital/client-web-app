#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'enquiry'

urlpatterns = [
    #Authenticated Views
    path('', views.EnquiryCreateView.as_view(), name='enquiry'),
    path('call', views.EnquiryCallView.as_view(), name='enquiryCall'),
    path('<uuid:uid>', views.EnquiryUpdateView.as_view(), name='enquiryDetail'),
    path('enquiryList', views.EnquiryListView.as_view(), name='enquiryList'),
    path('enquiryCreateSummary/<uuid:uid>',views.CreateEnquirySummary.as_view(),name='enqCreateSummary'),
    path('enquirySendDetail/<uuid:uid>', views.SendEnquirySummary.as_view(), name='enqSendDetails'),
    path('enquiryEligibility/<uuid:uid>',views.EnquiryEmailEligibility.as_view(), name='enqEligibility'),
    path('enquiryConvert/<uuid:uid>', views.EnquiryConvert.as_view(), name='enqConvert'),
    path('enquiryOwn/<uuid:uid>', views.EnquiryOwnView.as_view(), name='enquiryOwn'),
    path('enquiryAssign/<uuid:uid>', views.EnquiryAssignView.as_view(), name='enqAssign'),
    path('enquiryCloseFollowUp/<uuid:uid>',views.EnquiryCloseFollowUp.as_view(),name='enqMarkFollowUp'),
    path('enquiryDelete/<uuid:uid>', views.EnquiryDeleteView.as_view(), name='enqDelete'),

    #Unauthenticated Views
    path('enquirySummaryPdf/<uuid:uid>', views.EnqSummaryPdfView.as_view(), name='enqSummaryPdf'),
    path('enquiryIncomeSummaryPdf/<uuid:uid>', views.EnqIncomeSummaryPdfView.as_view(), name='enqIncomeSummaryPdf'),

]

