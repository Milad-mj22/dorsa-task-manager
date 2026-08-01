
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='نام حساب')),
                ('account_number', models.CharField(max_length=50, unique=True, verbose_name='شماره حساب')),
                ('bank_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='نام بانک')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
            ],
        ),
        migrations.CreateModel(
            name='SMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(max_length=50)),
                ('message', models.TextField()),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
