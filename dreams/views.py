import os, requests

from django.conf import settings
from django.contrib.auth import get_user_model
from lumaai import LumaAI
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dreams.serializers import DreamSerializer

User = get_user_model()

# Create your views here.
class CreateDreamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy
        data['user_id'] = request.user.id

        serializer = DreamSerializer(data=data)

        if serializer.is_valid():
            client = LumaAI(auth_token=os.getenv('LUMAAI_API_KEY'))
            prompt = data.get('content')
            try:
                generation = client.generations.create(prompt=prompt)
                while generation.state not in ["completed", "failed"]:
                    generation = client.generations.get(id=generation.id)
                if generation.state == "failed":
                    return Response({"error": "LumaAI가 영상 생성에 실패하였습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                video_url = generation.assets.video
                video_response = requests.get(video_url, stream=True)

                video_path = f'videos/{generation.id}.mp4'
                full_video_path = os.path.join(settings.MEDIA_ROOT, video_path)

                os.makedirs(os.path.dirname(full_video_path), exist_ok=True)

                with open(full_video_path, 'wb') as video_file:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        video_file.write(chunk)

                data['video'] = video_path
                dream = serializer.save()

                return Response(DreamSerializer(dream).data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dreams.serializers import DreamSerializer
from dreams.models import Dreams


class ListUserDreamsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 요청자(user_id)에 해당하는 꿈 리스트 가져오기
        dreams = Dreams.objects.filter(user_id=request.user.id)
        serializer = DreamSerializer(dreams, many=True)

        # 꿈 리스트 반환
        return Response(serializer.data, status=status.HTTP_200_OK)