#Django Imports
from django.urls import path, include

#Local Application Imports
from . import views

app_name = 'relationship'

urlpatterns = [

    #Authenticated Views

    path('', views.ContactListView.as_view(),name='contactList'),
    path('contact/<int:contId>', views.ContactDetailView.as_view(), name='contactDetail'),
    path('contactCreate', views.ContactDetailView.as_view(), name='contactCreate'),
    path('contactDelete/<int:contId>', views.ContactDelete.as_view(), name='contactDelete'),
    path('organisationCreate', views.OrganisationCreateView.as_view(), name='organisationCreate'),
    path('exportCSV', views.ExportCSV.as_view(), name='exportCSV'),
    path('exportStatusCSV', views.ExportStatusCSV.as_view(), name='exportStatusCSV'),

]

