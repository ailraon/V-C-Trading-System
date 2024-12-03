from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.http import JsonResponse  # JsonResponse 추가
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.contrib.sessions.models import Session
from datetime import datetime
import logging
from .utils import get_krw_markets_with_prices_and_change  # 유틸리티 함수 가져오기

import re  # re 모듈 추가
from decimal import Decimal
from .models import UserInfo, TransferHistory, BankAccount, VirtualAccount, CryptoInfo, OrderInfo, InvestmentPortfolio
logger = logging.getLogger(__name__)

'''
서버 실행문
cd VCTradingSystem
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

            # 계좌번호 중복 검사 - BankAccount 테이블에서 검사
            if BankAccount.objects.filter(account_id=user_data['account_id']).exists():
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
                'account_id': request.POST.get('account_id'),
                'bank_name': request.POST.get('bank_name')
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

            # 기존 세션이 있는지 확인
            existing_session = Session.objects.filter(
                expire_date__gt=datetime.now(),
                session_data__contains=user_id
            ).first()

            if existing_session:
                # 기존 세션 종료
                existing_session.delete()
                logger.info(f"Previous session terminated for user: {user_id}")

            # 새로운 세션 생성
            request.session['user_id'] = user_id
            request.session.set_expiry(3600)  # 1시간 세션 유효기간 설정

            return True, user_id
        except Exception as e:
            logger.error(f"Login request error: {str(e)}")
            return False, str(e)
        
    def update_user_info(self, user_id, update_data):
        """사용자 정보 수정"""
        try:
            user = UserInfo.objects.get(user_id=user_id)
            
            # 비밀번호 변경 처리
            if update_data.get('new_password'):
                if not check_password(update_data['current_password'], user.user_password):
                    return False, "현재 비밀번호가 일치하지 않습니다."
                user.user_password = make_password(update_data['new_password'])
            
            # 다른 정보 업데이트
            if update_data.get('user_name'):
                user.user_name = update_data['user_name']
            if update_data.get('birth_date'):
                user.birth_date = datetime.strptime(update_data['birth_date'], '%Y-%m-%d')
            if update_data.get('phone_number'):
                # 전화번호 중복 체크
                if UserInfo.objects.filter(phone_number=update_data['phone_number']).exclude(user_id=user_id).exists():
                    return False, "이미 등록된 전화번호입니다."
                user.phone_number = update_data['phone_number']
            
            user.save()
            return True, "사용자 정보가 성공적으로 수정되었습니다."
            
        except Exception as e:
            logger.error(f"User info update error: {str(e)}")
            return False, str(e)
        
    def withdraw_user(self, user_id, password):
        """회원 탈퇴 처리"""
        try:
            with transaction.atomic():
                user = UserInfo.objects.select_related(
                    'account', 
                    'virtual_account'
                ).get(user_id=user_id)

                # 비밀번호 확인
                if not check_password(password, user.user_password):
                    return False, "비밀번호가 일치하지 않습니다."

                # 관련된 거래 내역 삭제
                InvestmentPortfolio.objects.filter(user=user).delete()
                TransferHistory.objects.filter(user=user).delete()

                # 사용자의 모든 실계좌 조회 및 삭제
                BankAccount.objects.filter(
                    Q(account_id=user.account_id) |
                    Q(user_id=user_id)
                ).delete()

                # 가상계좌 삭제
                if user.virtual_account:
                    user.virtual_account.delete()

                # 사용자 삭제
                user.delete()

                # 모든 세션 삭제
                Session.objects.filter(
                    session_data__contains=user_id
                ).delete()

                return True, "회원 탈퇴가 완료되었습니다."

        except UserInfo.DoesNotExist:
            return False, "사용자 정보를 찾을 수 없습니다."
        except Exception as e:
            logger.error(f"User withdrawal error: {str(e)}")
            return False, "회원 탈퇴 처리 중 오류가 발생했습니다."
        
    def update_transfer_limit(self, user_id, transfer_limit):
        """입출금 한도 설정"""
        try:
            if not transfer_limit.isdigit():
                return False, "입출금 한도는 숫자만 입력 가능합니다."
                
            transfer_limit = Decimal(transfer_limit)
            if transfer_limit <= 0:
                return False, "입출금 한도는 0보다 커야 합니다."

            virtual_account = VirtualAccount.objects.get(userinfo__user_id=user_id)
            virtual_account.transfer_limit = transfer_limit
            virtual_account.save()
            
            return True, "입출금 한도가 성공적으로 설정되었습니다."
        except Exception as e:
            logger.error(f"Transfer limit update error: {str(e)}")
            return False, "입출금 한도 설정 중 오류가 발생했습니다."

    def get_user_accounts(self, user_id):
        """사용자의 모든 실계좌 조회"""
        try:
            return BankAccount.objects.filter(user_id=user_id)
        except Exception as e:
            logger.error(f"Get user accounts error: {str(e)}")
            return None

    def add_bank_account(self, user_id, bank_name, account_id):
        """실계좌 추가"""
        try:
            if not account_id.isdigit():
                return False, "계좌번호는 숫자만 입력 가능합니다."

            if BankAccount.objects.filter(account_id=account_id).exists():
                return False, "이미 등록된 계좌번호입니다."

            # 첫 번째 계좌 추가인지 확인
            existing_accounts = self.get_user_accounts(user_id)
            
            BankAccount.objects.create(
                account_id=account_id,
                bank_name=bank_name,
                balance=0.00,
                user_id=user_id
            )
            
            return True, "계좌가 성공적으로 추가되었습니다."
        except Exception as e:
            logger.error(f"Bank account addition error: {str(e)}")
            return False, "계좌 추가 중 오류가 발생했습니다."

    def delete_bank_account(self, user_id, account_id):
        """실계좌 삭제"""
        try:
            # 계좌 개수 확인
            user_accounts = self.get_user_accounts(user_id)
            if user_accounts.count() <= 1:
                return False, "최소 1개의 실계좌는 유지해야 합니다."

            # 계좌 삭제
            account = BankAccount.objects.get(account_id=account_id, user_id=user_id)
            account.delete()
            return True, "계좌가 성공적으로 삭제되었습니다."

        except BankAccount.DoesNotExist:
            return False, "해당 계좌를 찾을 수 없습니다."
        except Exception as e:
            logger.error(f"Bank account deletion error: {str(e)}")
            return False, "계좌 삭제 중 오류가 발생했습니다."
    
    # ==========User Class 뷰 처리 메서드=========
    def handle_signup(self, request):
        """회원가입 뷰 처리"""
        context = {}
        if request.method == 'POST':
            trading_system = VCTradingSystem()
            
            # POST 데이터를 context에 저장
            context.update({
                'user_id': request.POST.get('user_id', ''),
                'user_name': request.POST.get('user_name', ''),
                'birth_date': request.POST.get('birth_date', ''),
                'phone_number': request.POST.get('phone_number', ''),
                'bank_name': request.POST.get('bank_name', ''),
                'account_id': request.POST.get('account_id', '')
            })

            # 은행 선택 검증
            if not context['bank_name']:
                context['error'] = "은행을 선택해주세요."
                context['error_field'] = 'bank_name'
                return render(request, 'auth/signup.html', context)
            
            # 계좌번호 형식 검증
            account_id = context['account_id']
            if not account_id.isdigit():
                context['error'] = "계좌번호는 숫자만 입력 가능합니다."
                context['error_field'] = 'account_id'
                return render(request, 'auth/signup.html', context)
            
            success, result = self.sign_up_request(request)
            if not success:
                context['error'] = result
                error_field = result.split()[0].lower()
                if error_field in ['이미', '올바른', '존재하지']:
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
            
            result['bank_name'] = context['bank_name']
            success, message = trading_system.process_sign_up(result)
            if not success:
                context['error'] = message
                return render(request, 'auth/signup.html', context)
            
            messages.success(request, '회원가입이 성공적으로 완료되었습니다. 로그인해주세요.')
            return redirect('login')
        
        return render(request, 'auth/signup.html')

    def handle_login(self, request):
        """로그인 뷰 처리"""
        context = {}
        if request.method == 'POST':
            trading_system = VCTradingSystem()
            
            success, result = self.login_request(request)
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

    def handle_logout(self, request):
        """로그아웃 뷰 처리"""
        response = redirect('login')
        request.session.flush()
        
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        messages.success(request, '성공적으로 로그아웃되었습니다.')
        return response
    
    def handle_user_info_management(self, request, trading_system):
        """사용자 정보 관리 뷰 처리"""
        try:
            user_id = request.session.get('user_id')
            user = trading_system.get_user_info(user_id)
            if not user:
                return redirect('login')

            if request.method == 'POST':
                form_type = request.POST.get('form_type')
                success = False  # Initialize success variable
                message = ""    # Initialize message variable

                if form_type == 'user_info':
                    # 기존 사용자 정보 수정 처리
                    update_data = {
                        'user_name': request.POST.get('user_name'),
                        'birth_date': request.POST.get('birth_date'),
                        'phone_number': request.POST.get('phone_number'),
                        'current_password': request.POST.get('current_password'),
                        'new_password': request.POST.get('new_password')
                    }
                    success, message = self.update_user_info(user_id, update_data)

                elif form_type == 'transfer_limit':
                    # 입출금 한도 설정 처리
                    transfer_limit = request.POST.get('transfer_limit')
                    success, message = self.update_transfer_limit(user_id, transfer_limit)

                elif form_type == 'add_account':
                    # 실계좌 추가 처리
                    bank_name = request.POST.get('bank_name')
                    account_id = request.POST.get('account_id')
                    success, message = self.add_bank_account(user_id, bank_name, account_id)

                elif form_type == 'delete_account':
                    # 실계좌 삭제 처리
                    account_id = request.POST.get('account_id')
                    success, message = self.delete_bank_account(user_id, account_id)

                elif form_type == 'withdraw':  
                    # 회원 탈퇴 처리
                    password = request.POST.get('withdrawal_password')
                    if not password:
                        messages.error(request, '비밀번호를 입력해주세요.')
                        return redirect(f"{reverse('user_info_management')}?tab=user-info")

                    success, message = self.withdraw_user(user_id, password)

                    if success:
                        # 세션 삭제
                        request.session.flush()
                        messages.success(request, message)
                        return redirect('login')
                    else:
                        messages.error(request, message)
                        return redirect(f"{reverse('user_info_management')}?tab=user-info")

                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)

                # 현재 활성화된 탭을 유지하기 위한 파라미터 추가
                tab = 'account-info' if form_type in ['transfer_limit', 'add_account', 'delete_account'] else 'user-info'
                return redirect(f"{reverse('user_info_management')}?tab={tab}")

            # GET 요청 처리
            real_accounts = self.get_user_accounts(user_id)
            virtual_account = trading_system.get_virtual_account(user.virtual_account_id)

            context = {
                'user': user,
                'real_accounts': real_accounts,
                'virtual_account': virtual_account,
            }

            return render(request, 'management/user_info.html', context)

        except Exception as e:
            logger.error(f"User info management error: {str(e)}")
            messages.error(request, "사용자 정보 처리 중 오류가 발생했습니다.")
            return redirect('dashboard')
    
    
class InvestmentManager:
    """투자내역 관리 클래스"""
    def __init__(self):
        pass

    def get_portfolio(self, user):
        """사용자의 투자 포트폴리오 조회"""
        try:
            portfolios = InvestmentPortfolio.objects.filter(
                user=user
            ).select_related('crypto')

            total_investment = 0
            total_valuation = 0

            for portfolio in portfolios:
                # 현재 평가금액 계산
                portfolio.current_valuation = portfolio.total_quantity * portfolio.crypto.crypto_price
                # 평가손익 계산
                portfolio.profit = portfolio.current_valuation - portfolio.total_investment
                # 수익률 계산
                portfolio.profit_rate = (portfolio.profit / portfolio.total_investment * 100) if portfolio.total_investment > 0 else 0

                total_investment += portfolio.total_investment
                total_valuation += portfolio.current_valuation

            summary = {
                'total_investment': total_investment,
                'total_valuation': total_valuation,
                'total_profit': total_valuation - total_investment,
                'total_profit_rate': ((total_valuation - total_investment) / total_investment * 100) 
                                   if total_investment > 0 else 0
            }

            return portfolios, summary
        except Exception as e:
            logger.error(f"Portfolio retrieval error: {str(e)}")
            return None, None

    def get_order_history(self, user, order_type):
        """매수/매도 거래내역 조회"""
        try:
            return OrderInfo.objects.filter(
                user=user,
                order_type=order_type.upper()
            ).select_related('crypto').order_by('-executed_time')
        except Exception as e:
            logger.error(f"Order history retrieval error: {str(e)}")
            return None

    def handle_investment_management(self, request, trading_system):
        """투자내역 관리 뷰 처리"""
        try:
            user_id = request.session.get('user_id')
            user = trading_system.get_user_info(user_id)
            if not user:
                return redirect('login')

            # 기본 탭을 portfolio로 설정
            active_tab = request.GET.get('tab', 'portfolio')
            transaction_type = request.GET.get('type', 'sell')  # 거래내역 탭의 기본값은 매도
            page = request.GET.get('page', 1)

            context = {
                'user': user,
                'active_tab': active_tab,
                'transaction_type': transaction_type
            }

            # 투자내역 데이터는 항상 조회
            portfolios, summary = self.get_portfolio(user)
            if portfolios and summary:
                context.update({
                    'portfolios': portfolios,
                    'total_investment': summary['total_investment'],
                    'total_valuation': summary['total_valuation'],
                    'total_profit': summary['total_profit'],
                    'total_profit_rate': summary['total_profit_rate']
                })

            # 거래내역 탭이 활성화된 경우에만 거래내역 조회
            if active_tab == 'history':
                orders = self.get_order_history(user, transaction_type)
                if orders:
                    paginator = Paginator(orders, 10)
                    current_page = paginator.get_page(page)
                    context.update({
                        'orders': current_page
                    })

            return render(request, 'management/investment.html', context)

        except Exception as e:
            logger.error(f"Investment management error: {str(e)}")
            messages.error(request, "투자내역 조회 중 오류가 발생했습니다.")
            return redirect('dashboard')


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
                # 입금인 경우
                if transfer.transfer_type == 'DEPOSIT':
                    transfer.from_account = f'{transfer.account.bank_name} {transfer.account.account_id}'
                    transfer.to_account = transfer.virtual_account.virtual_account_id
                # 출금인 경우
                else:
                    transfer.from_account = transfer.virtual_account.virtual_account_id
                    transfer.to_account = f'{transfer.account.bank_name} {transfer.account.account_id}'

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
            from_account = BankAccount.objects.get(account_id=from_account_id, user_id=user.user_id)
            to_account = VirtualAccount.objects.get(virtual_account_id=user.virtual_account_id)

            # 입출금 한도 체크 추가
            if amount > to_account.transfer_limit:
                return False, f'입금 한도를 초과했습니다. (한도: {to_account.transfer_limit:,}원)'

            if from_account.balance < amount:
                return False, f'실계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'

            return self._process_transfer(user, from_account, to_account, amount, 'DEPOSIT')
        except BankAccount.DoesNotExist:
            return False, "해당 계좌를 찾을 수 없습니다."
        except Exception as e:
            logger.error(f"Deposit processing error: {str(e)}")
            return False, str(e)

    def process_withdrawal(self, user, to_account_id, amount):
        """출금 처리"""
        try:
            from_account = VirtualAccount.objects.get(virtual_account_id=user.virtual_account_id)
            to_account = BankAccount.objects.get(account_id=to_account_id, user_id=user.user_id)

            # 입출금 한도 체크 추가
            if amount > from_account.transfer_limit:
                return False, f'출금 한도를 초과했습니다. (한도: {from_account.transfer_limit:,}원)'

            if from_account.balance < amount:
                return False, f'가상계좌 잔액이 부족합니다. (현재 잔액: {from_account.balance:,}원)'

            return self._process_transfer(user, from_account, to_account, amount, 'WITHDRAWAL')
        except BankAccount.DoesNotExist:
            return False, "해당 계좌를 찾을 수 없습니다."
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
    
    # ==========AssetTransferManager Class 뷰 처리 메서드=========
    def handle_transfer_management(self, request, trading_system):
        """자산입출금 관리 뷰 처리"""
        try:
            user_id = request.session.get('user_id')
            user = trading_system.get_user_info(user_id)
            if not user:
                return redirect('login')
            
            page = request.GET.get('page', 1)
            
            virtual_account = trading_system.get_virtual_account(user.virtual_account_id)
            real_accounts = User().get_user_accounts(user_id)  # 실계좌 목록 조회
            transfers = self.get_transfer_history(user)

            if not virtual_account or not real_accounts:
                logger.error("Account information not found")
                return redirect('dashboard')
            
            paginator = Paginator(transfers, 10)
            current_page = paginator.get_page(page)
            
            context = {
                'user': user,
                'virtual_account': virtual_account,
                'real_accounts': real_accounts,  # 실계좌 목록 추가
                'transfers': current_page,
            }
            return render(request, 'management/transfer.html', context)
        except Exception as e:
            logger.error(f"Transfer management error: {str(e)}")
            return redirect('dashboard')

    def handle_process_transfer(self, request, trading_system):
        """입출금 처리 뷰"""
        if request.method == 'POST':
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
                    success, result = self.process_deposit(
                        user, 
                        request.POST.get('from_account'),
                        amount
                    )
                else:
                    success, result = self.process_withdrawal(
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
                # 가상 계좌 생성
                virtual_account = VirtualAccount.objects.create(
                    virtual_account_id=virtual_account_id,
                    balance=0.00
                )

                # UserInfo 생성
                user_info = UserInfo.objects.create(
                    user_id=user_data['user_id'],
                    user_password=make_password(user_data['user_password']),
                    user_name=user_data['user_name'],
                    birth_date=datetime.strptime(user_data['birth_date'], '%Y-%m-%d'),
                    phone_number=user_data['phone_number'],
                    virtual_account=virtual_account
                )

                # 첫 번째 은행 계좌 생성
                BankAccount.objects.create(
                    account_id=user_data['account_id'],
                    bank_name=user_data['bank_name'],
                    balance=0.00,
                    user_id=user_data['user_id']
                )

                return True, "회원가입이 완료되었습니다."

        except Exception as e:
            logger.error(f"Sign up processing error: {str(e)}")
            return False, f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"

    def get_user_info(self, user_id):
        """사용자 정보 조회"""
        try:
            return UserInfo.objects.select_related('virtual_account').get(user_id=user_id)
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
    
    
    def handle_test_deposit(self, request):
        """테스트용 실계좌 입금 처리"""
        if request.method == 'POST':
            try:
                user_id = request.session.get('user_id')
                user = self.get_user_info(user_id)
                if not user:
                    messages.error(request, '사용자 정보를 찾을 수 없습니다.')
                    return JsonResponse({
                        'success': False,
                        'message': '사용자 정보를 찾을 수 없습니다.'
                    })
                
                account_id = request.POST.get('account_id')
                amount = Decimal(request.POST.get('amount', '0'))
                
                if amount <= 0:
                    messages.error(request, '유효하지 않은 금액입니다.')
                    return JsonResponse({
                        'success': False,
                        'message': '유효하지 않은 금액입니다.'
                    })
                
                try:
                    with transaction.atomic():
                        # 선택한 실계좌에 입금
                        real_account = BankAccount.objects.get(
                            account_id=account_id,
                            user_id=user_id
                        )
                        real_account.balance += amount
                        real_account.save()
                    
                    messages.success(request, f'{amount:,.0f}원이 입금되었습니다.')
                    return JsonResponse({
                        'success': True,
                        'message': '입금이 완료되었습니다.',
                        'data': {
                            'balance': str(real_account.balance)
                        }
                    })
                except BankAccount.DoesNotExist:
                    messages.error(request, '해당 계좌를 찾을 수 없습니다.')
                    return JsonResponse({
                        'success': False,
                        'message': '해당 계좌를 찾을 수 없습니다.'
                    })
                    
            except Exception as e:
                logger.error(f"Test deposit error: {str(e)}")
                messages.error(request, '처리 중 오류가 발생했습니다.')
                return JsonResponse({
                    'success': False,
                    'message': f'처리 중 오류가 발생했습니다: {str(e)}'
                })
        
        messages.error(request, '잘못된 요청입니다.')
        return JsonResponse({
            'success': False,
            'message': '잘못된 요청입니다.'
        })
    
    # ==========VCTradingSystem Class 뷰 처리 메서드=========
    def handle_dashboard(self, request):
        """대시보드 뷰 처리"""
        try:
            user_id = request.session.get('user_id')
            user = self.get_user_info(user_id)
            if not user:
                return redirect('login')
            
            return render(request, 'dashboard/dashboard.html', {'user': user})
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return redirect('login')


# 뷰 함수들은 이제 단순히 클래스의 메서드를 호출하는 래퍼가 됩니다:
def signup_view(request):
    user = User()
    return user.handle_signup(request)

def login_view(request):
    user = User()
    return user.handle_login(request)

def logout_view(request):
    user = User()
    return user.handle_logout(request)

def user_info_management_view(request):
    user = User()
    trading_system = VCTradingSystem()
    return user.handle_user_info_management(request, trading_system)

def dashboard_view(request):
    trading_system = VCTradingSystem()
    return trading_system.handle_dashboard(request)

def investment_management_view(request):
    trading_system = VCTradingSystem()
    return trading_system.investment_manager.handle_investment_management(request, trading_system)

def transfer_management_view(request):
    trading_system = VCTradingSystem()
    return trading_system.asset_transfer_manager.handle_transfer_management(request, trading_system)

def process_transfer(request):
    trading_system = VCTradingSystem()
    return trading_system.asset_transfer_manager.handle_process_transfer(request, trading_system)

def deposit_to_real_account(request):
    trading_system = VCTradingSystem()
    return trading_system.handle_test_deposit(request)

class cryptocurrency:
    """가상화폐 클래스"""
    def __init__(self):
        pass

    def get_crypto_list_info(self):
        """가상화폐 전체 조회"""
        try:
            return True
        except:
            return False
    
    def get_crypto_detail_info(self, crypto_id):
        """가상화폐 상세정보 조회"""
        try:
            
            return True
        except:
            return False
    
    def sell_crypto():
        """가상화폐 매도"""
        try:
            return True
        except:
            return False
    
    def buy_crypto():
        """가상화폐 매수"""
        try:
            return True
        except:
            return False

def cryptolist_view(request):
    """
    가상화폐 목록 및 가격 조회
    """
    crypto = cryptocurrency()

    try:
        market_data = get_krw_markets_with_prices_and_change()
        
        context = {
            "market_data": market_data
        }

        return render(request, "cryptocurrency/cryptolist.html", context)

    except Exception as e:
        return render(request, "cryptocurrency/cryptolist.html", {"error": str(e)})
