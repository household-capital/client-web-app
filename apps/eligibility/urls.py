from django.urls import path


from . import views

app_name = 'eligibility'

urlpatterns = [
    path('', views.LandingView.as_view(), name='input'),
    path('email', views.EmailView.as_view(), name='email'),

]


