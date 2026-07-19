# در فایل management/commands/send_reminder_sms.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from otp_manager.models import OTPVar_Enum, SMS_Recievers, SMS_Template, SMSServiceTemplate_Enum
from otp_manager.service import send_sms
from timeTracker.models import TimeEntry, Sprint, Task
from django.db.models import Q
from django.db import connection

class Command(BaseCommand):
    help = 'ارسال پیامک یادآوری به کاربرانی که در 24 ساعت اخیر ساعت نزده‌اند و در اسپرینت فعال تسک دارند'

    def get_users_with_tasks_in_active_sprint(self):
        """
        دریافت کاربرانی که در آخرین اسپرینت فعال تسک دارند
        """
        active_sprint = Sprint.objects.filter(is_active=True).order_by('-start_date').first()
        
        if not active_sprint:
            self.stdout.write(self.style.WARNING('هیچ اسپرینت فعالی پیدا نشد'))
            return User.objects.none(), None
        
        self.stdout.write(f'اسپرینت فعال: {active_sprint.name}')
        
        tasks_in_sprint = Task.objects.filter(
            story__sprint=active_sprint,
            is_delete=False
        ).exclude(assigned_to__isnull=True)
        
        users_with_tasks = User.objects.filter(
            id__in=tasks_in_sprint.values_list('assigned_to_id', flat=True).distinct(),
            is_active=True
        )
        
        return users_with_tasks, active_sprint

    def get_user_full_name(self, user):
        """دریافت نام کامل کاربر"""
        try:
            if hasattr(user, 'profile'):
                first_name = user.profile.first_name if user.profile.first_name else user.first_name
                last_name = user.profile.last_name if user.profile.last_name else user.last_name
            else:
                first_name = user.first_name
                last_name = user.last_name
        except:
            first_name = user.first_name
            last_name = user.last_name
        
        # full_name = f'{first_name} {last_name}'.strip()
        full_name = f'{last_name}'.strip()
        return full_name if full_name else user.username

    def handle(self, *args, **options):
        now = timezone.now()
        last_24_hours = now - timedelta(hours=24)
        
        self.stdout.write(f'⏰ زمان فعلی: {now}')
        self.stdout.write(f'⏰ ۲۴ ساعت قبل: {last_24_hours}')
        
        # 1. دریافت کاربرانی که در اسپرینت فعال تسک دارند
        users_with_tasks, active_sprint = self.get_users_with_tasks_in_active_sprint()
        
        if not users_with_tasks.exists():
            self.stdout.write(self.style.WARNING('هیچ کاربری با تسک در اسپرینت فعال پیدا نشد'))
            return
        
        self.stdout.write(f'📊 تعداد کاربران دارای تسک در اسپرینت فعال: {users_with_tasks.count()}')
        
        # نمایش لیست کاربران دارای تسک برای دیباگ
        self.stdout.write('\n📋 لیست کاربران دارای تسک:')
        for user in users_with_tasks:
            self.stdout.write(f'  - {user.username} ({self.get_user_full_name(user)})')
        
        # 2. پیدا کردن کاربرانی که در 24 ساعت اخیر ساعت زده‌اند
        # روش اول: با فیلتر دقیق
        users_with_entry = TimeEntry.objects.filter(
            datetime__gte=last_24_hours,
            datetime__lte=now,
            user__in=users_with_tasks
        ).values_list('user_id', flat=True).distinct()
        
        # برای دیباگ: نمایش تمام TimeEntry های 24 ساعت اخیر
        all_entries_last_24 = TimeEntry.objects.filter(
            datetime__gte=last_24_hours,
            datetime__lte=now
        )
        
        self.stdout.write(f'\n📊 تعداد کل TimeEntry در ۲۴ ساعت اخیر: {all_entries_last_24.count()}')
        
        if all_entries_last_24.exists():
            self.stdout.write('📋 لیست TimeEntry های ۲۴ ساعت اخیر:')
            for entry in all_entries_last_24[:10]:  # فقط ۱۰ مورد اول
                self.stdout.write(
                    f'  - کاربر: {entry.user.username}, '
                    f'تسک: {entry.task.title}, '
                    f'ساعت: {entry.hours_spent}, '
                    f'زمان: {entry.datetime}'
                )
        
        # نمایش کاربرانی که ساعت زده‌اند
        users_with_entry_list = User.objects.filter(id__in=users_with_entry)
        self.stdout.write(f'\n📊 تعداد کاربرانی که در ۲۴ ساعت اخیر ساعت زده‌اند: {users_with_entry_list.count()}')
        
        if users_with_entry_list.exists():
            self.stdout.write('📋 لیست کاربرانی که ساعت زده‌اند:')
            for user in users_with_entry_list:
                self.stdout.write(f'  - {user.username} ({self.get_user_full_name(user)})')
        
        # 3. کاربرانی که تسک دارند ولی ساعت نزده‌اند
        users_without_entry = users_with_tasks.exclude(id__in=users_with_entry)
        
        self.stdout.write(f'\n📊 تعداد کاربرانی که ساعت نزده‌اند: {users_without_entry.count()}')
        
        if not users_without_entry.exists():
            self.stdout.write(self.style.SUCCESS('✅ همه کاربران دارای تسک، ساعت زده‌اند!'))
            return
        
        # ساخت لیست اسامی کاربران
        names_list = []
        for user in users_without_entry:
            full_name = self.get_user_full_name(user)
            names_list.append(full_name)
            
            # دیباگ: نمایش آخرین TimeEntry این کاربر
            last_entry = TimeEntry.objects.filter(user=user).order_by('-datetime').first()
            if last_entry:
                self.stdout.write(
                    f'  ⚠️ {user.username}: آخرین ساعت زده شده در {last_entry.datetime} '
                    f'(ساعت: {last_entry.hours_spent})'
                )
            else:
                self.stdout.write(f'  ⚠️ {user.username}: هیچ سابقه‌ای برای ساعت زدن ندارد')
        
        # ارسال پیامک
        names_text = ' - '.join(names_list)
        sprint_name = active_sprint.name if active_sprint else ''
        
        self.send_reminder_sms(
            text=names_text,
            count=len(names_list),
            sprint_name=sprint_name
        )
    
    def send_reminder_sms(self, text, count, sprint_name):
        try:
            sms_template = SMS_Template.objects.filter(
                name=SMSServiceTemplate_Enum.DAILY_NO_TASK
            ).first()
            
            if not sms_template:
                self.stdout.write(self.style.ERROR('تمپلیت پیامک پیدا نشد'))
                return
            
            receivers = SMS_Recievers.objects.filter(template=sms_template)
            
            if not receivers.exists():
                self.stdout.write(self.style.WARNING('هیچ گیرنده‌ای برای این تمپلیت تعریف نشده'))
                return
            
            message_text = f"""
            اسپرینت: {sprint_name}
            تعداد کاربرانی که ساعت نزده‌اند: {count} نفر
            اسامی: {text}
            """
            
            for receiver in receivers:
                try:
                    ret = send_sms(
                        sms_template,
                        phone_number=receiver.persons.phone,
                        vars={OTPVar_Enum.COUNT:count,OTPVar_Enum.NAMES:text,}
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'✅ پیامک برای {receiver.persons.phone} ارسال شد'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ خطا در ارسال پیامک برای {receiver.persons.phone}: {str(e)}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا در ارسال پیامک: {str(e)}'))