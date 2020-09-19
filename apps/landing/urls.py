from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [

    #Authenticated Views

    path('', views.LandingView.as_view(), name='landing'),
    path('dashboard',views.DashboardView.as_view(),name='dashboard'),

    #Obscured views ~ temporary
    path('dashboard/weekly',views.Weekly.as_view(),name='weekly'),
    path('calculatorExtract', views.CalculatorExtract.as_view(), name='calculatorExtract'),
    path('enquiryExtract', views.EnquiryExtract.as_view(), name='enquiryExtract'),

]
