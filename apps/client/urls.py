from django.urls import path


from . import views

app_name = 'client'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('introduction1', views.IntroductionView1.as_view(), name='introduction1'),
    path('introduction2', views.IntroductionView2.as_view(), name='introduction2'),
    path('introduction3', views.IntroductionView3.as_view(), name='introduction3'),
    path('introduction4', views.IntroductionView4.as_view(), name='introduction4'),
    path('introduction4/<int:post_id>/', views.IntroductionView4.as_view()),

    path('topUp1', views.TopUp1.as_view(), name='topUp1'),
    path('topUp1/<int:post_id>/', views.TopUp1.as_view() ),
    path('topUp2', views.TopUp2.as_view(), name='topUp2'),

    path('setclient', views.SetClientView.as_view(), name='setClient'),
    path('settings', views.SettingsView.as_view(), name='settings'),
    path('pdfResults', views.pdfView.as_view(), name='pdfResults'),

]


