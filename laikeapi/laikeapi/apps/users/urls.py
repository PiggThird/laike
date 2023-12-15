from django.urls import path, include, re_path
# from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers
from . import views


router = routers.SimpleRouter()
router.register('', views.LoginView, 'login')

urlpatterns = [
    # path('login', obtain_jwt_token, name='login'),
    path('', include(router.urls)),
    re_path(r'^mobile/(?P<mobile>1[3-9]\d{9})/$', views.MobileView.as_view()),
    path('register/', views.UserRegAPIView.as_view()),
    re_path(r"^sms/(?P<mobile>1[3-9]\d{9})/$", views.SendSmSView.as_view()),
    path("course/", views.CourseListAPIView.as_view()),
]
