from django.urls import path, include
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers
from . import views


router = routers.SimpleRouter()
router.register('', views.LoginView, 'login')
urlpatterns = [
    # path('login', obtain_jwt_token, name='login'),
    path('', include(router.urls))
]
