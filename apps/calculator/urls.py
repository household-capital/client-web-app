#Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.InputView.as_view()),
    path('input' ,views.InputView.as_view() ,name='calcInput'),
    path('input/<uuid:uid>', views.InputView.as_view(), name='calcInputItem'),
    path('output/<uuid:uid>/', views.OutputView.as_view(), name='calcOutput'),

    path('calcList', views.CalcListView.as_view(), name='calcList'),
    path('calcSpam/<uuid:uid>', views.CalcMarkSpam.as_view(), name='calcSpam'),
    path('calcSendDetail/<uuid:uid>', views.CalcSendDetails.as_view(), name='calcSendDetails'),
    path('calcSummaryPdf/<uuid:uid>', views.CalcSummaryPdfView.as_view(), name='calcSummaryPdf'),

    path('contact',views.ContactView.as_view(),name='webContact'),
    path('contactList', views.ContactListView.as_view(), name='contactList'),
    path('contactDetail/<uuid:uid>', views.ContactDetailView.as_view(), name='contactDetail'),
    path('contactAction/<uuid:uid>', views.ContactActionView.as_view(), name='contactAction'),
    path('contactDelete/<uuid:uid>', views.ContactDeleteView.as_view(), name='contactDelete'),

]



