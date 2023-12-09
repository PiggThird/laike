from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .serializers import UserSerializer
from rest_framework.decorators import action


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