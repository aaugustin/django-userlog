from django.conf.urls import include, url
from django.contrib import admin

from .views import search


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', search, name='search'),
]
