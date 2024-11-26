from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class UserInfo(models.Model):
    user_id = models.CharField(max_length=20, primary_key=True)
    user_password = models.CharField(max_length=128)  # password -> user_password로 변경
    user_name = models.CharField(max_length=20)
    birth_date = models.DateField()
    phone_number = models.CharField(max_length=20)
    account_id = models.CharField(max_length=20, db_index=True)
    virtual_account_id = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='ACTIVE')

    class Meta:
        db_table = 'UserInfo'

class BankAccount(models.Model):  # Bank_Account -> BankAccount
    account_id = models.CharField(max_length=20, primary_key=True)
    bank_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Bank_Account'

class VirtualAccount(models.Model):  # Virtual_Account -> VirtualAccount
    virtual_account_id = models.CharField(max_length=20, primary_key=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Virtual_Account'

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
    account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True)  # 수정됨
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.SET_NULL, null=True)  # 수정됨

    class Meta:
        db_table = 'Investment_History'

class TransferHistory(models.Model):
    transfer_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    transfer_type = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance = models.DecimalField(max_digits=18, decimal_places=2)
    transfer_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='COMPLETED')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)  # 수정됨
    virtual_account = models.ForeignKey(VirtualAccount, on_delete=models.CASCADE)  # 수정됨

    class Meta:
        db_table = 'Transfer_History'