from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class BankAccount(models.Model):
    account_id = models.CharField(max_length=20, primary_key=True)
    bank_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    user_id = models.CharField(max_length=20, null=True)  # 추가
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Bank_Account'

class VirtualAccount(models.Model):
    virtual_account_id = models.CharField(max_length=20, primary_key=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    transfer_limit = models.DecimalField(max_digits=18, decimal_places=2, default=10000000.00)  # 추가
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Virtual_Account'

class UserInfo(models.Model):
    user_id = models.CharField(max_length=20, primary_key=True)
    user_password = models.CharField(max_length=128)
    user_name = models.CharField(max_length=20)
    birth_date = models.DateField()
    phone_number = models.CharField(max_length=20)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, db_column='account_id')
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.CASCADE, db_column='virtual_account_id')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='ACTIVE')

    class Meta:
        db_table = 'UserInfo'

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