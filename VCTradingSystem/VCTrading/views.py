from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import UserInfo, InvestmentHistory, TransferHistory
import uuid
from datetime import datetime
import logging
from .utils import get_markets, get_current_price, get_krw_markets_with_prices_and_change  # 유틸리티 함수 가져오기

logger = logging.getLogger(__name__)

def signup_view(request):
    """회원가입 뷰"""
    if request.method == 'POST':
        try:
            user_data = {
                'user_id': request.POST.get('user_id'),
                'password': make_password(request.POST.get('password')),
                'user_name': request.POST.get('user_name'),
                'birth_date': datetime.strptime(request.POST.get('birth_date'), '%Y-%m-%d'),
                'phone_number': request.POST.get('phone_number'),
                'account_id': request.POST.get('account_id'), 
                'virtual_account_id': f'V{datetime.now().strftime("%Y%m%d%H%M%S")}'
            } 

            user_info = UserInfo(**user_data)
            user_info.save()
            return redirect('login')

        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            return render(request, 'auth/signup.html', {'error': '회원가입 처리 중 오류가 발생했습니다.'})
    
    return render(request, 'auth/signup.html')

def login_view(request):
    """로그인 뷰"""  
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            password = request.POST.get('password')
            
            user = UserInfo.objects.filter(user_id=user_id).first()
            
            if user and check_password(password, user.password):
                request.session['user_id'] = user_id
                return redirect('dashboard')
            return render(request, 'auth/login.html', {'error': '잘못된 로그인 정보입니다.'})

        except Exception as e:  
            logger.error(f"Login error: {str(e)}")
            return render(request, 'auth/login.html', {'error': '로그인 처리 중 오류가 발생했습니다.'})
    return render(request, 'auth/login.html')
    #return render(request, 'dashboard/dashboard.html')

def dashboard_view(request):
    """메인 대시보드 뷰"""
    try:
        user_id = request.session.get('user_id')
        user = UserInfo.objects.get(user_id=user_id)
        
        context = {
            'user': user,
        }
        return render(request, 'dashboard/dashboard.html', context)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return redirect('login')

def investment_management_view(request):
    """투자내역 관리 뷰"""
    try:
        user_id = request.session.get('user_id')
        user = UserInfo.objects.get(user_id=user_id)
        
        # 투자 내역 조회
        buy_transactions = InvestmentHistory.objects.filter(user=user, transaction_type='BUY')
        sell_transactions = InvestmentHistory.objects.filter(user=user, transaction_type='SELL')
        
        context = {
            'user': user,
            'buy_transactions': buy_transactions,
            'sell_transactions': sell_transactions
        }
        return render(request, 'management/investment.html', context)
    except Exception as e:
        logger.error(f"Investment management error: {str(e)}")
        return redirect('dashboard')

def transfer_management_view(request):
    """자산입출금 관리 뷰"""
    try:
        user_id = request.session.get('user_id')
        user = UserInfo.objects.get(user_id=user_id)
        
        # 입출금 내역 조회
        transfers = TransferHistory.objects.filter(user=user)
        
        context = {
            'user': user,
            'transfers': transfers
        }
        return render(request, 'management/transfer.html', context)
    except Exception as e:
        logger.error(f"Transfer management error: {str(e)}")
        return redirect('dashboard')
    
def process_transfer(request):
    """입출금 처리 뷰"""
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user = UserInfo.objects.get(user_id=user_id)

            transfer_type = request.POST.get('transfer_type')
            amount = float(request.POST.get('amount', 0))

            if amount <= 0:
                return JsonResponse({'success': False, 'message': '유효하지 않은 금액입니다.'})

            # 출금 시 잔액 검증
            if transfer_type == 'WITHDRAW':
                if not hasattr(user, 'balance') or user.balance < amount:
                    return JsonResponse({'success': False, 'message': '잔액이 부족합니다.'})

            # 입출금 처리
            if transfer_type == 'DEPOSIT':
                if not hasattr(user, 'balance'):
                    user.balance = 0
                user.balance = float(user.balance) + amount
            else:  # WITHDRAW
                user.balance = float(user.balance) - amount

            user.save()

            # 거래 내역 생성
            transfer = TransferHistory(
                transfer_id=f'TR{datetime.now().strftime("%Y%m%d%H%M%S")}',
                user=user,
                bank_id=request.POST.get('bank_id', 'DEFAULT_BANK'),  # 기본값 설정
                account_id=user.account_id,
                virtual_account_id=user.virtual_account_id,
                transfer_type=transfer_type,
                amount=amount,
                balance=user.balance,
                status='COMPLETED'
            )
            transfer.save()

            return JsonResponse({
                'success': True,
                'message': '처리가 완료되었습니다.',
                'data': {
                    'balance': user.balance,
                    'transfer_id': transfer.transfer_id,
                    'transfer_time': transfer.transfer_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            })

        except UserInfo.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
        except Exception as e:
            logger.error(f"Transfer processing error: {str(e)}")
            return JsonResponse({'success': False, 'message': '처리 중 오류가 발생했습니다.'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

def cryptolist_view(request):
    """
    가상화폐 목록 및 가격 조회
    """
    try:
        # 업비트 지원 마켓 목록 가져오기
        # markets = get_markets()

        # 예시: KRW-BTC, KRW-ETH의 현재 가격 가져오기
        # selected_markets = ["KRW-BTC", "KRW-ETH"]
        # prices = {market: get_current_price(market) for market in selected_markets}
        # prices = get_current_price(markets)

        # context = {
        #     "markets": markets,  # 상위 10개만 표시
        #     "prices": prices,         # 현재 가격 정보
        # }
        # return render(request, "cryptocurrency/cryptolist.html", context)
        market_data = get_krw_markets_with_prices_and_change()
        return render(request, "cryptocurrency/cryptolist.html", {"market_data": market_data})

    except Exception as e:
        return render(request, "cryptocurrency/cryptolist.html", {"error": str(e)})