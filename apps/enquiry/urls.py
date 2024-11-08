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
    path('enquiryAssign/<uuid:uid>', views.EnquiryAssignView.as_view(), name='enqAssign'),
    path('enquiryCreateSummary/<uuid:uid>',views.CreateEnquirySummary.as_view(),name='enqCreateSummary'),
    path('enquirySendDetail/<uuid:uid>', views.SendEnquirySummary.as_view(), name='enqSendDetails'),
    path('enquiryEligibility/<uuid:uid>',views.EnquiryEmailEligibility.as_view(), name='enqEligibility'),
    path('enquiryDelete/<uuid:uid>', views.EnquiryDeleteView.as_view(), name='enqDelete'),
    path('enquiryPartnerUpload', views.EnquiryPartnerUpload.as_view(), name='enqPartnerUpload'),
    path('enquiryPartnerList', views.EnquiryPartnerList.as_view(), name='enqPartnerList'),
    path('notes/<uuid:uid>', views.EnquiryNotesView.as_view(), name='enquiryNotes'),
    path('enquiryOwn/<uuid:uid>', views.EnquiryOwnView.as_view(), name='enquiryOwn'),

    # Ajax Views
    path('addressComplete', views.AddressComplete.as_view(), name='addressComplete'),

    #Unauthenticated Views
    path('enquirySummaryPdf/<uuid:uid>', views.EnqSummaryPdfView.as_view(), name='enqSummaryPdf'),

    # API Views 
    path('api/', include('apps.enquiry.api_urls')),

    path('EMAILPdfView/<uuid:uid>', views.EMAILPdfView.as_view(), name='lol'),

]

