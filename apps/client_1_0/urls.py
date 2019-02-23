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

    path('final', views.Final.as_view(), name='final'),
    path('final_error', views.FinalError.as_view(), name='final_error'),

    path('PdfProduction', views.PdfProduction.as_view(), name='PdfProduction'),
    path('PdfReport/<uuid:uid>', views.PdfReport.as_view()),
    path('PdfRespLending/<uuid:uid>', views.PdfRespLending.as_view())

]


