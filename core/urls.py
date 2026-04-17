# core/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404, HttpResponse
import os

def serve_media_files(request, path):
    """Serve media files directly"""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
    raise Http404("File not found")

def home_view(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Diploma Project</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h1>Welcome to Diploma Project</h1>
        <p>Your E-commerce Assistant</p>
        <a href="/admin/" style="display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Admin Panel</a>
        <a href="/chatbot/" style="display: inline-block; margin: 10px; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">Chatbot</a>
    </body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('api/', include('api.urls')), 
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('chatbot/', include('chatbot.urls')),
    path('media/<path:path>', serve_media_files, name='serve_media'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)