from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
import random

from VCTrading.models import (
    CryptoInfo, 
    OrderInfo, 
    InvestmentPortfolio,
    UserInfo
)

def generate_test_data():
    """테스트 데이터를 생성하는 함수"""
    try:
        print("테스트 데이터 생성 시작...")
        
        # 가상화폐 초기 데이터
        crypto_data = [
            {
                'id': 'BTC001',
                'type': 'BTC',
                'name': '비트코인',
                'price': Decimal('58000000.00'),
            },
            {
                'id': 'ETH001',
                'type': 'ETH',
                'name': '이더리움',
                'price': Decimal('3500000.00'),
            },
            {
                'id': 'XRP001',
                'type': 'XRP',
                'name': '리플',
                'price': Decimal('800.00'),
            },
            {
                'id': 'DOGE001',
                'type': 'DOGE',
                'name': '도지코인',
                'price': Decimal('150.00'),
            }
        ]

        with transaction.atomic():
            # 기존 데이터 삭제
            print("기존 데이터 삭제 중...")
            CryptoInfo.objects.all().delete()
            OrderInfo.objects.all().delete()
            InvestmentPortfolio.objects.all().delete()
            
            # 1. CryptoInfo 데이터 생성
            created_cryptos = []
            for crypto in crypto_data:
                crypto_obj = CryptoInfo.objects.create(
                    crypto_id=crypto['id'],
                    crypto_type=crypto['type'],
                    crypto_name=crypto['name'],
                    crypto_price=crypto['price'],
                    crypto_volume=random.randint(1000000, 10000000),
                    crypto_cap=random.randint(10000000, 100000000),
                    executed_price=crypto['price'] * Decimal(str(random.uniform(0.98, 1.02))),
                    executed_quantity=random.randint(1000, 10000)
                )
                created_cryptos.append(crypto_obj)
            print(f"가상화폐 데이터 생성 완료 ({len(created_cryptos)}개)")

            users = UserInfo.objects.all()
            if not users:
                print("등록된 사용자가 없습니다.")
                return False

            # 2. 각 사용자별 주문 및 포트폴리오 생성
            for user in users:
                print(f"\n사용자 {user.user_id}의 데이터 생성 중...")
                
                for crypto in created_cryptos:
                    # 매수 주문 2-3개 생성
                    buy_orders = []
                    total_quantity = Decimal('0')
                    total_investment = Decimal('0')
                    
                    for i in range(random.randint(2, 3)):
                        quantity = Decimal(str(random.uniform(0.1, 2.0)))
                        price = crypto.crypto_price * Decimal(str(random.uniform(0.8, 1.2)))
                        total = quantity * price
                        
                        order = OrderInfo.objects.create(
                            order_id=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
                            user=user,
                            crypto=crypto,
                            order_type='BUY',
                            order_price=price,
                            order_quantity=quantity,
                            total_amount=total,
                            market_price=crypto.crypto_price
                        )
                        buy_orders.append(order)
                        total_quantity += quantity
                        total_investment += total
                    
                    # 매도 주문 1-2개 생성
                    sell_quantity = Decimal('0')
                    for i in range(random.randint(1, 2)):
                        quantity = Decimal(str(random.uniform(0.1, 0.5)))
                        if quantity > total_quantity - sell_quantity:
                            quantity = total_quantity - sell_quantity
                        
                        if quantity <= 0:
                            break
                            
                        price = crypto.crypto_price * Decimal(str(random.uniform(0.8, 1.2)))
                        total = quantity * price
                        
                        OrderInfo.objects.create(
                            order_id=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
                            user=user,
                            crypto=crypto,
                            order_type='SELL',
                            order_price=price,
                            order_quantity=quantity,
                            total_amount=total,
                            market_price=crypto.crypto_price
                        )
                        sell_quantity += quantity

                    # 남은 수량이 있으면 포트폴리오 생성
                    remaining_quantity = total_quantity - sell_quantity
                    if remaining_quantity > 0 and buy_orders:
                        avg_price = total_investment / total_quantity
                        InvestmentPortfolio.objects.create(
                            portfolio_id=f"PF{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
                            user=user,
                            crypto=crypto,
                            total_quantity=remaining_quantity,
                            avg_buy_price=avg_price,
                            total_investment=remaining_quantity * avg_price,
                            first_buy_date=min(order.executed_time for order in buy_orders)
                        )

                print(f"사용자 {user.user_id}의 데이터 생성 완료")

        print("\n모든 테스트 데이터 생성 완료!")
        return True

    except Exception as e:
        print(f"테스트 데이터 생성 중 오류 발생: {str(e)}")
        return False