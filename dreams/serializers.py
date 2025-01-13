from rest_framework import serializers

from dreams.models import Dreams


class DreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dreams
        fields = ['id', 'title', 'content', 'user_id', 'video', 'interpret', 'created_at']
        read_only_fields = ['id', 'user_id', 'created_at']