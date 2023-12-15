import constants
import logging

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from django_redis import get_redis_connection
from django.db import transaction
from courses.paginations import CourseListPageNumberPagination

from .serializers import UserSerializer, UserRegisterModelSerializer, CodeUserSerializer, UserCourseModelSerializer
from .models import User, UserCourse, StudyProgress
from courses.models import Course, CourseLesson
from .task import send_sms

logger = logging.getLogger("django")


# Create your views here.
class LoginView(ViewSet):
    @action(methods=['POST'], detail=False)
    def login(self, request, *args, **kwargs):
        ser = UserSerializer(data=request.data)
        if ser.is_valid():
            token = ser.context.get('token')
            username = ser.context.get('user').username
            cart_total = ser.context.get('cart_total')
            return Response({'code': 0, 'username': username, 'token': token, "cart_total": cart_total})
        else:
            return Response({'code': 1, 'msg': ser.errors})

    @action(methods=['POST'], detail=False)
    def code_login(self, request, *args, **kwargs):
        ser = CodeUserSerializer(data=request.data)
        if ser.is_valid():
            token = ser.context['token']
            username = ser.context['user'].username
            return Response({"token": token, "username": username})
        else:
            return Response({"code": 0, "msg": ser.errors})


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


class UserRegAPIView(CreateAPIView):
    """用户注册接口"""
    queryset = User.objects.all()
    serializer_class = UserRegisterModelSerializer


class SendSmSView(APIView):
    # throttle_classes = [throttles.SMSThrottle]

    def get(self, request, mobile):
        """
        发送短信验证码接口
        :return:
        """
        from laikeapi.libs.tx_sms import get_code
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
        # send_message(mobile, code)
        send_sms.delay(mobile, code)

        # 记录code到redis中，并以time作为有效期
        # 使用redis提供的管道对象pipeline来优化redis的写入操作[添加/修改/删除]
        pipe = redis.pipeline()
        pipe.multi()  # 开启事务
        pipe.setex(f"sms_{mobile}", 180, code)
        pipe.setex(f"interval_{mobile}", 60, "_")
        pipe.execute()  # 提交事务，同时把暂存在pipeline的数据一次性提交给redis

        return Response({"errmsg": "OK"}, status=status.HTTP_200_OK)


class CourseListAPIView(ListAPIView):
    """当前用户的课程列表信息"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserCourseModelSerializer
    pagination_class = CourseListPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        query = UserCourse.objects.filter(user=user)
        course_type = int(self.request.query_params.get("type", -1))
        course_type_list = [item[0] for item in Course.COURSE_TYPE]
        if course_type in course_type_list:
            query = query.filter(course__course_type=course_type)
        return query.order_by("-id").all()


class UserCourseAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserCourseModelSerializer

    def get(self, request, course_id):
        """获取用户在当前课程的学习进度"""
        user = request.user
        user_course = UserCourse.objects.filter(user=user, course=course_id).first()
        if not user_course:
            return Response({"error": "当前课程您尚未购买！"}, status=status.HTTP_400_BAD_REQUEST)

        chapter_id = user_course.chapter_id
        print(f"chapter_id={chapter_id}")

        if chapter_id:
            """曾经学习过本课程"""
            lesson = user_course.lesson
        else:
            """从未学习当前课程"""
            # 获取当前课程第1个章节
            chapter = user_course.course.chapter_list.order_by("orders").first()
            if not chapter:
                return Response({"error": "当前课程没有任何章节！"}, status=status.HTTP_400_BAD_REQUEST)
            # 获取当前章节第1个课时
            lesson = chapter.lesson_list.order_by("orders").first()
            if not lesson:
                return Response({"error": "当前课程章节没有任何课时！"}, status=status.HTTP_400_BAD_REQUEST)
            # 保存本次学习起始进度
            user_course.chapter = chapter
            user_course.lesson = lesson
            user_course.save()

        serializer = self.get_serializer(user_course)
        data = serializer.data
        # 获取当前课时的课时类型和课时链接
        data["lesson_type"] = lesson.lesson_type
        data["lesson_link"] = lesson.lesson_link

        return Response(data)


class StudyLessonAPIView(APIView):
    """用户在当前课时的学习时间进度"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lesson_id = int(request.query_params.get("lesson"))
        user = request.user

        # 查找课时
        lesson = CourseLesson.objects.get(pk=lesson_id)

        progress = StudyProgress.objects.filter(user=user, lesson=lesson).first()

        # 如果查询没有进度，则默认进度为0
        if progress is None:
            progress = StudyProgress.objects.create(
                user=request.user,
                lesson=lesson,
                study_time=0
            )

        return Response(progress.study_time)


class StudyProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """添加课时学习进度"""
        try:
            # 1. 接收客户端提交的视频进度和课时ID
            study_time = int(request.data.get("time"))
            lesson_id = int(request.data.get("lesson"))
            user = request.user

            # 判断当前课时是否免费或者当前课时所属的课程是否被用户购买了

            # 判断本次更新学习时间是否超出阈值，当超过阈值，则表示用户已经违规快进了。
            if study_time > constants.MAV_SEEK_TIME:
                raise Exception

            # 查找课时
            lesson = CourseLesson.objects.get(pk=lesson_id)

        except:
            return Response({"error": "无效的参数或当前课程信息不存在！"})

        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                # 2. 记录课时学习进度
                progress = StudyProgress.objects.filter(user=user, lesson=lesson).first()

                if progress is None:
                    """新增一条用户与课时的学习记录"""
                    progress = StudyProgress(
                        user=user,
                        lesson=lesson,
                        study_time=study_time
                    )
                else:
                    """直接更新现有的学习时间"""
                    progress.study_time = int(progress.study_time) + int(study_time)

                progress.save()

                # 3. 记录课程学习的总进度
                user_course = UserCourse.objects.get(user=user, course=lesson.course)
                user_course.study_time = int(user_course.study_time) + int(study_time)

                # 用户如果往后观看章节，则记录下
                if lesson.chapter.orders > user_course.chapter.orders:
                    user_course.chapter = lesson.chapter

                # 用户如果往后观看课时，则记录下
                if lesson.orders > user_course.lesson.orders:
                    user_course.lesson = lesson

                user_course.save()

                return Response({"message": "课时学习进度更新完成！"})

            except Exception as e:
                print(f"error={e}")
                logger.error(f"更新课时进度失败！:{e}")
                transaction.savepoint_rollback(save_id)
                return Response({"error": "当前课时学习进度丢失！"})