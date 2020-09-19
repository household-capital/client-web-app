#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'referrer'

urlpatterns = [

    #Authenticated Views (Referrer)

    path('', views.MainView.as_view(), name='main'),
    path('enquiry', views.EnquiryView.as_view(), name='enqCreate'),
    path('enquiry/<uuid:uid>', views.EnquiryView.as_view(), name='enqUpdate'),
    path('enquiryEmail/<uuid:uid>', views.EnquiryEmail.as_view(), name='enqEmail'),

    path('case', views.CaseCreateView.as_view(), name='caseCreate'),
    path('caseDetail/<uuid:uid>', views.CaseDetailView.as_view(), name='caseDetail'),
    path('caseList', views.CaseListView.as_view(), name='caseList'),

]

