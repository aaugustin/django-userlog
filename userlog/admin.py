"""Steaming pile of hacks. Read at your own risks."""

from django.conf.urls import url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .views import bigbrother, jsi18n, live, static


class _meta:
    abstract = None
    app_label = 'userlog'
    swapped = None


class LiveUserLogModel:

    class _meta(_meta):
        object_name = 'live'
        model_name = 'live'
        verbose_name = _("Live log")
        verbose_name_plural = _("Live logs")


class LiveUserLogModelAdmin(admin.ModelAdmin):

    def get_urls(self):
        av = self.admin_site.admin_view
        return [
            url(r'^$', av(live), name='userlog_live'),
            # Integrates into the admin index and app index.
            url(r'^$', av(live), name='userlog_live_changelist'),
            # Easter egg.
            url(r'^bigbrother/', av(bigbrother), name='userlog_bigbrother'),
        ]


admin.site.register([LiveUserLogModel], LiveUserLogModelAdmin)


class StaticUserLogModel:

    class _meta(_meta):
        object_name = 'static'
        model_name = 'static'
        verbose_name = _("Static log")
        verbose_name_plural = _("Static logs")


class StaticUserLogModelAdmin(admin.ModelAdmin):

    def get_urls(self):
        av = self.admin_site.admin_view
        return [
            url(r'^$', av(static), name='userlog_static'),
            # Integrates into the admin index and app index.
            url(r'^$', av(static), name='userlog_static_changelist'),
            # This needs to live somewhere.
            url(r'^jsi18n/$', av(jsi18n), name='userlog_jsi18n'),
        ]


admin.site.register([StaticUserLogModel], StaticUserLogModelAdmin)
