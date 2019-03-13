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

]

