from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # 인증 관련 URL
    path('signup/', views.signup_view, name='signup'),  # 회원가입
    path('login/', views.login_view, name='login'),    # 로그인
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # 로그아웃
    
    # 대시보드 관련 URL
    path('', views.dashboard_view, name='dashboard'),  # 메인 대시보드
    
    # API 엔드포인트
    path('api/transfer/process/', views.process_transfer, name='process_transfer'),  # 입출금 처리
]