#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'enquiry'

urlpatterns = [
    path('', views.EnquiryCreateView.as_view(), name='enquiry'),
    path('<uuid:uid>', views.EnquiryUpdateView.as_view(), name='enquiryDetail'),
    path('enquiryList', views.EnquiryListView.as_view(), name='enquiryList'),
    path('enquirySummaryPdf/<uuid:uid>', views.EnqSummaryPdfView.as_view(), name='enqSummaryPdf'),
    path('enquirySendDetail/<uuid:uid>', views.SendEnquirySummary.as_view(), name='enqSendDetails'),
    path('enquiryEligibility/<uuid:uid>',views.EnquiryEmailEligibility.as_view(), name='enqEligibility'),
    path('enquiryConvert/<uuid:uid>', views.EnquiryConvert.as_view(), name='enqConvert'),
    path('enquiryOwn/<uuid:uid>', views.EnquiryOwnView.as_view(), name='enquiryOwn'),
    path('enquiryFollowUp/<uuid:uid>', views.FollowUpEmail.as_view(), name='enqFollowUp'),
    path('enquiryMarkFollowUp/<uuid:uid>',views.EnquiryMarkFollowUp.as_view(),name='enqMarkFollowUp'),
    path('enquiryDelete/<uuid:uid>', views.EnquiryDeleteView.as_view(), name='enqDelete'),

    path('referrer', views.ReferrerView.as_view(), name='enqReferrerCreate'),
    path('referrer/<uuid:uid>', views.ReferrerView.as_view(), name='enqReferrerUpdate'),
    path('referrerEmail/<uuid:uid>', views.ReferralEmail.as_view(), name='enqReferrerEmail'),

    path('dataLoad',views.DataLoad.as_view(),name='dataLoad')
]

