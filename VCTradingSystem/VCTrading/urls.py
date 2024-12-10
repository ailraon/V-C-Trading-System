from django.urls import path
from . import views

urlpatterns = [
    # 루트 및 메인 페이지
    path('', views.cryptolist_view, name='crypto_list'),  # 루트 URL
    path('crypto/', views.cryptolist_view, name='crypto_list'),  # 기존 crypto URL도 유지
    
    # 인증 관련 URL
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 관리 관련 URL
    path('investment/', views.investment_management_view, name='investment_management'),
    path('transfer/', views.transfer_management_view, name='transfer_management'),
    path('user/info/', views.user_info_management_view, name='user_info_management'),
    
    # API 엔드포인트
    path('api/transfer/process/', views.process_transfer, name='process_transfer'),
    path('crypto/buy/', views.buy_crypto, name='crypto_buy'),
    path('crypto/sell/', views.sell_crypto, name='crypto_sell'),
    
    # 테스트용 실계좌 입금 처리 URL
    path('api/test/deposit/', views.deposit_to_real_account, name='test_deposit'),

    # 가상화폐 예측
    path('prediction/', views.prediction_view, name='prediction'),
    path('api/predict/<str:coin_id>/', views.get_prediction_data, name='get_prediction'),
]