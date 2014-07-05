from django.conf.urls import include, url
from django.contrib import admin

from .views import live, static


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^userlog/live/', live, name='live-userlog'),
    url(r'^userlog/static/', static, name='static-userlog'),
]
