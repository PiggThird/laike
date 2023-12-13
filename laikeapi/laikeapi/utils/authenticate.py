from rest_framework_jwt.utils import jwt_payload_handler as payload_handler
from django_redis import get_redis_connection


def jwt_payload_handler(user):
    """
    自定义载荷信息
    :params user  用户模型实例对象
    """
    # 先让jwt模块生成自己的载荷信息
    payload = payload_handler(user)
    # 追加自己要返回的内容
    if hasattr(user, 'avatar'):
        payload['avatar'] = user.avatar.url if user.avatar else ""
    if hasattr(user, 'nickname'):
        payload['nickname'] = user.nickname
    if hasattr(user, 'money'):
        payload['money'] = float(user.money)
    if hasattr(user, 'credit'):
        payload['credit'] = user.credit

    return payload


def jwt_response_payload_handler(token, user, request):
    """
    增加返回购物车的商品数量
    token: jwt token
    user: 用户模型对象
    request: 客户端的请求对象
    """
    redis = get_redis_connection("cart")
    cart_total = redis.hlen(f"cart_{user.id}")

    return {
        "cart_total": cart_total,
        "token": token
    }