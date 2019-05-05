from django.urls import path


#from . import views
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('dashboard',views.DashboardView.as_view(),name='dashboard'),
    path('dashboardCalc', views.DashboardCalcView.as_view(), name='dashboardCalc')

]
