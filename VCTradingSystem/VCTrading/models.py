from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class UserInfo(models.Model):
    user_id = models.CharField(max_length=20, primary_key=True)
    password = models.CharField(max_length=128)
    user_name = models.CharField(max_length=20)
    birth_date = models.DateField()
    phone_number = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20)
    virtual_account_id = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='ACTIVE')

    class Meta:
        db_table = 'UserInfo'

class InvestmentHistory(models.Model):
    transaction_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    crypto_id = models.CharField(max_length=20)
    transaction_type = models.CharField(max_length=10)
    trade_volume = models.DecimalField(max_digits=18, decimal_places=8)
    total_trade_amount = models.DecimalField(max_digits=18, decimal_places=2)
    valuation = models.DecimalField(max_digits=18, decimal_places=2)
    rate_of_return = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='COMPLETED')

    class Meta:
        db_table = 'Investment_History'

class TransferHistory(models.Model):
    transfer_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    bank_id = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20)
    virtual_account_id = models.CharField(max_length=20)
    transfer_type = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance = models.DecimalField(max_digits=18, decimal_places=2)
    transfer_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='COMPLETED')

    class Meta:
        db_table = 'Transfer_History'