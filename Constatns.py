
class Base:
    class Name:

        seke = 'seke'
        moallem = 'moallem'
        dorsa = 'dorsa'
        kaman = 'kaman'

    name = Name.dorsa

class Constants:
    if Base.name == Base.Name.seke:
        NAME = 'سکه طلا'
        PWA_NAME = 'مدیریت سکه طلا'
        PWA_DESCRIPTION = 'مدیریت انبار و دستیار هوشمند سکه طلا'
        PWA_COLOR = "#FFD900"
        PWA_BACKGROUND_COLOR = '#FFFFFF'
        LOGO_PATH = 'icons/logo.gif'
        LOGIN_LOGO_PATH = 'icons/logo.png'
        ALT_LOGO = 'لوگوی سکه طلا'
        LOGIN_BANNER = 'images/hero1.png'
        TOPBAR_COLOR_START = '#cab331'
        TOPBAR_COLOR_END = '#63635a'

    
    elif Base.name == Base.Name.moallem:
        NAME = 'خانه معلم'
        PWA_NAME = 'مدیریت خانه معلم'
        PWA_DESCRIPTION = 'مدیریت انبار و دستیار هوشمند خانه معلم'
        PWA_COLOR = "#2723FC"
        PWA_BACKGROUND_COLOR = "#74B0FF"
        LOGO_PATH = 'icons/moallem_logo.png'
        LOGIN_LOGO_PATH = 'icons/moallem_logo.png'
        ALT_LOGO = 'لوگوی خانه معلم'
        LOGIN_BANNER = 'images/banner.png'
        TOPBAR_COLOR_START = '#cab331'
        TOPBAR_COLOR_END = '#63635a'

    elif Base.name == Base.Name.dorsa:
        NAME = 'شرکت درصا'
        PWA_NAME = 'مدیریت شرکت درصا'
        PWA_DESCRIPTION = 'مدیریت زمانی و نیروهای هوشمند شرکت درصا'
        PWA_COLOR = "#2723FC"
        PWA_BACKGROUND_COLOR = "#74B0FF"
        LOGO_PATH = 'icons/dorsa_logo.png'
        LOGIN_LOGO_PATH = 'icons/d_logo.png'
        ALT_LOGO = 'لوگوی شرکت درصا'
        LOGIN_BANNER = 'images/dorsa_timing.png'
        TOPBAR_COLOR_START = "#2D5BF1"
        TOPBAR_COLOR_END = "#151e46"     
           


    elif Base.name == Base.Name.kaman:
        NAME = 'شرکت کمان'
        PWA_NAME = 'مدیریت مشتریان کمان'
        PWA_DESCRIPTION = 'مدیریت  مشتریان و محصولات کمان'
        PWA_COLOR = "#CD21F0"
        PWA_BACKGROUND_COLOR = "#D049F1"
        LOGO_PATH = 'icons/kamannew.png'
        LOGIN_LOGO_PATH = 'icons/kamannew.png'
        ALT_LOGO = 'لوگوی خانه معلم'
        LOGIN_BANNER = 'images/kamannew.png'
        TOPBAR_COLOR_START = "#9b4fff"
        TOPBAR_COLOR_END = "#d581ee"