from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from friends.models import FriendsRequests, Friends

User = get_user_model()


class FriendsViewsTestCase(APITestCase):
    def setUp(self):
        """
        테스트를 위한 초기 설정
        """
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password="password1")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password2")
        self.user3 = User.objects.create_user(username="user3", email="user3@example.com", password="password3")

        self.client1 = APIClient()
        self.client2 = APIClient()

        self.user1_tokens = self.get_tokens_for_user(self.user1, self.client1)
        self.user2_tokens = self.get_tokens_for_user(self.user2, self.client2)

        self.client1.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_tokens["access"]}')
        self.client2.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user2_tokens["access"]}')

    def get_tokens_for_user(self, user, client):
        """
        주어진 사용자의 JWT 토큰을 반환
        """
        response = client.post('/api/token/', {"username": user.username, "password": "password1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_send_friend_request(self):
        """
        친구 요청 보내기 테스트
        """
        response = self.client1.post(
            "/api/friends/send/",
            data={"receive_id": self.user2.id},  # receive_id를 본문에 포함
            format="json"  # 요청 데이터 형식 지정
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FriendsRequests.objects.count(), 1)
        self.assertEqual(FriendsRequests.objects.first().request_id, self.user1.id)

    def test_cannot_send_request_to_self(self):
        """
        자신에게 친구 요청을 보낼 수 없는지 확인
        """
        response = self.client1.post(
            "/api/friends/send/",
            data={"receive_id": self.user1.id},  # 자신에게 요청
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("자기 자신은 친구 추가할 수 없습니다.", response.data["error"])

    def test_show_incoming_requests(self):
        """
        받은 친구 요청 리스트 확인 테스트
        """
        FriendsRequests.objects.create(request_id=self.user1.id, receive_id=self.user2.id, status="pending")
        response = self.client2.get("/api/friends/incoming-requests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["request_id"], self.user1.id)

    def test_accept_friend_request(self):
        """
        친구 요청 수락 테스트
        """
        friend_request = FriendsRequests.objects.create(request_id=self.user1.id, receive_id=self.user2.id, status="pending")
        response = self.client2.post(f"/api/friends/respond-request/{friend_request.id}/", data={"action": "accept"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FriendsRequests.objects.first().status, "accepted")
        self.assertEqual(Friends.objects.count(), 1)

    def test_reject_friend_request(self):
        """
        친구 요청 거절 테스트
        """
        friend_request = FriendsRequests.objects.create(request_id=self.user1.id, receive_id=self.user2.id, status="pending")
        response = self.client2.post(f"/api/friends/respond-request/{friend_request.id}/", data={"action": "reject"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FriendsRequests.objects.first().status, "rejected")
        self.assertEqual(Friends.objects.count(), 0)

    def test_friend_list(self):
        """
        친구 목록 조회 테스트
        """
        Friends.objects.create(user1=self.user1, user2=self.user2)
        response = self.client1.get("/api/friends/friend-list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["friend_id"], self.user2.id)

    def test_delete_friend(self):
        """
        친구 삭제 테스트
        """
        friendship = Friends.objects.create(user1=self.user1, user2=self.user2)
        response = self.client1.delete(f"/api/friends/delete-friend/{self.user2.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Friends.objects.count(), 0)