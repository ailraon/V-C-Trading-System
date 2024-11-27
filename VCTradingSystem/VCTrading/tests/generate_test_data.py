from django.db import transaction
from datetime import datetime, timedelta
import random
from VCTrading.models import CryptoInfo, OrderInfo, InvestmentHistory

'''
테스트 데이터 생성 방법 파이썬 버전 13으로 해야 함
python manage.py shell

from VCTrading.tests.generate_test_data import generate_test_data
generate_test_data()
'''

def generate_test_data():
    """테스트 데이터를 생성하는 함수"""
    try:
        print('테스트 데이터 생성 시작...')
        
        # 가상화폐 종류 정의
        crypto_types = ['BTC', 'ETH', 'XRP', 'DOGE']
        crypto_names = ['Bitcoin', 'Ethereum', 'Ripple', 'Dogecoin']
        
        with transaction.atomic():
            # Crypto_Info 데이터 생성
            crypto_objects = []
            for i in range(len(crypto_types)):
                crypto = CryptoInfo.objects.create(
                    crypto_id=f'CRYPTO_{crypto_types[i]}',
                    crypto_type=crypto_types[i],
                    crypto_name=crypto_names[i],  # 이름 추가
                    crypto_price=random.uniform(1000, 100000),
                    crypto_volume=random.randint(1000, 10000),
                    crypto_cap=random.randint(10000000, 100000000),
                    executed_price=random.uniform(1000, 100000),
                    executed_quantity=random.randint(100, 1000)
                )
                crypto_objects.append(crypto)
            print(f'가상화폐 정보 {len(crypto_objects)}개 생성 완료')

            # OrderInfo 데이터 생성 (30개로 증가)
            order_objects = []
            for i in range(30):
                order = OrderInfo.objects.create(
                    order_id=f'ORDER_{datetime.now().strftime("%Y%m%d")}_{i+1}',
                    crypto=random.choice(crypto_objects),
                    order_date=datetime.now().date() - timedelta(days=random.randint(0, 30)),
                    order_price=random.uniform(1000, 100000),
                    order_cap=random.randint(1000, 10000)
                )
                order_objects.append(order)
            print(f'주문 정보 {len(order_objects)}개 생성 완료')

            # Investment_History 데이터 생성 (총 30개: 매수 15개, 매도 15개)
            base_date = datetime.now() - timedelta(days=30)
            
            # 매수 거래 15개 생성
            for i in range(15):
                trade_amount = random.uniform(1000000, 10000000)
                rate_return = random.uniform(-15, 15)
                
                InvestmentHistory.objects.create(
                    transaction_id=f'TR{datetime.now().strftime("%Y%m%d")}B{i+1}',
                    user_id='test01',
                    order=order_objects[i],
                    crypto=random.choice(crypto_objects),
                    transaction_type='BUY',
                    trade_volume=random.uniform(0.1, 10),
                    total_trade_amount=trade_amount,
                    valuation=trade_amount * (1 + rate_return/100),
                    rate_of_return=rate_return,
                    transaction_time=base_date + timedelta(days=i),
                    status='COMPLETED'
                )

            # 매도 거래 15개 생성
            for i in range(15):
                trade_amount = random.uniform(1000000, 10000000)
                rate_return = random.uniform(-15, 15)
                
                InvestmentHistory.objects.create(
                    transaction_id=f'TR{datetime.now().strftime("%Y%m%d")}S{i+1}',
                    user_id='test01',
                    order=order_objects[i+15],
                    crypto=random.choice(crypto_objects),
                    transaction_type='SELL',
                    trade_volume=random.uniform(0.1, 10),
                    total_trade_amount=trade_amount,
                    valuation=trade_amount * (1 + rate_return/100),
                    rate_of_return=rate_return,
                    transaction_time=base_date + timedelta(days=i),
                    status='COMPLETED'
                )

            print('투자 내역 생성 완료 (매수 15개, 매도 15개)')
            print('모든 테스트 데이터 생성이 완료되었습니다!')
            return True

    except Exception as e:
        print(f'데이터 생성 중 오류 발생: {str(e)}')
        return False