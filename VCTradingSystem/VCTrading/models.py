from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class BankAccount(models.Model):
    account_id = models.CharField(max_length=20, primary_key=True)
    bank_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Bank_Account'

class VirtualAccount(models.Model):
    virtual_account_id = models.CharField(max_length=20, primary_key=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
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
    order_id = models.CharField(max_length=20, primary_key=True)
    crypto = models.ForeignKey(CryptoInfo, on_delete=models.CASCADE, db_column='crypto_id')
    order_date = models.DateField()
    order_price = models.DecimalField(max_digits=18, decimal_places=2)
    order_cap = models.IntegerField()

    class Meta:
        db_table = 'Order_Info'

class InvestmentHistory(models.Model):
    transaction_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='user_id')
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, db_column='order_id')
    crypto = models.ForeignKey(CryptoInfo, on_delete=models.CASCADE, db_column='crypto_id')
    transaction_type = models.CharField(max_length=10)
    trade_volume = models.DecimalField(max_digits=18, decimal_places=8)
    total_trade_amount = models.DecimalField(max_digits=18, decimal_places=2)
    valuation = models.DecimalField(max_digits=18, decimal_places=2)
    rate_of_return = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='COMPLETED')
    account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, db_column='account_id')
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.SET_NULL, null=True, db_column='virtual_account_id')

    class Meta:
        db_table = 'Investment_History'

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