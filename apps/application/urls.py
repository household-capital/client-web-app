# Django Imports
from django.urls import path, re_path

#Local Application Imports
from . import views

app_name = 'application'

urlpatterns = [
    # Authenticated Views


    # Externally Exposed Views
    path('sessionError', views.SessionErrorView.as_view(), name='sessionError'),
    path('validationError', views.ValidationErrorView.as_view(), name='validationError'),
    path('apply', views.InitiateView.as_view(), name='initiate'),
    re_path(r'^validate/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.Validate.as_view(), name='validate'),

    # Session Validated Views
    path('introduction', views.IntroductionView.as_view(), name='introduction'),

]


