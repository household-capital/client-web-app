from django.urls import path
from apps.accounts.views import myLoginView, myPasswordResetView, myPasswordResetDoneView,myLogoutView, myPasswordResetConfirmView,myPasswordResetCompleteView
from django.contrib.auth.views import *


app_name = 'accounts'

urlpatterns = [
    path('login/', myLoginView.as_view(), name="login"),
    path('logout/', myLogoutView.as_view(), name="logout"),
    path('password_reset/done/', myPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset/',myPasswordResetView.as_view(),name='password_reset'),
    path('reset/<uidb64>/<token>/',myPasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('reset/done/',myPasswordResetCompleteView.as_view(),name='password_reset_complete'),
]
