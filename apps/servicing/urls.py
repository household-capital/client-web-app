from django.urls import path

#Local Application Imports
from . import views

app_name = 'servicing'

urlpatterns = [
     path('loanList', views.LoanListView.as_view(), name='loanList'),
     path('loanDetail/<uuid:uid>', views.LoanDetailView.as_view(), name='loanDetail'),
     path('loanDetailBalances/<uuid:uid>', views.LoanDetailBalances.as_view(), name='loanDetailBalances'),
     path('loanDetailRoles/<uuid:uid>', views.LoanDetailRoles.as_view(), name='loanDetailRoles'),
     path('loanDetailProperty/<uuid:uid>', views.LoanDetailProperty.as_view(), name='loanDetailProperty'),
     path('loanDetailPurposes/<uuid:uid>', views.LoanDetailPurposes.as_view(), name='loanDetailPurposes'),
     path('loanEnquiries', views.LoanEnquiryList.as_view(), name='loanEnquiryList'),
     path('loanEnquiryUpdate/<uuid:uid>/<int:pk>', views.LoanEnquiryUpdate.as_view(), name='loanEnquiryUpdate'),
     path('loanEnquiry/<uuid:uid>', views.LoanEnquiry.as_view(), name='loanEnquiry'),
     path('loanEvents', views.LoanEventList.as_view(), name='loanEventList'),

]