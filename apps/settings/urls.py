from django.urls import path, re_path

from . import views

app_name = 'settings'

urlpatterns = [
     # Authenticated Views
     path('global', views.GlobalSettingView.as_view(), name='globalSettings'),
]