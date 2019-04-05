#Django Imports
from django.urls import path


from . import views

app_name = 'client'

urlpatterns = [
    path('meeting/<uuid:uid>', views.LandingView.as_view(), name='meeting'),
    path('meeting/start', views.LandingView.as_view(), name='meetingStart'),
    path('meeting/start/<int:post_id>/', views.LandingView.as_view()),

    path('reviewclient', views.SetClientView.as_view(), name='setClient'),
    path('settings', views.SettingsView.as_view(), name='settings'),

    path('introduction1', views.IntroductionView1.as_view(), name='introduction1'),
    path('introduction2', views.IntroductionView2.as_view(), name='introduction2'),
    path('introduction3', views.IntroductionView3.as_view(), name='introduction3'),
    path('introduction3/<int:post_id>/', views.IntroductionView3.as_view()),
    path('introduction4', views.IntroductionView4.as_view(), name='introduction4'),
    path('introduction4/<int:post_id>/', views.IntroductionView4.as_view()),

    path('topUp1', views.TopUp1.as_view(), name='topUp1'),
    path('topUp1/<int:post_id>/', views.TopUp1.as_view() ),
    path('topUp2', views.TopUp2.as_view(), name='topUp2'),
    path('topUp3', views.TopUp3.as_view(), name='topUp3'),

    path('give', views.Give.as_view(), name='give'),

    path('live1', views.Live1.as_view(), name='live1'),
    path('live2', views.Live2.as_view(), name='live2'),

    path('care', views.Care.as_view(), name='care'),

    path('results1', views.Results1.as_view(), name='results1'),
    path('results2', views.Results2.as_view(), name='results2'),
    path('results3', views.Results3.as_view(), name='results3'),
    path('results4', views.Results4.as_view(), name='results4'),

    path('final', views.FinalView.as_view(), name='final'),
    path('finalPdf', views.FinalPDFView.as_view(), name='finalPdf'),
    path('finalError', views.FinalErrorView.as_view(), name='finalError'),

    path('pdfLoanSummary/<uuid:uid>', views.PdfLoanSummary.as_view(),name='pdfLoanSummary'),
    path('pdfRespLending/<uuid:uid>', views.PdfRespLending.as_view(), name='pdfRespLending'),
    path('pdfPrivacy/<uuid:uid>', views.PdfPrivacy.as_view(), name='pdfPrivacy'),
    path('pdfElectronic/<uuid:uid>', views.PdfElectronic.as_view(), name='pdfElectronic'),
    path('pdfClientData/<uuid:uid>', views.PdfClientData.as_view(), name='pdfClientData'),
    path('pdfInstruction/<uuid:uid>', views.PdfInstruction.as_view(), name='pdfInstruction'),
    path('pdfValInstruction/<uuid:uid>', views.PdfValInstruction.as_view(), name='pdfValInstruction')
]


