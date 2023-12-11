from rest_framework.generics import ListAPIView

from .models import CourseDirection, CourseCategory
from .serializers import CourseDirectionModelSerializer, CourseCategoryModelSerializer


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
