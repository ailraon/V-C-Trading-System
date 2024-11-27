from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.http import JsonResponse  # JsonResponse 추가
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime
import logging
import re  # re 모듈 추가
from decimal import Decimal
from .models import UserInfo, InvestmentHistory, TransferHistory, BankAccount, VirtualAccount, CryptoInfo, OrderInfo
logger = logging.getLogger(__name__)

'''
서버 실행문
python manage.py runserver
'''

class InfoValidator:
    """정보 검증 클래스"""
    def __init__(self):
        """검증기 초기화"""
        pass

    def validate_sign_up_info(self, user_data):
        """회원가입 정보 검증"""
        try:
            # 필수 필드 검증
            required_fields = ['user_id', 'user_password', 'user_name', 'birth_date', 'phone_number', 'account_id']
            for field in required_fields:
                if not user_data.get(field):
                    return False, f"{field} 필드는 필수입니다."

            # 아이디 중복 검사
            if UserInfo.objects.filter(user_id=user_data['user_id']).exists():
                return False, "이미 사용중인 아이디입니다."

            # 비밀번호 유효성 검사
            if len(user_data['user_password']) < 8:
                return False, "비밀번호는 8자 이상이어야 합니다."

            # 전화번호 중복/형식 검사
            phone_pattern = re.compile(r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$')
            if not phone_pattern.match(user_data['phone_number']):
                return False, "올바른 전화번호 형식이 아닙니다."
            if UserInfo.objects.filter(phone_number=user_data['phone_number']).exists():
                return False, "이미 등록된 전화번호입니다."

            # 계좌번호 중복 검사
            if UserInfo.objects.filter(account_id=user_data['account_id']).exists():
                return False, "이미 등록된 계좌번호입니다."

            return True, "유효한 회원가입 정보입니다."
        except Exception as e:
            return False, f"검증 중 오류가 발생했습니다: {str(e)}"

    def validate_login_info(self, user_id, password):
        """로그인 정보 검증"""
        try:
            user = UserInfo.objects.filter(user_id=user_id).first()
            if not user:
                return False, "존재하지 않는 아이디입니다."
            
            if not check_password(password, user.user_password):
                return False, "비밀번호가 일치하지 않습니다."

            return True, "유효한 로그인 정보입니다."
        except Exception as e:
            return False, f"검증 중 오류가 발생했습니다: {str(e)}"

    def validate_admin_info(self, admin_id, admin_password):
        """관리자 정보 검증"""
        # 관리자 검증 로직 구현
        pass

class User:
    """사용자 클래스"""
    def __init__(self):
        self.info_validator = InfoValidator()

    def sign_up_request(self, request):
        """회원가입 요청"""
        try:
            user_data = {
                'user_id': request.POST.get('user_id'),
                'user_password': request.POST.get('password'),
                'user_name': request.POST.get('user_name'),
                'birth_date': request.POST.get('birth_date'),
                'phone_number': request.POST.get('phone_number'),
                'account_id': request.POST.get('account_id')
            }
            
            is_valid, message = self.info_validator.validate_sign_up_info(user_data)
            if not is_valid:
                return False, message

            return True, user_data
        except Exception as e:
            logger.error(f"Sign up request error: {str(e)}")
            return False, str(e)

    def login_request(self, request):
        """로그인 요청"""
        try:
            user_id = request.POST.get('user_id')
            password = request.POST.get('password')
            
            is_valid, message = self.info_validator.validate_login_info(user_id, password)
            if not is_valid:
                return False, message

            return True, user_id
        except Exception as e:
            logger.error(f"Login request error: {str(e)}")
            return False, str(e)

class InvestmentManager:
    """투자내역 관리 클래스"""
    def __init__(self):
        pass

    def check_buy_transactions(self, user):
        """매수 거래내역 확인"""
        try:
            return InvestmentHistory.objects.filter(user=user, transaction_type='BUY')
        except Exception as e:
            logger.error(f"Buy transactions check error: {str(e)}")
            return None

    def check_sell_transactions(self, user):
        """매도 거래내역 확인"""
        try:
            return InvestmentHistory.objects.filter(user=user, transaction_type='SELL')
        except Exception as e:
            logger.error(f"Sell transactions check error: {str(e)}")
            return None

class AssetTransferManager:
    """자산입출금 관리 클래스"""
    def __init__(self):
        pass

    def get_transfer_history(self, user):
        """입출금 내역 조회"""
        try:
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

            return transfers
        except Exception as e:
            logger.error(f"Transfer history error: {str(e)}")
            return None

    def process_deposit(self, user, from_account_id, amount):
        """입금 처리"""
        try:
            from_account = BankAccount.objects.get(account_id=from_account_id)
            to_account = VirtualAccount.objects.get(virtual_account_id=user.virtual_account_id)

            if from_account.balance < amount:
                return False, f'실계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'

            return self._process_transfer(user, from_account, to_account, amount, 'DEPOSIT')
        except Exception as e:
            logger.error(f"Deposit processing error: {str(e)}")
            return False, str(e)

    def process_withdrawal(self, user, to_account_id, amount):
        """출금 처리"""
        try:
            from_account = VirtualAccount.objects.get(virtual_account_id=user.virtual_account_id)
            to_account = BankAccount.objects.get(account_id=to_account_id)

            if from_account.balance < amount:
                return False, f'가상계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'

            return self._process_transfer(user, from_account, to_account, amount, 'WITHDRAWAL')
        except Exception as e:
            logger.error(f"Withdrawal processing error: {str(e)}")
            return False, str(e)

    def _process_transfer(self, user, from_account, to_account, amount, transfer_type):
        """입출금 공통 처리"""
        try:
            with transaction.atomic():
                from_account.balance -= amount
                to_account.balance += amount

                from_account.save()
                to_account.save()

                transfer = TransferHistory(
                    transfer_id=f'TR{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    user=user,
                    bank_name=from_account.bank_name if transfer_type == 'DEPOSIT' else to_account.bank_name,
                    transfer_type=transfer_type,
                    amount=amount,
                    balance=to_account.balance if transfer_type == 'DEPOSIT' else from_account.balance,
                    status='COMPLETED',
                    account=from_account if transfer_type == 'DEPOSIT' else to_account,
                    virtual_account=to_account if transfer_type == 'DEPOSIT' else from_account
                )
                transfer.save()

                return True, {
                    'balance': str(to_account.balance if transfer_type == 'DEPOSIT' else from_account.balance),
                    'transfer_id': transfer.transfer_id,
                    'transfer_time': transfer.transfer_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'bank_name': transfer.bank_name,
                    'from_account': from_account.account_id if hasattr(from_account, 'account_id') 
                                  else from_account.virtual_account_id,
                    'to_account': to_account.virtual_account_id if hasattr(to_account, 'virtual_account_id') 
                                else to_account.account_id,
                }
        except Exception as e:
            logger.error(f"Transfer processing error: {str(e)}")
            return False, str(e)

class VCTradingSystem:
    """가상화폐 트레이딩 시스템 클래스"""
    def __init__(self):
        self.info_validator = InfoValidator()
        self.investment_manager = InvestmentManager()
        self.asset_transfer_manager = AssetTransferManager()
        
    def process_sign_up(self, user_data):
        """회원가입 처리"""
        try:
            virtual_account_id = f'V{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
            with transaction.atomic():
                # 먼저 은행 계좌 생성
                bank_account = BankAccount.objects.create(
                    account_id=user_data['account_id'],
                    bank_name='DEFAULT_BANK',
                    balance=0.00
                )

                # 가상 계좌 생성
                virtual_account = VirtualAccount.objects.create(
                    virtual_account_id=virtual_account_id,
                    balance=0.00
                )

                # UserInfo 생성 - 외래키 관계 사용
                user_info = UserInfo.objects.create(
                    user_id=user_data['user_id'],
                    user_password=make_password(user_data['user_password']),
                    user_name=user_data['user_name'],
                    birth_date=datetime.strptime(user_data['birth_date'], '%Y-%m-%d'),
                    phone_number=user_data['phone_number'],
                    account=bank_account,  # 외래키 관계로 수정
                    virtual_account=virtual_account  # 외래키 관계로 수정
                )

                return True, "회원가입이 완료되었습니다."

        except Exception as e:
            logger.error(f"Sign up processing error: {str(e)}")
            return False, f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"

    def get_user_info(self, user_id):
        """사용자 정보 조회 - related fields 포함"""
        try:
            return UserInfo.objects.select_related('account', 'virtual_account').get(user_id=user_id)
        except UserInfo.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"User info error: {str(e)}")
            return None

    def process_login(self, user_id):
        """로그인 처리"""
        try:
            return True, user_id
        except Exception as e:
            logger.error(f"Login processing error: {str(e)}")
            return False, str(e)

    def process_logout(self, request):
        """로그아웃 처리"""
        try:
            request.session.flush()
            return True, "로그아웃되었습니다."
        except Exception as e:
            logger.error(f"Logout processing error: {str(e)}")
            return False, str(e)

    def get_user_info(self, user_id):
        """사용자 정보 조회"""
        try:
            return UserInfo.objects.get(user_id=user_id)
        except UserInfo.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"User info error: {str(e)}")
            return None
        
    def get_virtual_account(self, virtual_account_id):
        """가상계좌 정보 조회"""
        try:
            return VirtualAccount.objects.get(virtual_account_id=virtual_account_id)
        except VirtualAccount.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Virtual account info error: {str(e)}")
            return None

    def get_bank_account(self, account_id):
        """은행계좌 정보 조회"""
        try:
            return BankAccount.objects.get(account_id=account_id)
        except BankAccount.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Bank account info error: {str(e)}")
            return None

