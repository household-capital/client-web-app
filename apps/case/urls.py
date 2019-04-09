# Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'case'

urlpatterns = [
    path('caseList' ,views.CaseListView.as_view() ,name='caseList'),
    path('caseSummary', views.CaseSummaryView.as_view(), name='caseSummary'),
    path('caseCreate', views.CaseCreateView.as_view(),name='caseCreate'),
    path('caseDetail/<int:pk>' ,views.CaseDetailView.as_view() ,name='caseDetail'),
    path('caseDelete/<uuid:uid>', views.CaseDeleteView.as_view(), name='caseDelete'),
    path('caseClose/<uuid:uid>', views.CaseCloseView.as_view(), name='caseClose'),
    path('caseEmailEligibility/<uuid:uid>', views.CaseEmailEligibility.as_view(), name='caseEmailEligibility'),
    path('caseAnalysis/<int:pk>', views.CaseAnalysisView.as_view(), name='caseAnalysis'),
    path('caseEmailLoanSummary/<uuid:uid>', views.CaseEmailLoanSummary.as_view(), name = 'caseEmailLoanSummary'),
    path('caseSalesforce/<uuid:uid>',views.CaseSalesforce.as_view(),name='caseSalesforce'),
    path('caseSolicitor/<uuid:uid>',views.CaseSolicitorView.as_view(), name='caseSolicitor'),
    path('caseValuer/<uuid:uid>', views.CaseValuerView.as_view(), name='caseValuer'),
    path('caseOwn/<uuid:uid>',views.CaseOwnView.as_view(),name='caseOwn'),
    path('caseData/<uuid:uid>',views.CaseDataExtract.as_view(),name='caseData')
]


