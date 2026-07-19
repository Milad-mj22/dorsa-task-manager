
from Constatns import Constants
from users.models import MenuItem, UserRole, jobs



def menu_items_processor(request):
   
    SITE_LOGO = Constants.LOGO_PATH
    SITE_NAME = Constants.NAME
    PWA_DESCRIPTION = Constants.PWA_DESCRIPTION
    TOPBAR_COLOR_START = Constants.TOPBAR_COLOR_START
    TOPBAR_COLOR_END = Constants.TOPBAR_COLOR_END


   
    try:
        user = request.user
        if not user.is_authenticated:
            return {'menu_items': [] , 'SITE_LOGO':SITE_LOGO,'SITE_NAME':SITE_NAME , 'PWA_DESCRIPTION':PWA_DESCRIPTION,'TOPBAR_COLOR_START':TOPBAR_COLOR_START,'TOPBAR_COLOR_END':TOPBAR_COLOR_END}    


        # گرفتن نقش‌های کاربر
        roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)

        # job = jobs.objects.filter(name=user.profile.).first()
    # 
        job = user.profile.job_position.name

        items = user.profile.job_position.items.filter(show=True).order_by('order')

        # To efficiently fetch related submenus of these items (assuming submenus is a related_name)
        items = items.prefetch_related('submenus')


        # گرفتن آیتم‌های منو مرتبط با نقش‌ها
        # items = MenuItem.objects.filter(roles__id__in=roles).distinct().order_by('order')

        return {'menu_items': items , 'SITE_LOGO':SITE_LOGO,'SITE_NAME':SITE_NAME , 'PWA_DESCRIPTION':PWA_DESCRIPTION,'TOPBAR_COLOR_START':TOPBAR_COLOR_START,'TOPBAR_COLOR_END':TOPBAR_COLOR_END}    
    
    except:
        return {'menu_items': None , 'SITE_LOGO':SITE_LOGO,'SITE_NAME':SITE_NAME , 'PWA_DESCRIPTION':PWA_DESCRIPTION,'TOPBAR_COLOR_START':TOPBAR_COLOR_START,'TOPBAR_COLOR_END':TOPBAR_COLOR_END}    

