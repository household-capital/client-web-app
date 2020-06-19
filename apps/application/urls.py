# Django Imports
from django.urls import path, re_path

#Third-party Imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


#Local Application Imports
from . import views

app_name = 'application'

urlpatterns = [
    # AUTHENTICATED VIEWS


    # UNAUTHENTICATED VIEWS

    #Document print views
    path('pdfLoanSummary/<uuid:uid>', views.PdfLoanSummary.as_view(), name='pdfLoanSummary'),
    path('pdfApplication/<uuid:uid>', views.PdfApplication.as_view(), name='pdfApplication'),

    #API views
    path('api/token/get', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/create', views.CreateApplication.as_view(), name="createApplication"),

    #Session validation
    re_path(r'^validateReturn/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.ValidateReturn.as_view(),
            name='validateReturn'),

    re_path(r'^validateStart/(?P<signed_pk>[A-Za-z0-9_:=-]+)/$', views.ValidateStart.as_view(),
            name='validateStart'),

    path('sessionError', views.SessionErrorView.as_view(), name='sessionError'),
    path('validationError', views.ValidationErrorView.as_view(), name='validationError'),

    #Session workflow views
    path('start', views.StartApplicationView.as_view(), name='start'),
    path('resume', views.ResumeApplicationView.as_view(), name='resume'),
    path('generatePin/<slug:returnPage>', views.GeneratePin.as_view(), name="generatePin"),

    #About
    path('introduction', views.EligibilityView.as_view(), name='introduction'),
    path('consents', views.ConsentsView.as_view(), name='consents'),
    path('applicant', views.Applicant1View.as_view(), name='applicant1'),
    path('additionalApplicant', views.Applicant2View.as_view(), name='applicant2'),

    #Product
    path('productOverview', views.ProductView.as_view(), name='product'),

    #Objectives
    path('objectives', views.ObjectivesView.as_view(), name='objectives'),
    path('sliderUpdate',views.SliderUpdate.as_view(), name='sliderUpdate'),

    #Projections
    path('projections', views.ProjectionsView.as_view(), name='projections'),
    path('sendLoanSummary', views.SendLoanSummary.as_view(), name='sendLoanSummary'),

    #Application
    path('assets', views.AssetsView.as_view(), name='assets'),
    path('income', views.IncomeView.as_view(), name='income'),
    path('homeExpenses', views.HomeExpensesView.as_view(), name='homeExpenses'),
    path('bank', views.BankView.as_view(), name='bank'),
    path('declarations', views.DeclarationsView.as_view(), name='declarations'),

    #Next Stpes
    path('nextSteps', views.NextStepsView.as_view(), name='nextSteps'),
    path('documents', views.DocumentsView.as_view(), name='documents'),

    # Application Exit Views
    path('exit', views.ExitView.as_view(), name='exit'),
    path('submitted', views.SubmittedView.as_view(), name='submitted'),
    path('exitProduct', views.ExitProductView.as_view(), name='exitProduct'),
    path('minimum', views.MinimumView.as_view(), name='minimum'),
    path('maximum', views.MaximumView.as_view(), name='maximum'),
    path('multiple', views.MultiplePurposesView.as_view(), name='multiPurpose'),
    path('contact', views.ContactView.as_view(), name='contactMe'),
    path('ownership', views.OwnershipView.as_view(), name='ownership'),
    path('mortgage', views.MortgageView.as_view(), name='mortgage'),
    path('age', views.AgeView.as_view(), name='age'),
    path('error', views.SystemError.as_view(), name='systemError'),

]



