from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError
from laikeapi.utils import constants


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


class UserRegisterModelSerializer(serializers.ModelSerializer):
    """
    用户注册的序列化器
    """
    re_password = serializers.CharField(required=True, write_only=True)
    sms_code = serializers.CharField(min_length=4, max_length=6, required=True, write_only=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["mobile", "password", "re_password", "sms_code", "token"]
        extra_kwargs = {
            "mobile": {"required": True, "write_only": True},
            "password": {"required": True, "write_only": True, "min_length": 6, "max_length": 16},
        }

    def validate(self, data):
        """验证客户端数据"""
        # 手机号格式验证
        import re
        mobile = data.get("mobile", None)
        if not re.match("^1[3-9]\d{9}$", mobile):
            raise serializers.ValidationError(detail="手机号格式不正确！", code="mobile")

        # 密码和确认密码
        password = data.get("password")
        re_password = data.get("re_password")
        if password != re_password:
            raise serializers.ValidationError(detail="密码和确认密码不一致！", code="password")

        # 手机号是否已注册
        try:
            User.objects.get(mobile=mobile)
            raise serializers.ValidationError(detail="手机号已注册！")
        except User.DoesNotExist:
            pass

        # todo 验证短信验证码

        return data

    def create(self, validated_data):
        """保存用户信息，完成注册"""
        mobile = validated_data.get('mobile')
        password = validated_data.get('password')

        user = User.objects.create_user(username=mobile,
                                        mobile=mobile,
                                        avatar=constants.DEFAULT_USER_AVATAR,
                                        password=password
                                        )

        # 注册成功以后，免登陆
        from rest_framework_jwt.serializers import jwt_encode_handler
        from laikeapi.utils.authenticate import jwt_payload_handler
        payload = jwt_payload_handler(user)
        user.token = jwt_encode_handler(payload)

        return user

