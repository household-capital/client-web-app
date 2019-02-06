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
from django.views.static import serve
from django.urls import path, re_path
from django.conf import settings

from apps.landing.views import LandingView

urlpatterns = [
    path('', lambda r: HttpResponseRedirect('landing/')),
    path('accounts/', include('apps.accounts.urls')),
    path('landing/', include('apps.landing.urls')),
    path('eligibility/', include('apps.eligibility.urls')),
    path('client/', include('apps.client_1_0.urls')),
    path('hhcadmin/', admin.site.urls),
    re_path(r'^media/Users/developmentaccount/Development/hhc/static/media/(.*)',serve, {'document_root': settings.MEDIA_ROOT})
]

