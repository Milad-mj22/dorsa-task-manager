
from django.http import JsonResponse
from django.templatetags.static import static

from Constatns import Constants

def manifest(request):
    data = {
        "name": Constants.PWA_NAME,
        "short_name": Constants.PWA_NAME,
        "description": Constants.PWA_DESCRIPTION,
        "start_url": "/",
        "display": "standalone",
        "background_color": "#e379fd",
        "theme_color": "#0A0A0A",
        "icons": [
            {
                "src": static(Constants.LOGO_PATH),
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": static(Constants.LOGO_PATH),
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(data)