def signup_view(request):
    """회원가입 뷰"""
    context = {}
    if request.method == 'POST':
        user = User()
        trading_system = VCTradingSystem()
        
        # POST 데이터를 context에 저장
        context.update({
            'user_id': request.POST.get('user_id', ''),
            'user_name': request.POST.get('user_name', ''),
            'birth_date': request.POST.get('birth_date', ''),
            'phone_number': request.POST.get('phone_number', ''),
            'account_id': request.POST.get('account_id', '')
        })
        
        success, result = user.sign_up_request(request)
        if not success:
            context['error'] = result
            # 에러가 발생한 필드를 찾아서 포커싱
            error_field = result.split()[0].lower()
            if error_field in ['이미', '올바른', '존재하지']:  # 에러 메시지 첫 단어로 필드 식별
                if '아이디' in result:
                    error_field = 'user_id'
                elif '비밀번호' in result:
                    error_field = 'password'
                elif '전화번호' in result:
                    error_field = 'phone_number'
                elif '계좌번호' in result:
                    error_field = 'account_id'
            context['error_field'] = error_field
            return render(request, 'auth/signup.html', context)
        
        success, message = trading_system.process_sign_up(result)
        if not success:
            context['error'] = message
            return render(request, 'auth/signup.html', context)
            
        # 회원가입 성공 메시지 추가
        messages.success(request, '회원가입이 성공적으로 완료되었습니다. 로그인해주세요.')
        return redirect('login')
    
    return render(request, 'auth/signup.html')

