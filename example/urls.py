from django.conf.urls import include, url
from django.contrib import admin

from .views import js18n, live, static


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^userlog/jsi18n/$', js18n, name='js18n-userlog'),
    url(r'^userlog/live/', live, name='live-userlog'),
    url(r'^userlog/static/', static, name='static-userlog'),
]
