#Django Imports
from django.urls import path

#Third-party Imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#Local Application Imports
from . import views


app_name = 'api'

urlpatterns = [
    path('test', views.TEST.as_view(), name='token_obtain_pair'),

]

