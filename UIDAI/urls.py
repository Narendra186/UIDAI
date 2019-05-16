from django.contrib import admin
from django.urls import path,include
from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('update/',include("update.urls")),
    path('aadharcard/',include("aadharcard.urls")),
    url(r'^captcha/', include('captcha.urls')),
    path('nearest_centre/',views.nearest_centre,name = 'nearest_centre'),
    path('',views.uidai_home,name = 'uidai_home')
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
