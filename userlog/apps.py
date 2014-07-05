from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UserLogConfig(AppConfig):
    name = 'userlog'
    verbose_name = _("User logs")
