# Generated by Django 5.1.3 on 2024-11-25 10:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserInfo",
            fields=[
                (
                    "user_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("password", models.CharField(max_length=128)),
                ("user_name", models.CharField(max_length=20)),
                ("birth_date", models.DateField()),
                ("phone_number", models.CharField(max_length=20)),
                ("account_id", models.CharField(max_length=20)),
                ("virtual_account_id", models.CharField(max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(default="ACTIVE", max_length=10)),
            ],
            options={
                "db_table": "UserInfo",
            },
        ),
        migrations.CreateModel(
            name="TransferHistory",
            fields=[
                (
                    "transfer_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("bank_id", models.CharField(max_length=20)),
                ("account_id", models.CharField(max_length=20)),
                ("virtual_account_id", models.CharField(max_length=20)),
                ("transfer_type", models.CharField(max_length=10)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=18)),
                ("balance", models.DecimalField(decimal_places=2, max_digits=18)),
                ("transfer_time", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(default="COMPLETED", max_length=10)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="VCTrading.userinfo",
                    ),
                ),
            ],
            options={
                "db_table": "Transfer_History",
            },
        ),
        migrations.CreateModel(
            name="InvestmentHistory",
            fields=[
                (
                    "transaction_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("crypto_id", models.CharField(max_length=20)),
                ("transaction_type", models.CharField(max_length=10)),
                ("trade_volume", models.DecimalField(decimal_places=8, max_digits=18)),
                (
                    "total_trade_amount",
                    models.DecimalField(decimal_places=2, max_digits=18),
                ),
                ("valuation", models.DecimalField(decimal_places=2, max_digits=18)),
                ("rate_of_return", models.DecimalField(decimal_places=2, max_digits=8)),
                ("transaction_time", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(default="COMPLETED", max_length=10)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="VCTrading.userinfo",
                    ),
                ),
            ],
            options={
                "db_table": "Investment_History",
            },
        ),
    ]
