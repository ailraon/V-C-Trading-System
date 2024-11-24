from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 기본 페이지
]