# Django Imports
from django.urls import path, re_path

#Third-party Imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


#Local Application Imports
from . import views

app_name = 'application'

urlpatterns = [
    # Authenticated Views


    # Unauthenticated Views
    path('api/token/get', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/create', views.CreateApplication.as_view(), name="createApplication"),

    re_path(r'^validateReturn/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.ValidateReturn.as_view(),
            name='validateReturn'),

    re_path(r'^validateStart/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.ValidateStart.as_view(),
            name='validateStart'),

    path('sessionError', views.SessionErrorView.as_view(), name='sessionError'),
    path('validationError', views.ValidationErrorView.as_view(), name='validationError'),

    path('pdfLoanSummary/<uuid:uid>', views.PdfLoanSummary.as_view(), name = 'pdfLoanSummary'),

    # Session Validated Views (ID Only)
    path('start', views.StartApplicationView.as_view(), name='start'),
    path('resume', views.ResumeApplicationView.as_view(), name='resume'),
    path('generatePin/<slug:returnPage>', views.GeneratePin.as_view(), name="generatePin"),

    # Session Validated Views
    path('consents', views.ConsentsView.as_view(), name='consents'),
    path('introduction', views.IntroductionView.as_view(), name='introduction'),
    path('applicant', views.Applicant1View.as_view(), name='applicant1'),
    path('additionalApplicant', views.Applicant2View.as_view(), name='applicant2'),
    path('productOverview', views.ProductView.as_view(), name='product'),
    path('objectives', views.ObjectivesView.as_view(), name='objectives'),
    path('sliderUpdate',views.SliderUpdate.as_view(), name='sliderUpdate'),
    path('projections', views.ProjectionsView.as_view(), name='projections'),
    path('sendLoanSummary', views.SendLoanSummary.as_view(), name='sendLoanSummary'),
    path('assets', views.AssestView.as_view(), name='assets'),
    path('income', views.IncomeView.as_view(), name='income'),
    path('bank', views.BankView.as_view(), name='bank'),
    path('declarations', views.DeclarationsView.as_view(), name='declarations'),
    path('nextSteps', views.NextStepsView.as_view(), name='nextSteps'),

    path('exit', views.ExitView.as_view(), name='exit'),
    path('minimum', views.MinimumView.as_view(), name='minimum'),
    path('multiple', views.MultiplePurposesView.as_view(), name='multiPurpose'),
    path('contact', views.ContactView.as_view(), name='contactMe'),
    path('ownership', views.OwnershipView.as_view(), name='ownership'),
    path('age', views.AgeView.as_view(), name='age'),
]



