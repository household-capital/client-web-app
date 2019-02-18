from django.urls import path


from . import views

app_name = 'case'

urlpatterns = [
    path('caseList' ,views.CaseListView.as_view() ,name='caseList'),
    path('caseCreate', views.CaseCreateView.as_view(),name='caseCreate'),
    path('caseDetail/<int:pk>' ,views.CaseDetailView.as_view() ,name='caseDetail'),
    path('emailSummary/<int:pk>', views.EmailSummary.as_view(), name='emailSummary')

]

