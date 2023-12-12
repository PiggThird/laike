from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from .models import CourseDirection, CourseCategory, Course
from .search_indexes import CourseIndex


class CourseDirectionModelSerializer(serializers.ModelSerializer):
    """学习方向的序列化器"""

    class Meta:
        model = CourseDirection
        fields = ["id", "name"]


class CourseCategoryModelSerializer(serializers.ModelSerializer):
    """课程分类的序列化器"""

    class Meta:
        model = CourseCategory
        fields = ["id", "name"]


class CourseInfoModelSerializer(serializers.ModelSerializer):
    """课程信息的序列化器"""

    class Meta:
        model = Course
        fields = [
            "id", "name", "course_cover", "level", "get_level_display",
            "students", "status", "get_status_display",
            "lessons", "pub_lessons", "price", "discount"
        ]


class CourseIndexHaystackSerializer(HaystackSerializer):
    """课程搜索的序列化器"""

    class Meta:
        index_classes = [CourseIndex]
        fields = ["text", "id", "name", "course_cover", "get_level_display", "students", "get_status_display",
                  "pub_lessons", "price", "discount", "orders"]
