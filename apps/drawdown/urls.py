# Django Imports
from django.urls import path

# Local Application Imports
from . import views

app_name = 'drawdown'

urlpatterns = [

   # Unauthenticated Views

    path('income', views.IncomeInputView.as_view(), name="incomeInput"),
    path('incomeOutput/<uuid:uid>', views.IncomeOutputView.as_view(), name="incomeOutput"),
    path('incomeOutputPostcode/<uuid:uid>', views.IncomeOutputPostcode.as_view(), name='incomeOutputPostcode'),
    path('incomeOutputAge/<uuid:uid>', views.IncomeOutputAge.as_view(), name='incomeOutputAge'),
    path('addressComplete', views.AddressComplete.as_view(), name='addressComplete')

]



