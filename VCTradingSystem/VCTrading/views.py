from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from .models import UserInfo, InvestmentHistory, TransferHistory
import uuid
from datetime import datetime
import logging
from decimal import Decimal

from .models import (
    UserInfo, 
    InvestmentHistory, 
    TransferHistory, 
    BankAccount, 
    VirtualAccount 
)

logger = logging.getLogger(__name__)


def signup_view(request):
    """회원가입 뷰"""
    if request.method == 'POST':
        try:
            # 계좌 ID와 가상계좌 ID 생성
            account_id = f'A{datetime.now().strftime("%Y%m%d%H%M%S")}'
            virtual_account_id = f'V{datetime.now().strftime("%Y%m%d%H%M%S")}'
            # 먼저 사용자 정보 생성
            user_data = {
                'user_id': request.POST.get('user_id'),
                'user_password': make_password(request.POST.get('password')),  # password를 user_password로 수정
                'user_name': request.POST.get('user_name'),
                'birth_date': datetime.strptime(request.POST.get('birth_date'), '%Y-%m-%d'),
                'phone_number': request.POST.get('phone_number'),
                'account_id': account_id,
                'virtual_account_id': virtual_account_id
            }

            user_info = UserInfo(**user_data)
            user_info.save()

            # UserInfo 생성 후 은행계좌와 가상계좌 생성
            bank_account = BankAccount(
                account_id=account_id,
                bank_name='DEFAULT_BANK',
                balance=0.00
            )
            bank_account.save()

            virtual_account = VirtualAccount(
                virtual_account_id=virtual_account_id,
                balance=0.00
            )
            virtual_account.save()

            return redirect('login')

        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            return render(request, 'auth/signup.html', {'error': f'회원가입 처리 중 오류가 발생했습니다: {str(e)}'})
    
    return render(request, 'auth/signup.html')

def login_view(request):
    """로그인 뷰"""  
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            password = request.POST.get('password')
            
            user = UserInfo.objects.filter(user_id=user_id).first()
            
            if user and check_password(password, user.user_password):  # user.password -> user.user_password로 수정
                request.session['user_id'] = user_id
                return redirect('dashboard')
            return render(request, 'auth/login.html', {'error': '잘못된 로그인 정보입니다.'})

        except Exception as e:  
            logger.error(f"Login error: {str(e)}")
            return render(request, 'auth/login.html', {'error': '로그인 처리 중 오류가 발생했습니다.'})
    return render(request, 'auth/login.html')

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
        
        # 가상계좌 정보 조회
        virtual_account = VirtualAccount.objects.get(virtual_account_id=user.virtual_account_id)
        
        # 실계좌 조회
        real_account = BankAccount.objects.get(account_id=user.account_id)
        
        # 입출금 내역 조회
        transfers = TransferHistory.objects.filter(
            user=user
        ).select_related('account', 'virtual_account').order_by('-transfer_time')

        for transfer in transfers:
            if transfer.transfer_type == 'DEPOSIT':
                transfer.from_account = transfer.account.account_id
                transfer.to_account = transfer.virtual_account.virtual_account_id
            else:
                transfer.from_account = transfer.virtual_account.virtual_account_id
                transfer.to_account = transfer.account.account_id

            if hasattr(transfer, 'crypto_transaction'):
                transfer.transaction_type = 'CRYPTO'
            else:
                transfer.transaction_type = 'VIRTUAL'
        
        context = {
            'user': user,
            'virtual_account': virtual_account,  # 가상계좌 정보 추가
            'real_account': real_account,  # 실계좌 정보 추가
            'transfers': transfers,
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
            # float 대신 Decimal 사용
            amount = Decimal(request.POST.get('amount', '0'))
            
            # 금액 유효성 검사
            if amount <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': '유효하지 않은 금액입니다.'
                })

            # 최대 거래 한도 체크 (예: 1천만원)
            if amount > Decimal('10000000'):
                return JsonResponse({
                    'success': False,
                    'message': '최대 거래 한도(1천만원)를 초과했습니다.'
                })
            
            if transfer_type == 'DEPOSIT':
                from_account = BankAccount.objects.get(
                    account_id=request.POST.get('from_account')
                )
                to_account = VirtualAccount.objects.get(
                    virtual_account_id=user.virtual_account_id
                )
                
                # 실계좌 잔액 체크
                if from_account.balance < amount:
                    return JsonResponse({
                        'success': False,
                        'message': f'실계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'
                    })
            else:
                from_account = VirtualAccount.objects.get(
                    virtual_account_id=user.virtual_account_id
                )
                to_account = BankAccount.objects.get(
                    account_id=request.POST.get('to_account')
                )
                
                # 가상계좌 잔액 체크
                if from_account.balance < amount:
                    return JsonResponse({
                        'success': False,
                        'message': f'가상계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'
                    })

            # 거래 처리
            with transaction.atomic():
                from_account.balance -= amount
                to_account.balance += amount

                from_account.save()
                to_account.save()

                transfer = TransferHistory(
                    transfer_id=f'TR{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    user=user,
                    transfer_type=transfer_type,
                    amount=amount,
                    balance=to_account.balance if transfer_type == 'DEPOSIT' else from_account.balance,
                    status='COMPLETED',
                    account=from_account if transfer_type == 'DEPOSIT' else to_account,
                    virtual_account=to_account if transfer_type == 'DEPOSIT' else from_account
                )
                transfer.save()

            return JsonResponse({
                'success': True,
                'message': '처리가 완료되었습니다.',
                'data': {
                    'balance': str(to_account.balance if transfer_type == 'DEPOSIT' else from_account.balance),
                    'transfer_id': transfer.transfer_id,
                    'transfer_time': transfer.transfer_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'from_account': from_account.account_id if transfer_type == 'DEPOSIT' else from_account.virtual_account_id,
                    'to_account': to_account.virtual_account_id if transfer_type == 'DEPOSIT' else to_account.account_id,
                }
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': '유효하지 않은 금액입니다.'
            })
            
        except Exception as e:
            logger.error(f"Transfer processing error details: {str(e)}")
            logger.error(f"Request POST data: {request.POST}")
            return JsonResponse({
                'success': False,
                'message': f'처리 중 오류가 발생했습니다: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': '잘못된 요청입니다.'
    })