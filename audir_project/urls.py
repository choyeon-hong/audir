from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from audir.views import CustomPasswordChangeView


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('audir.urls')),
    path('accounts/password/change/', CustomPasswordChangeView.as_view(), name='account_password_change'),
    path('accounts/', include('allauth.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
