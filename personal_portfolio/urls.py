"""
URL configuration for personal_portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.urls import path, include
from django.conf import settings
from main.views import handler404, handler500
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main.urls")),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]
# Always serve media files for development
# Note: In a real production environment, media files should be served by a web server like Nginx or Apache
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configure custom error handlers
handler404 = 'main.views.handler404'
handler500 = 'main.views.handler500'
