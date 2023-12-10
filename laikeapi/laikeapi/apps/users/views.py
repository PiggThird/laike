from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .serializers import UserSerializer, UserRegisterModelSerializer
from rest_framework.decorators import action
from .models import User
from rest_framework import status
from django_redis import get_redis_connection


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


class UserAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterModelSerializer


class SendSmSView(APIView):
    # throttle_classes = [throttles.SMSThrottle]

    def get(self, request, mobile):
        """
        发送短信验证码接口
        :return:
        """
        import re
        from laikeapi.libs.tx_sms import get_code, send_message
        from django.conf import settings
        """发送短信验证码"""
        redis = get_redis_connection("sms_code")
        # 判断手机短信是否处于发送冷却中[60秒只能发送一条]
        interval = redis.ttl(f"interval_{mobile}")  # 通过ttl方法可以获取保存在redis中的变量的剩余有效期
        if interval != -2:
            return Response(
                {"errmsg": f"短信发送过于频繁，请{interval}秒后再次点击获取!", "interval": interval},
                status=status.HTTP_400_BAD_REQUEST
            )
        code = get_code()
        send_message(mobile, code)

        # 记录code到redis中，并以time作为有效期
        # 使用redis提供的管道对象pipeline来优化redis的写入操作[添加/修改/删除]
        pipe = redis.pipeline()
        pipe.multi()  # 开启事务
        pipe.setex(f"sms_{mobile}", 180, code)
        pipe.setex(f"interval_{mobile}", 60, "_")
        pipe.execute()  # 提交事务，同时把暂存在pipeline的数据一次性提交给redis

        return Response({"errmsg": "OK"}, status=status.HTTP_200_OK)