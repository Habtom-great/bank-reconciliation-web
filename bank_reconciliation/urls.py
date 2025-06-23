"""
URL configuration for bank_reconciliation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import RedirectView
from bank_recon import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_bank_statement, name='upload_bank_statement'),
    path('', RedirectView.as_view(url='/transactions/', permanent=False)),
    path('upload-bank-statement/', views.upload_bank_statement, name='upload_bank_statement'),
    path('transactions/', include('bank_recon.urls')),
    path('', include('bank_recon.urls')),  # ✅ This line must be here
]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
