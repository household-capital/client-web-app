from django.urls import path, re_path

#Local Application Imports
from . import views

app_name = 'servicing'

urlpatterns = [
     # Authenticated Views
     path('loanList', views.LoanListView.as_view(), name='loanList'),
     path('loanDetail/<uuid:uid>', views.LoanDetailView.as_view(), name='loanDetail'),
     path('loanDetailBalances/<uuid:uid>', views.LoanDetailBalances.as_view(), name='loanDetailBalances'),
     path('loanDetailRoles/<uuid:uid>', views.LoanDetailRoles.as_view(), name='loanDetailRoles'),
     path('loanDetailProperty/<uuid:uid>', views.LoanDetailProperty.as_view(), name='loanDetailProperty'),
     path('loanDetailPurposes/<uuid:uid>', views.LoanDetailPurposes.as_view(), name='loanDetailPurposes'),
     path('loanDetailAnnualList/<uuid:uid>', views.LoanDetailAnnualList.as_view(), name='loanDetailAnnualList'),
     path('loanDetailAnnual/<uuid:uid>', views.LoanDetailAnnual.as_view(), name='loanDetailAnnual'),
     path('loanEnquiries', views.LoanEnquiryList.as_view(), name='loanEnquiryList'),
     path('loanRecentEnquiries', views.LoanRecentEnquiryList.as_view(), name='loanRecentEnquiryList'),
     path('loanEnquiryUpdate/<uuid:uid>/<int:pk>', views.LoanEnquiryUpdate.as_view(), name='loanEnquiryUpdate'),
     path('loanEnquiry/<uuid:uid>', views.LoanEnquiry.as_view(), name='loanEnquiry'),
     path('loanEvents', views.LoanEventList.as_view(), name='loanEventList'),
     path('loanAnnual', views.LoanAnnualList.as_view(), name='loanAnnualList'),
     path('loanAdditionalLink/<uuid:uid>', views.LoanAdditionalLink.as_view(), name='loanAdditionalLink'),
     path('loanCreateVariation/<uuid:uid>', views.LoanCreateVariation.as_view(), name='loanCreateVariation'),
     path('loanAnnualLink/<uuid:uid>', views.LoanAnnualLink.as_view(), name='loanAnnualLink'),

     # Unauthenticated Views
     re_path(r'^loanAdditionalValidate/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.ServicingValidate.as_view(), name='servicingValidate'),
     path('validationError', views.ValidationErrorView.as_view(), name='validationError'),
     path('sessionError', views.SessionErrorView.as_view(), name='sessionError'),

     # Session Validated Views
     path('loanAdditionalRequest', views.LoanAdditionalRequest.as_view(), name='loanAdditionalRequest'),
     path('loanAdditionalConfirm', views.LoanAdditionalConfirm.as_view(), name='loanAdditionalConfirm'),
     path('loanAdditionalThankYou', views.LoanAdditionalThankYou.as_view(), name='loanAdditionalThankYou'),
     path('loanAdditionalSubmitted', views.LoanAdditionalSubmitted.as_view(), name='loanAdditionalSubmitted'),

     path('loanAnnualHousehold', views.LoanAnnualHousehold.as_view(), name='loanAnnualHousehold'),
     path('loanAnnualHome', views.LoanAnnualHome.as_view(), name='loanAnnualHome'),
     path('loanAnnualNeeds', views.LoanAnnualNeeds.as_view(), name='loanAnnualNeeds'),
     path('loanAnnualThankYou', views.LoanAnnualThankYou.as_view(), name='loanAnnualThankYou'),
     path('loanAnnualSubmitted', views.LoanAnnualSubmitted.as_view(), name='loanAnnualSubmitted'),

]