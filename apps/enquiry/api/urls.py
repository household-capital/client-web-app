#Django Imports
from django.urls import path

#Local Application Imports
from . import views


urlpatterns = [
    path('statusView', views.StatusAPIView.as_view(), name='status'),
    path('statusDetailView/<uuid:enqUID>', views.StatusAPIDetailView.as_view(), name='statusDetail'),
    path('listView', views.APIListView.as_view(), name='listView'),
    path('createView', views.APICreateView.as_view(), name='createView'),
    path('detailView/<uuid:enqUID>', views.APIDetailView.as_view(), name='detailView'),
    path('updateView/<uuid:enqUID>', views.APIUpdateView.as_view(), name='updateView'),
    path('deleteView/<uuid:enqUID>', views.APIDeleteView.as_view(), name='deleteView'),

]