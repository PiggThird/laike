from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ['username', 'password', 'id']
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        user = self._get_user(attrs)
        token = self._get_token(user)
        self.context['user'] = user
        self.context['token'] = token
        return attrs

    def _get_user(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        import re
        if re.match('^1[3-9][0-9]{9}$', username):
            user = User.objects.filter(mobile=username).first()
        elif re.match('^.+@.+$', username):
            user = User.objects.filter(email=username).first()
        else:
            user = User.objects.filter(username=username).first()
        if user:
            res = user.check_password(password)
            if res:
                return user
            else:
                raise ValidationError('密码不正确！')
        else:
            raise ValidationError('用户不存在！')

    def _get_token(self, user):
        from rest_framework_jwt.serializers import jwt_encode_handler
        from laikeapi.utils.authenticate import jwt_payload_handler
        payload = jwt_payload_handler(user)  # 通过user对象获得payload
        token = jwt_encode_handler(payload)  # 通过payload获得token
        return token
