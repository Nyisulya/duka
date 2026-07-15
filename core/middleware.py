from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Duka

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.duka = None
        
        # 1. Mbinu ya 1: Kugundua kupitia Subdomain (mfano: sabuni.duka.nyisu.com au sabuni.localhost:8000)
        host = request.get_host().split(':')[0].lower()  # Ondoa port na uweke herufi ndogo
        
        from django.conf import settings
        primary_domain = getattr(settings, 'PRIMARY_DOMAIN', 'localhost').lower()
        
        # Angalia kama host inaisha na subdomain ya primary domain
        if host.endswith('.' + primary_domain):
            subdomain = host[:-len('.' + primary_domain)]
            subdomain = subdomain.split('.')[-1]  # Pata subdomain ya kwanza (mfano: sabuni)
            
            if subdomain not in ['www', 'localhost', '127']:
                try:
                    request.duka = Duka.objects.get(slug=subdomain)
                except Duka.DoesNotExist:
                    pass
                
        # 2. Mbinu ya 2: Kugundua kupitia Slug ya URL (mfano: /store/sabuni/)
        if not request.duka:
            path_info = request.path_info.strip('/')
            path_parts = path_info.split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'store':
                slug = path_parts[1]
                try:
                    request.duka = Duka.objects.get(slug=slug)
                except Duka.DoesNotExist:
                    raise Http404("Samahani! Duka hili halipo katika mfumo wetu.")

        response = self.get_response(request)
        return response
