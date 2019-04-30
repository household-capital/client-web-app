#Django Imports
from django.urls import path

#Local Application Imports
from . import views


urlpatterns = [
    path('view', views.APIView.as_view(), name='view'),
    path('listView', views.APIListView.as_view(), name='listView'),
    path('createView', views.APICreateView.as_view(), name='createView'),
    path('detailView/<int:pk>', views.APIDetailView.as_view(), name='detailView'),

]