import logging
from datetime import datetime
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.http.response import HttpResponse

from orders.models import Order
from alipaysdk import AliPaySDK
from users.models import Credit, UserCourse
from courses.serializers import CourseInfoModelSerializer
from coupon.models import CouponLog

logger = logging.getLogger("django")


# Create your views here.
class AlipayAPIViewSet(ViewSet):
    """支付宝接口"""

    def link(self, request, order_number):
        """生成支付宝支付链接信息"""
        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 0:
                return Response({"message": "对不起，当前订单不能重复支付或订单已超时！"})
        except Order.DoesNotExist:
            return Response({"message": "对不起，当前订单不存在！"})

        # # 读取支付宝公钥与商户私钥
        # app_private_key_string = open(settings.ALIPAY["app_private_key_path"]).read()
        # alipay_public_key_string = open(settings.ALIPAY["alipay_public_key_path"]).read()
        #
        # # 创建alipay SDK操作对象
        # alipay = AliPay(
        #     appid=settings.ALIPAY["appid"],
        #     app_notify_url=settings.ALIPAY["notify_url"],       # 默认全局回调 url
        #     app_private_key_string=app_private_key_string,
        #     # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        #     alipay_public_key_string=alipay_public_key_string,
        #     sign_type=settings.ALIPAY["sign_type"],             # RSA2
        #     debug=settings.ALIPAY["debug"],                     # 默认 False，沙箱模式下必须设置为True
        #     verbose=settings.ALIPAY["verbose"],                 # 输出调试数据
        #     config=AliPayConfig(timeout=settings.ALIPAY["timeout"])  # 可选，请求超时时间，单位：秒
        # )
        #
        # # 生成支付信息
        # order_string = alipay.client_api(
        #     "alipay.trade.page.pay",                        # 接口名称
        #     biz_content={
        #         "out_trade_no": order_number,               # 订单号
        #         "total_amount": float(order.real_price),    # 订单金额 单位：元
        #         "subject": order.name,                      # 订单标题
        #         "product_code": "FAST_INSTANT_TRADE_PAY",   # 产品码，目前只能支持 FAST_INSTANT_TRADE_PAY
        #     },
        #     return_url=settings.ALIPAY["return_url"],       # 可选，同步回调地址，必须填写客户端的路径
        #     notify_url=settings.ALIPAY["notify_url"]        # 可选，不填则使用采用全局默认notify_url，必须填写服务端的路径
        # )
        #
        # # 拼接完整的支付链接
        # link = f"{settings.ALIPAY['gateway']}?{order_string}"
        # print(link)
        alipay = AliPaySDK()
        link = alipay.page_pay(order_number, order.real_price, order.name)
        print(link)

        return Response({
            "pay_type": 0,                                  # 支付类型
            "get_pay_type_display": "支付宝",                # 支付类型的提示
            "link": link                                    # 支付连接地址
        })

    def return_result(self, request):
        """支付宝支付结果的同步通知处理"""
        data = request.query_params.dict()  # QueryDict
        alipay = AliPaySDK()
        success = alipay.check_sign(data)
        if not success:
            return Response({"errmsg": "通知通知结果不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        order_number = data.get("out_trade_no")
        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return Response({"errmsg": "订单超时或已取消！"}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"errmsg": "订单不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前订单相关的课程信息，用于返回给客户端
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]

        if order.order_status == 0:
            # 请求支付宝，查询订单的支付结果
            result = alipay.query(order_number)
            print(f"result-{result}")
            if result.get("trade_status", None) in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
                """支付成功"""
                with transaction.atomic():
                    save_id = transaction.savepoint()
                    try:
                        now_time = datetime.now()
                        # 1. 修改订单状态
                        order.pay_time = now_time
                        order.order_status = 1
                        order.save()
                        # 2.1 记录扣除个人积分的流水信息
                        if order.credit > 0:
                            Credit.objects.create(operation=1, number=order.credit, user=order.user)

                        # 2.2 补充个人的优惠券使用记录
                        coupon_log = CouponLog.objects.filter(order=order).first()
                        if coupon_log:
                            coupon_log.use_time = now_time
                            coupon_log.use_status = 1  # 1 表示已使用
                            coupon_log.save()

                        # 3. 用户和课程的关系绑定
                        user_course_list = []
                        for course in course_list:
                            user_course_list.append(UserCourse(course=course, user=order.user))
                        UserCourse.objects.bulk_create(user_course_list)

                        # 4. 取消订单超时

                    except Exception as e:
                        logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                        transaction.savepoint_rollback(save_id)
                        return Response({"errmsg": "当前订单支付未完成！请联系客服工作人员！"},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 返回客户端结果
        serializer = CourseInfoModelSerializer(course_list, many=True)
        return Response({
            "pay_time": order.pay_time.strftime("%Y-%m-%d %H:%M:%S"),
            "real_price": float(order.real_price),
            "course_list": serializer.data
        })

    def notify_result(self, request):
        """支付宝支付结果的异步通知处理"""
        # drf中接收POST参数需要使用request.data
        data = request.data
        alipay = AliPaySDK()
        success = alipay.check_sign(data)
        if not success:
            # 因为是属于异步处理，这个过程无法通过终端调试，因此，需要把支付发送过来的结果，记录到日志中。
            logger.error(f"[支付宝]>> 异步通知结果验证失败：{data}")
            return HttpResponse("fail")

        if data.get("trade_status") not in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
            return HttpResponse("fail")

        # 基于支付包异步请求的支付结果中提取订单号
        order_number = data.get("out_trade_no")

        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return HttpResponse("fail")
        except Order.DoesNotExist:
            return HttpResponse("fail")

        # 如果已经支付完成，则不需要继续往下处理
        if order.order_status == 1:
            return HttpResponse("success")

        # 获取本次下单的商品课程列表
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]
        courses_list = []

        for course in course_list:
            courses_list.append(UserCourse(course=course, user=order.user))

        """支付成功"""
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                now_time = datetime.now()
                # 1. 修改订单状态
                order.pay_time = now_time
                order.order_status = 1
                order.save()
                # 2.1 记录扣除个人积分的流水信息
                if order.credit > 0:
                    Credit.objects.create(operation=1, number=order.credit, user=order.user)

                # 2.2 补充个人的优惠券使用记录
                coupon_log = CouponLog.objects.filter(order=order).first()
                if coupon_log:
                    coupon_log.use_time = now_time
                    coupon_log.use_status = 1  # 1 表示已使用
                    coupon_log.save()

                # 3. 用户和课程的关系绑定
                user_course_list = []
                for course in course_list:
                    user_course_list.append(UserCourse(course=course, user=order.user))
                UserCourse.objects.bulk_create(user_course_list)

                # 4. 取消订单超时

            except Exception as e:
                logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                transaction.savepoint_rollback(save_id)
                return HttpResponse("fail")

        return HttpResponse("success")

    def query(self, request, order_number):
        """主动查询订单支付的支付结果"""
        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return Response({"errmsg": "订单超时或已取消！"}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"errmsg": "订单不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前订单相关的课程信息，用于返回给客户端
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]
        courses_list = []
        for course in course_list:
            courses_list.append(UserCourse(course=course, user=order.user))

        if order.order_status == 0:
            # 请求支付宝，查询订单的支付结果
            alipay = AliPaySDK()
            result = alipay.query(order_number)
            print(f"result-{result}")
            if result.get("trade_status", None) in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
                """支付成功"""
                with transaction.atomic():
                    save_id = transaction.savepoint()
                    try:
                        now_time = datetime.now()
                        # 1. 修改订单状态
                        order.pay_time = now_time
                        order.order_status = 1
                        order.save()
                        # 2.1 记录扣除个人积分的流水信息
                        if order.credit > 0:
                            Credit.objects.create(operation=1, number=order.credit, user=order.user)

                        # 2.2 补充个人的优惠券使用记录
                        coupon_log = CouponLog.objects.filter(order=order).first()
                        if coupon_log:
                            coupon_log.use_time = now_time
                            coupon_log.use_status = 1  # 1 表示已使用
                            coupon_log.save()

                        # 3. 用户和课程的关系绑定
                        user_course_list = []
                        for course in course_list:
                            user_course_list.append(UserCourse(course=course, user=order.user))
                        UserCourse.objects.bulk_create(user_course_list)

                        # 4. 取消订单超时

                    except Exception as e:
                        logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                        transaction.savepoint_rollback(save_id)
                        return Response({"errmsg": "当前订单支付未完成！请联系客服工作人员！"},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                """当前订单未支付"""
                return Response({"errmsg": "当前订单未支付！"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errmsg": "当前订单已支付！"})

