"""household URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', lambda r: HttpResponseRedirect('landing/')),
    path('accounts/', include('apps.accounts.urls')),
    path('application/', include('apps.application.urls')),
    path('calculator/', include('apps.calculator.urls')),
    path('calendly/', include('apps.calendly.urls')),
    path('case/', include('apps.case.urls')),
    path('client2/', include('apps.client_2_0.urls')),
    path('enquiry/', include('apps.enquiry.urls')),
    path('factfind/', include('apps.fact_find.urls')),
    path('hhcadmin/', admin.site.urls),
    path('landing/', include('apps.landing.urls')),
    path('referrer/', include('apps.referrer.urls')),
    path('servicing/', include('apps.servicing.urls')),
    path('settings/', include('apps.settings.urls')),
    path('comments/', include('django_comments.urls')),
    path('comments/', include("comments_extension.urls")),
]

urlpatterns+=static('/static/', document_root=settings.STATIC_ROOT)
urlpatterns+=static('/media/', document_root=settings.MEDIA_ROOT)


