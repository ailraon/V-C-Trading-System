from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import UserInfo, InvestmentHistory, TransferHistory
import uuid
from datetime import datetime
import logging

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
    # return render(request, 'dashboard/dashboard.html')

# @login_required
def dashboard_view(request):
    """대시보드 뷰"""
    try:
        user_id = request.session.get('user_id')
        user = UserInfo.objects.get(user_id=user_id)

        # 투자 내역 조회
        buy_transactions = InvestmentHistory.objects.filter(user=user, transaction_type='BUY')
        sell_transactions = InvestmentHistory.objects.filter(user=user, transaction_type='SELL')

        # 입출금 내역 조회  
        transfers = TransferHistory.objects.filter(user=user)

        context = {
            'user': user,
            'buy_transactions': buy_transactions, 
            'sell_transactions': sell_transactions,
            'transfers': transfers
        }
        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return redirect('login')

@login_required  
def process_transfer(request):
    """입출금 처리 뷰"""
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')  
            user = UserInfo.objects.get(user_id=user_id)

            amount = float(request.POST.get('amount'))
            transfer_type = request.POST.get('transfer_type') 
            is_deposit = transfer_type == 'DEPOSIT'

            # 가상계좌 잔액 업데이트
            if is_deposit:
                user.balance += amount
            else:
                if user.balance < amount:
                    return JsonResponse({'success': False, 'message': '잔액이 부족합니다.'})
                user.balance -= amount
            user.save()

            # 거래 내역 생성
            transfer_data = {  
                'transfer_id': f'TR{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'user': user,
                'account_id': user.account_id,
                'virtual_account_id': user.virtual_account_id,
                'transfer_type': transfer_type,
                'amount': amount,
                'balance': user.balance,
                'status': 'COMPLETED'
            }

            transfer = TransferHistory(**transfer_data)
            transfer.save()

            return JsonResponse({
                'success': True, 
                'message': '처리되었습니다.',
                'balance': user.balance
            })

        except Exception as e:
            logger.error(f"Transfer processing error: {str(e)}")  
            return JsonResponse({'success': False, 'message': '처리 중 오류가 발생했습니다.'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})