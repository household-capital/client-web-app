#Django Imports
from django.urls import path

#Local Application Imports
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.InputView.as_view()),
    path('input' ,views.InputView.as_view() ,name='calcInput'),
    path('input/<uuid:uid>', views.InputView.as_view(), name='calcInputItem'),
    path('output/<uuid:uid>', views.OutputView.as_view(), name='calcOutput'),
]

