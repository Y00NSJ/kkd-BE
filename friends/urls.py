from django.urls import path
from .views import *

urlpatterns = [
    path('send/', SendRequestView.as_view(), name='send'),
    path('incoming/', ShowIncomingRequestsView.as_view(), name='incoming'),
    path('respond/<int:request_id>/', RespondToRequestView.as_view(), name='respond'),
    path('list/', FriendListView.as_view(), name='friend_list'),  # 친구 목록 보기
    path('delete/<int:friend_id>/', DeleteFriendView.as_view(), name='delete_friend'),  # 친구 삭제
]