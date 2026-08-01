

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otp_manager', '0006_alter_sms_template_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sms_template',
            name='name',
            field=models.CharField(choices=[('signup', 'ثبت نام'), ('auto_signup', 'ثبت نام اتوماتیک'), ('login', 'ورود'), ('close_sandogh', 'بستن صندوق'), ('night_order', 'سفارش شب'), ('personel_night_order', 'سفارش به نام پرسنل'), ('daily_report', 'گزارش روزانه'), ('task_manager', 'مدیریت تسک'), ('daily_no_task', 'عدم انجام تسک')], max_length=100, verbose_name='نوع قالب پیامک'),
        ),
    ]
