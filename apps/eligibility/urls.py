from django.urls import path


from . import views

app_name = 'eligibility'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('email', views.EmailView.as_view(), name='email'),

]


