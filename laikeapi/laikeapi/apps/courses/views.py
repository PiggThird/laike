import constants
from datetime import datetime, timedelta
from drf_haystack.filters import HaystackFilter
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django_redis import get_redis_connection

from .models import CourseDirection, CourseCategory, Course
from .paginations import CourseListPageNumberPagination
from .serializers import CourseDirectionModelSerializer, CourseCategoryModelSerializer, CourseInfoModelSerializer, \
    CourseIndexHaystackSerializer


class CourseDirectionListAPIView(ListAPIView):
    """学习方向"""
    queryset = CourseDirection.objects.filter(is_show=True, is_deleted=False).order_by("orders", "id")
    serializer_class = CourseDirectionModelSerializer
    pagination_class = None


class CourseCategoryListAPIView(ListAPIView):
    """学习分类"""
    # queryset = CourseCategory.objects.filter(is_show=True, is_deleted=False).order_by("orders", "-id")
    serializer_class = CourseCategoryModelSerializer
    pagination_class = None

    def get_queryset(self):
        # 类视图中，获取路由参数
        queryset = CourseCategory.objects.filter(is_show=True, is_deleted=False)
        # 如果direction为0，则表示查询所有的课程分类，如果大于0，则表示按学习方向来查找课程分类
        direction = int(self.kwargs.get("direction", 0))
        if direction > 0:
            queryset = queryset.filter(direction=direction)
        return queryset.order_by("orders", "id").all()


class CourseListAPIView(ListAPIView):
    """
    课程列表接口
    # url: /course/学习方向ID/课程分类
    # url: /course/P<direction>\d+)/(?P<category>\d+)$/
    # url: /course/0/0  # 展示所有的课程列表信息，不区分学习方向和课程分类
    # url: /course/1/0  # 展示前端开发学习方向的课程列表信息，不区分课程分类
    # url: /course/1/5  # 展示前端开发学习方向下javascript课程分类的课程列表信息
    """
    serializer_class = CourseInfoModelSerializer
    filter_backends = [OrderingFilter, ]
    ordering_fields = ['id', 'students', 'orders']
    pagination_class = CourseListPageNumberPagination

    def get_queryset(self):
        queryset = Course.objects.filter(is_deleted=False, is_show=True).order_by("-orders", "-id")
        direction = int(self.kwargs.get("direction", 0))
        category = int(self.kwargs.get("category", 0))
        # 只有在学习方向大于0的情况下才进行学习方向的过滤
        if direction > 0:
            queryset = queryset.filter(direction=direction)

        # 只有在课程分类大于0的情况下才进行课程分类的过滤
        if category > 0:
            queryset = queryset.filter(category=category)

        return queryset.all()


class CourseSearchViewSet(HaystackViewSet):
    """课程信息全文搜索视图类"""
    # 指定本次搜索的最终真实数据的保存模型
    index_models = [Course]
    serializer_class = CourseIndexHaystackSerializer
    filter_backends = [OrderingFilter, HaystackFilter]
    ordering_fields = ('id', 'students', 'orders')
    pagination_class = CourseListPageNumberPagination

    def list(self, request, *args, **kwargs):
        # 保存本次搜索的关键字
        redis = get_redis_connection("hot_word")
        text = request.query_params.get("text")
        if text:
            key = f"{constants.DEFAULT_HOT_WORD}:{datetime.now().strftime('%Y:%m:%d')}"
            is_exists = redis.exists(key)
            redis.zincrby(key, 1, text)  # 让有序集合中的text搜索关键字次数+1，如果该关键字第一次出现，则为1
            if not is_exists:
                redis.expire(key, constants.HOT_WORD_EXPIRE * 24 * 3600)

        return super().list(request, *args, **kwargs)


class HotWordAPIView(APIView):
    """搜索热词"""
    def get(self, request):
        redis = get_redis_connection("hot_word")
        # 获取最近指定天数的热词的key
        date_list = []
        for i in range(0, constants.HOT_WORD_EXPIRE):
            day = datetime.now() - timedelta(days=i)
            # 让小于10的天数跟月份前面补0 因为它默认是2023:5:6 变成 2023:05:06
            full_month = day.month if day.month >= 10 else f"0{day.month}"
            full_day = day.day if day.day >= 10 else f"0{day.day}"
            key = f"{constants.DEFAULT_HOT_WORD}:{day.year}:{full_month}:{full_day}"
            date_list.append(key)

        # 先删除原有的统计最近几天的热搜词的有序统计集合
        redis.delete(constants.DEFAULT_HOT_WORD)
        # 根据date_list找到最近指定天数的所有集合，并完成并集计算，产生新的有序统计集合constants.DEFAULT_HOT_WORD
        redis.zunionstore(constants.DEFAULT_HOT_WORD, date_list, aggregate="sum")
        # 按分数store进行倒序显示排名靠前的指定数量的热词
        word_list = redis.zrevrange(constants.DEFAULT_HOT_WORD, 0, constants.HOT_WORD_LENGTH - 1)
        return Response(word_list)
