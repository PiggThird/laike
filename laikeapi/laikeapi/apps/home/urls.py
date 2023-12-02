from django.urls import path
from . import views

urlpatterns = [
    path("regi", views.HomeAPIView.as_view()),
    path("login", views.login),
]
