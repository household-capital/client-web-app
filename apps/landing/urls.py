from django.urls import path


#from . import views
from apps.case import views

app_name = 'landing'

urlpatterns = [
    path('', views.CaseListView.as_view(), name='landing'),
]
