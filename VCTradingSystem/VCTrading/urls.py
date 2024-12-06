from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # 인증 관련 URL
    path('signup/', views.signup_view, name='signup'),  # 회원가입
    path('login/', views.login_view, name='login'),    # 로그인
    path('logout/', views.logout_view, name='logout'),
    
    path('', views.dashboard_view, name='dashboard'),  # 대시보드
    
    # 관리 관련 URL
    path('investment/', views.investment_management_view, name='investment_management'),
    path('transfer/', views.transfer_management_view, name='transfer_management'),
    path('user/info/', views.user_info_management_view, name='user_info_management'),
    
    # API 엔드포인트
    path('api/transfer/process/', views.process_transfer, name='process_transfer'),  # 입출금 처리

    path('crypto/', views.cryptolist_view, name='crypto_list'),
    path('crypto/buy/', views.buy_crypto, name='crypto_buy'),
    path('crypto/sell/', views.sell_crypto, name='crypto_sell'),
    
    # 테스트용 실계좌 입금 처리 URL
    path('api/test/deposit/', views.deposit_to_real_account, name='test_deposit'),

    # 가상화폐 예측
    path('cryptocurrency/prediction/', views.prediction_view, name='prediction'),
    path('api/predict/<str:coin_id>/', views.get_prediction_data, name='get_prediction'),
]