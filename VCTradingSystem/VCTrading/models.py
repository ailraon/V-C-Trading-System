import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
import pyupbit
import logging

logger = logging.getLogger(__name__)

class VirtualAccount(models.Model):
    virtual_account_id = models.CharField(max_length=20, primary_key=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    transfer_limit = models.DecimalField(max_digits=18, decimal_places=2, default=10000000.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Virtual_Account'

class UserInfo(models.Model):
    user_id = models.CharField(max_length=20, primary_key=True)
    user_password = models.CharField(max_length=128)
    user_name = models.CharField(max_length=20)
    birth_date = models.DateField()
    phone_number = models.CharField(max_length=20)
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.CASCADE, db_column='virtual_account_id')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='ACTIVE')

    class Meta:
        db_table = 'UserInfo'

class BankAccount(models.Model):
    account_id = models.CharField(max_length=20, primary_key=True)
    bank_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Bank_Account'

class CryptoInfo(models.Model):
    crypto_id = models.CharField(max_length=20, primary_key=True)
    crypto_type = models.CharField(max_length=20)
    crypto_name = models.CharField(max_length=50)
    crypto_price = models.DecimalField(max_digits=18, decimal_places=8)
    crypto_volume = models.IntegerField()
    crypto_cap = models.IntegerField()
    executed_price = models.DecimalField(max_digits=18, decimal_places=8)
    executed_quantity = models.IntegerField()
    quote_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Crypto_Info'

class OrderInfo(models.Model):
    order_id = models.CharField(max_length=25, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='user_id')  # 사용자 정보 추가
    crypto = models.ForeignKey(CryptoInfo, on_delete=models.CASCADE, db_column='crypto_id')
    order_type = models.CharField(max_length=10)  # 'BUY' or 'SELL'
    order_price = models.DecimalField(max_digits=18, decimal_places=8)  # 주문 가격
    order_quantity = models.DecimalField(max_digits=18, decimal_places=8)  # 주문 수량
    total_amount = models.DecimalField(max_digits=18, decimal_places=2)  # 총 거래금액
    order_status = models.CharField(max_length=20, default='COMPLETED')  # 주문 상태
    executed_time = models.DateTimeField(auto_now_add=True)  # 체결 시간
    market_price = models.DecimalField(max_digits=18, decimal_places=8)  # 체결 당시 시장가

    class Meta:
        db_table = 'Order_Info'

class InvestmentPortfolio(models.Model):
    portfolio_id = models.CharField(max_length=25, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='user_id')
    crypto = models.ForeignKey(CryptoInfo, on_delete=models.CASCADE, db_column='crypto_id')
    total_quantity = models.DecimalField(max_digits=18, decimal_places=8)  # 보유 수량
    avg_buy_price = models.DecimalField(max_digits=18, decimal_places=8)  # 평균 매수가
    total_investment = models.DecimalField(max_digits=18, decimal_places=2)  # 총 매수금액
    first_buy_date = models.DateTimeField()  # 최초 매수일
    last_updated = models.DateTimeField(auto_now=True)  # 마지막 업데이트 시간

    class Meta:
        db_table = 'Investment_Portfolio'
        unique_together = ('user', 'crypto')  # 사용자별 암호화폐는 유니크해야 함

class TransferHistory(models.Model):
    transfer_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='user_id')
    bank_name = models.CharField(max_length=40)
    transfer_type = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance = models.DecimalField(max_digits=18, decimal_places=2)
    transfer_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='COMPLETED')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, db_column='account_id')
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.CASCADE, db_column='virtual_account_id')

    class Meta:
        db_table = 'Transfer_History'

class CryptoPrediction:
    def __init__(self, coin_id: str):
        self.coin_id = coin_id
        self.ticker = f'KRW-{coin_id}'
        self.scaler = MinMaxScaler()
        self.window_size = 60
        self.model = self._build_model()

    def _build_model(self):
        model = keras.Sequential([
            keras.layers.LSTM(50, return_sequences=True, input_shape=(self.window_size, 1)),
            keras.layers.LSTM(50, return_sequences=False),
            keras.layers.Dense(25),
            keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def get_prediction(self, count=20):
        try:
            current_price = pyupbit.get_current_price(self.ticker)
            df = pyupbit.get_ohlcv(self.ticker, interval="day", count=100)
            
            if df is None or current_price is None:
                raise ValueError("가격 데이터를 가져올 수 없습니다.")

            # 트렌드와 변동성 분석
            daily_returns = df['close'].pct_change().dropna()
            volatility = daily_returns.std()
            trend = daily_returns.mean()

            # 추세 방향 감지
            short_ma = df['close'].rolling(window=7).mean()
            long_ma = df['close'].rolling(window=20).mean()
            is_uptrend = short_ma.iloc[-1] > long_ma.iloc[-1]

            predictions = []
            dates = []
            last_price = current_price

            for i in range(count):
                # 변동성을 기반으로 한 랜덤 변화
                random_change = np.random.normal(0, volatility)
                
                # 추세 기반 조정
                if is_uptrend:
                    # 상승 추세일 때는 양의 방향으로 더 큰 변화
                    trend_factor = abs(trend) * 2 if trend > 0 else abs(trend)
                else:
                    # 하락 추세일 때는 음의 방향으로 더 큰 변화
                    trend_factor = -abs(trend) * 2 if trend < 0 else -abs(trend)

                # 최종 가격 변화율 계산
                change_rate = random_change + trend_factor

                # 가격 예측
                next_price = last_price * (1 + change_rate)
                
                # 극단적인 변화 방지
                max_change = 0.1  # 최대 10% 변화
                if abs((next_price - last_price) / last_price) > max_change:
                    if next_price > last_price:
                        next_price = last_price * (1 + max_change)
                    else:
                        next_price = last_price * (1 - max_change)

                predictions.append(float(next_price))
                last_price = next_price
                
                next_date = datetime.now() + timedelta(days=i+1)
                dates.append(next_date.strftime('%Y-%m-%d'))

            return {
                'dates': dates,
                'prices': predictions,
                'min_price': min(predictions),
                'max_price': max(predictions),
                'avg_price': sum(predictions) / len(predictions)
            }
                
        except Exception as e:
            logger.error(f"Prediction error for {self.ticker}: {str(e)}")
            raise