def login_view(request):
    """로그인 뷰"""
    context = {}
    if request.method == 'POST':
        user = User()
        trading_system = VCTradingSystem()
        
        success, result = user.login_request(request)
        if not success:
            context.update({
                'error': result,
                'user_id': request.POST.get('user_id', ''),
                'error_field': 'password' if '비밀번호' in result else 'user_id'
            })
            return render(request, 'auth/login.html', context)
        
        success, user_id = trading_system.process_login(result)
        if success:
            request.session['user_id'] = user_id
            return redirect('dashboard')
        
        context.update({
            'error': user_id,
            'user_id': request.POST.get('user_id', '')
        })
        return render(request, 'auth/login.html', context)
    
    return render(request, 'auth/login.html')

def dashboard_view(request):
    """메인 대시보드 뷰"""
    trading_system = VCTradingSystem()
    
    try:
        user_id = request.session.get('user_id')
        user = trading_system.get_user_info(user_id)
        if not user:
            return redirect('login')
        
        return render(request, 'dashboard/dashboard.html', {'user': user})
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return redirect('login')

def investment_management_view(request):
    """투자내역 관리 뷰"""
    trading_system = VCTradingSystem()
    
    try:
        user_id = request.session.get('user_id')
        user = trading_system.get_user_info(user_id)
        if not user:
            return redirect('login')
        
        # 페이지 및 거래 유형 파라미터
        page = request.GET.get('page', 1)
        transaction_type = request.GET.get('type', 'sell')
        
        # 거래 내역 조회
        transactions = None
        if transaction_type == 'buy':
            transactions = trading_system.investment_manager.check_buy_transactions(user)
        else:
            transactions = trading_system.investment_manager.check_sell_transactions(user)
        
        # 페이지네이션 설정 (10개씩 표시)
        paginator = Paginator(transactions, 10)
        current_page = paginator.get_page(page)
        
        context = {
            'user': user,
            'transactions': current_page,
            'transaction_type': transaction_type
        }
            
        return render(request, 'management/investment.html', context)
        
    except Exception as e:
        logger.error(f"Investment management error: {str(e)}")
        return redirect('dashboard')

