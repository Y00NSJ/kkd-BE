import os, requests, time

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
from rest_framework import status


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from dreams.serializers import DreamSerializer

from dreams.models import Dreams
class CreateDreamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("Request Data:", request.data)  # 요청 데이터 확인
        data = request.data.copy()
        data['user_id'] = request.user.id

        serializer = DreamSerializer(data=data)

        if not serializer.is_valid():
            print("Validation Errors:", serializer.errors)  # 유효성 검사 실패 출력
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        print("Serializer is valid. Proceeding with video generation.")

        # 비디오 생성 및 저장
        try:
            video_path = self._generate_and_save_video(data.get('content'))
            print("Video successfully saved at:", video_path)
        except Exception as e:
            print("Error during video generation or saving:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 데이터베이스 저장
        try:
            data['video'] = video_path  # 비디오 경로 추가
            dream = serializer.save()  # Dream 데이터 저장
            print("Dream successfully saved:", dream)
            return Response(DreamSerializer(dream).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Error during database save:", str(e))
            # 비디오 삭제 (필요 시)
            if os.path.exists(video_path):
                os.remove(video_path)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_and_save_video(self, prompt):
        print("Initializing LumaAI client...")
        client = LumaAI(auth_token=os.getenv('LUMAAI_API_KEY'))

        print("Sending prompt to LumaAI:", prompt)
        generation = client.generations.create(prompt=prompt)

        start_time = time.time()
        timeout = 300  # 5분

        while generation.state not in ["completed", "failed"]:
            print(f"Generation state: {generation.state}")
            generation = client.generations.get(id=generation.id)

            if time.time() - start_time > timeout:
                print("Video generation timed out.")
                raise Exception("LumaAI video generation timed out")

            time.sleep(5)

        if generation.state == "failed":
            error_details = generation.error if hasattr(generation, 'error') else "Unknown error"
            print("LumaAI video generation failed:", error_details)
            raise Exception(f"LumaAI video generation 실패: {error_details}")

        print("Video generation completed.")
        video_url = generation.assets.video
        print("Video URL:", video_url)

        try:
            video_response = requests.get(video_url, stream=True)
            video_path = f'videos/{generation.id}.mp4'
            full_video_path = os.path.join(settings.MEDIA_ROOT, video_path)
            print("Saving video to:", full_video_path)

            os.makedirs(os.path.dirname(full_video_path), exist_ok=True)
            with open(full_video_path, 'wb') as video_file:
                for chunk in video_response.iter_content(chunk_size=8192):
                    video_file.write(chunk)

            print("Video successfully saved.")
            return video_path

        except Exception as e:
            print("Error during video save:", str(e))
            raise


class ListUserDreamsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 요청자(user_id)에 해당하는 꿈 리스트 가져오기
        dreams = Dreams.objects.filter(user_id=request.user.id)
        serializer = DreamSerializer(dreams, many=True)

        # 꿈 리스트 반환
        return Response(serializer.data, status=status.HTTP_200_OK)


class DreamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dream_id):
        try:
            dream = Dreams.objects.get(id=dream_id, user_id=request.user.id)
            serializer = DreamSerializer(dream)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Dreams.DoesNotExist:
            return Response(
                {"error": "해당 꿈을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )