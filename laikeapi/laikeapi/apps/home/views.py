from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_redis import get_redis_connection
from django.http import HttpResponse


# Create your views here.
class HomeAPIView(APIView):
    def get(self, request):
        redis = get_redis_connection("sms_code")
        brother = redis.lrange("brother", 0, -1)
        return Response(brother, status.HTTP_200_OK)


def login(request):
    return HttpResponse('ok')