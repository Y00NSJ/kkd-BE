from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from friends.serializers import *

# Create your views here.
User = get_user_model()

class SendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        receive_id = request.data.get('receive_id')  # receive_id를 본문에서 가져옴
        if not receive_id:
            return Response({"error": "받는 사람의 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        receive = get_object_or_404(User, id=receive_id)
        if receive == request.user:
            return Response({"error": "자기 자신은 친구 추가할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "request_id": request.user.id,
            "receive_id": receive_id
        }
        serializer = FriendRequestSerializer(data=data)
        if serializer.is_valid():
            created_request = serializer.save()
            return Response({"message": str(created_request)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShowIncomingRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        incoming_requests = FriendsRequests.objects.filter(receive_id=request.user.id, status='pending')
        serializer = FriendRequestSerializer(incoming_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RespondToRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        action = request.data.get('action')
        if action not in ['accept', 'reject']:
            return Response({"error": "친구 신청에 대한 응답은 수락 혹은 거절이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        incoming_request = get_object_or_404(FriendsRequests, id=request_id, receive_id=request.user.id)
        if action == 'accept':
            incoming_request.status = 'accepted'
            incoming_request.save()

            user1 = min(incoming_request.request_id, incoming_request.receive_id)
            user2 = max(incoming_request.request_id, incoming_request.receive_id)
            data  = {
                "user1_id": user1,
                "user2_id": user2
            }
            serializer = FriendsSerializer(data=data)
            if serializer.is_valid():
                matched_friend = serializer.save()
                return Response({"message": "친구 신청을 수락했습니다: " + str(matched_friend)}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'reject':
            incoming_request.status = 'rejected'
            mismatched_friend = incoming_request.save()
            return Response({"message": "친구 신청을 거절했습니다: "+ str(mismatched_friend)}, status=status.HTTP_200_OK)


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = Friends.objects.filter(models.Q(user1=request.user) | models.Q(user2=request.user))
        serializer = FriendListSerializer(friends, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        serializer =DeleteFriendSerializer(data={}, context={'request': request, 'friend_id': friend_id})
        if serializer.is_valid():
            friend = serializer.validated_data['friend']
            friend.delete()
            return Response({"message": "친구가 삭제되었습니다."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)