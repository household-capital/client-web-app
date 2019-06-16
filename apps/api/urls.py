#Django Imports
from django.urls import path

#Third-party Imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#Local Application Imports
from . import views


app_name = 'api'

urlpatterns = [
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    path('statusView', views.StatusAPIView.as_view(), name='status'),
    path('statusDetailView/<uuid:enqUID>', views.StatusAPIDetailView.as_view(), name='statusDetail'),
    path('listView', views.APIListView.as_view(), name='listView'),
    path('createView', views.APICreateView.as_view(), name='createView'),
    path('detailView/<uuid:enqUID>', views.APIDetailView.as_view(), name='detailView'),
    path('updateView/<uuid:enqUID>', views.APIUpdateView.as_view(), name='updateView'),
    path('deleteView/<uuid:enqUID>', views.APIDeleteView.as_view(), name='deleteView'),

]

