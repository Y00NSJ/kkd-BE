from rest_framework import serializers
from django.db import models

from friends.models import FriendsRequests, Friends


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRequests
        fields = ['id', 'request_id', 'receive_id', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ['id', 'user1_id', 'user2_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class FriendListSerializer(serializers.ModelSerializer):
    friend_id = serializers.SerializerMethodField()
    friend_name = serializers.SerializerMethodField()

    class Meta:
        model = Friends
        fields = ['friend_id', 'friend_name']

    def get_friend_id(self, obj):
        request_user = self.context['request'].user
        return obj.user1.id if obj.user2 == request_user else obj.user2.id

    def get_friend_name(self, obj):
        request_user = self.context['request'].user
        return obj.user1.username if obj.user2 == request_user else obj.user2.username


class DeleteFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ['user1', 'user2']

    def validate(self, attrs):
        request_user = self.context['request'].user
        friend_id = self.context['friend_id']
        friend_relation = Friends.objects.filter(
            models.Q(user1=request_user, user2__id=friend_id) |
            models.Q(user2=request_user, user1__id=friend_id)
        ).first()

        if not friend_relation:
            raise serializers.ValidationError("Friendship not found.")
        return {'friend_relation': friend_relation}