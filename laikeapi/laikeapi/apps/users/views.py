from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .serializers import UserSerializer
from rest_framework.decorators import action
from .models import User
from rest_framework import status


# Create your views here.
class LoginView(ViewSet):
    @action(methods=['POST'], detail=False)
    def login(self, request, *args, **kwargs):
        ser = UserSerializer(data=request.data)
        if ser.is_valid():
            token = ser.context.get('token')
            username = ser.context.get('user').username
            return Response({'code': 0, 'username': username, 'token': token})
        else:
            return Response({'code': 1, 'msg': ser.errors})


class MobileView(APIView):
    def get(self, request, mobile):
        """
        校验手机号是否已注册
        :param request:
        :param mobile: 手机号
        :return:
        """
        try:
            User.objects.get(mobile=mobile)
            return Response({"errmsg": "当前手机号已经注册！"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            # 如果查不到该手机号的注册记录，则证明手机号可以注册使用
            return Response({"errmsg": "手机号未注册，欢迎注册！"}, status=status.HTTP_200_OK)