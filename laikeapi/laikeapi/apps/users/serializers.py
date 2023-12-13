import constants
from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError
from django_redis import get_redis_connection


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
        cart_total = self._get_cart_total(user)
        self.context['user'] = user
        self.context['token'] = token
        self.context['cart_total'] = cart_total
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

    def _get_cart_total(self, user):
        redis = get_redis_connection("cart")
        cart_total = redis.hlen(f"cart_{user.id}")
        return cart_total



class CodeUserSerializer(serializers.ModelSerializer):
    code = serializers.CharField()
    mobile = serializers.CharField(max_length=11, min_length=11)

    class Meta:
        model = User
        fields = ['mobile', 'code']

    def validate(self, attrs):
        user = self._get_user(attrs)
        token = self._get_token(user)
        self.context['token'] = token
        self.context['user'] = user
        return attrs

    def _get_user(self, attrs):
        mobile = attrs.get('mobile')
        code = attrs.get('code')

        # 取出原来的code
        redis = get_redis_connection('sms_code')
        cache_code = redis.get(f'sms_{mobile}').decode()

        if code == cache_code:
            # 验证码通过
            user = User.objects.filter(mobile=mobile).first()
            # 把使用过的验证码清空
            redis.delete(f"sms_{mobile}")
            return user
        else:
            raise serializers.ValidationError('验证码错误')

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

        # 验证短信验证码
        redis = get_redis_connection('sms_code')
        code = redis.get(f'sms_{mobile}')
        if code is None:
            """获取不到验证码，则表示验证码已经过期了"""
            raise serializers.ValidationError(detail="验证码失效或已过期!", code="sms_code")

        # 从redis提取的数据，字符串都是bytes类型，所以decode
        if code.decode() != data.get("sms_code"):
            raise serializers.ValidationError(detail="短信验证码错误！", code="sms_code")
        # 删除掉redis中的短信，后续不管用户是否注册成功，至少当前这条短信验证码已经没有用处了
        redis.delete(f"sms_{mobile}")

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