def transfer_management_view(request):
    """자산입출금 관리 뷰"""
    trading_system = VCTradingSystem()
    
    try:
        user_id = request.session.get('user_id')
        user = trading_system.get_user_info(user_id)
        if not user:
            return redirect('login')
        
        virtual_account = trading_system.get_virtual_account(user.virtual_account_id)
        real_account = trading_system.get_bank_account(user.account_id)
        transfers = trading_system.asset_transfer_manager.get_transfer_history(user)

        if not virtual_account or not real_account:
            logger.error("Account information not found")
            return redirect('dashboard')
        
        context = {
            'user': user,
            'virtual_account': virtual_account,
            'real_account': real_account,
            'transfers': transfers,
        }
        return render(request, 'management/transfer.html', context)
    except Exception as e:
        logger.error(f"Transfer management error: {str(e)}")
        return redirect('dashboard')

def process_transfer(request):
    """입출금 처리 뷰"""
    if request.method == 'POST':
        trading_system = VCTradingSystem()
        
        try:
            user_id = request.session.get('user_id')
            user = trading_system.get_user_info(user_id)
            if not user:
                return JsonResponse({
                    'success': False,
                    'message': '사용자 정보를 찾을 수 없습니다.'
                })
            
            transfer_type = request.POST.get('transfer_type')
            amount = Decimal(request.POST.get('amount', '0'))
            
            if amount <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': '유효하지 않은 금액입니다.'
                })

            if amount > Decimal('10000000'):
                return JsonResponse({
                    'success': False,
                    'message': '최대 거래 한도(1천만원)를 초과했습니다.'
                })
            
            if transfer_type == 'DEPOSIT':
                success, result = trading_system.asset_transfer_manager.process_deposit(
                    user, 
                    request.POST.get('from_account'),
                    amount
                )
            else:
                success, result = trading_system.asset_transfer_manager.process_withdrawal(
                    user,
                    request.POST.get('to_account'),
                    amount
                )

            if success:
                return JsonResponse({
                    'success': True,
                    'message': '처리가 완료되었습니다.',
                    'data': result
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': result
                })

        except ValueError:
            return JsonResponse({
                'success': False,
                'message': '유효하지 않은 금액입니다.'
            })
        except Exception as e:
            logger.error(f"Transfer processing error: {str(e)}")
            logger.error(f"Request POST data: {request.POST}")
            return JsonResponse({
                'success': False,
                'message': f'처리 중 오류가 발생했습니다: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': '잘못된 요청입니다.'
    })

def logout_view(request):
    """로그아웃 뷰"""
    response = redirect('login')
    
    # 세션 삭제
    request.session.flush()
    
    # 캐시 제어 헤더 설정
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    # 로그아웃 메시지 추가
    messages.success(request, '성공적으로 로그아웃되었습니다.')
    
    return response