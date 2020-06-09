# Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'case'

urlpatterns = [

    #Authenticated Views

    path('caseList' ,views.CaseListView.as_view() ,name='caseList'),
    path('caseCreate', views.CaseCreateView.as_view(),name='caseCreate'),
    path('caseDetail/<uuid:uid>' ,views.CaseDetailView.as_view() ,name='caseDetail'),
    path('caseDelete/<uuid:uid>', views.CaseDeleteView.as_view(), name='caseDelete'),
    path('caseClose/<uuid:uid>', views.CaseCloseView.as_view(), name='caseClose'),
    path('caseUnclose/<uuid:uid>', views.CaseUncloseView.as_view(), name='caseUnclose'),
    path('caseAnalysis/<int:pk>', views.CaseAnalysisView.as_view(), name='caseAnalysis'),
    path('caseEmailLoanSummary/<uuid:uid>', views.CaseEmailLoanSummary.as_view(), name = 'caseEmailLoanSummary'),
    path('caseMailLoanSummary/<uuid:uid>/<int:pk>', views.CaseMailLoanSummary.as_view(), name='caseMailLoanSummary'),
    path('caseOwn/<uuid:uid>',views.CaseOwnView.as_view(),name='caseOwn'),
    path('caseAssign/<uuid:uid>', views.CaseAssignView.as_view(), name='caseAssign'),
    path('caseData/<uuid:uid>',views.CaseDataExtract.as_view(),name='caseData'),
    path('caseSMS/<uuid:uid>', views.SMSCustomerView.as_view(), name='caseSMS'),

    path('cloudBridge/<uuid:uid>', views.CloudbridgeView.as_view(), name='cloudBridge'),

    path('caseVariation/<uuid:uid>', views.CaseVariation.as_view(), name='caseVariation'),
    path('caseVariationLumpSum/<uuid:purposeUID>' , views.CaseVariationLumpSum.as_view(), name='caseVariationLumpSum'),
    path('caseVariationDrawdown/<uuid:purposeUID>', views.CaseVariationDrawdown.as_view(), name='caseVariationDrawdown'),
    path('caseVariationAdd/<uuid:uid>', views.CaseVariationAdd.as_view(), name='caseVariationAdd'),
    path('pdfLoanVariationSummary/<uuid:uid>', views.PdfLoanVariationSummary.as_view(), name='pdfLoanVariationSummary'),
    path('createLoanVariationSummary/<uuid:uid>', views.CreateLoanVariationSummary.as_view(), name='createLoanVariationSummary'),

]



