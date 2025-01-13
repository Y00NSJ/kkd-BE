from django.urls import path
from .views import *

urlpatterns = [
    path('create/', CreateDreamView.as_view(), name='create-dream'),
    path('list/', ListUserDreamsView.as_view(), name='list-dreams'),
    path('list/<int:dream_id>/', DreamDetailView.as_view(), name='dream-detail'),
]