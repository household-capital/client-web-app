from django.urls import path

# from . import views
from . import views

app_name = 'landing'

urlpatterns = [

    # Authenticated Views

    path('', views.LandingView.as_view(), name='landing'),
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),

]
