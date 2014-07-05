from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.http import last_modified
from django.views.i18n import javascript_catalog

from userlog.util import get_log, get_token


last_modified_date = timezone.now()


@last_modified(lambda req, **kw: last_modified_date)
def js18n(request):
    return javascript_catalog(request, 'djangojs', ['example'])


@user_passes_test(lambda user: user.is_superuser)
def bigbrother(request):
    return render(request, 'userlog/live.html', {
        'title': _("Live user logs"),
        'token': get_token('*'),
    })


@user_passes_test(lambda user: user.is_superuser)
def live(request):
    User = get_user_model()
    username_field = User.USERNAME_FIELD

    token = None

    username = request.GET.get('username')
    if username:
        try:
            User.objects.get(**{username_field: username})
        except User.DoesNotExist:
            messages.error(request, _("User {} not found.").format(username))
        else:
            token = get_token(username)
            messages.info(request, _("Logs found for {}.").format(username))

    return render(request, 'userlog/live.html', {
        'title': _("Live user logs"),
        'token': token,
        'fieldname': User._meta.get_field(username_field).verbose_name,
    })


@user_passes_test(lambda user: user.is_superuser)
def static(request):
    User = get_user_model()
    username_field = User.USERNAME_FIELD

    log = None

    username = request.GET.get('username')
    if username:
        try:
            User.objects.get(**{username_field: username})
        except User.DoesNotExist:
            messages.error(request, _("User {} not found.").format(username))
        else:
            log = get_log(username)
            if log:
                messages.info(request, _("Logs found for {}.").format(username))    # noqa
            else:
                messages.warning(request, _("No logs for {}.").format(username))    # noqa

    return render(request, 'userlog/static.html', {
        'title': _("Static user logs"),
        'log': log,
        'fieldname': User._meta.get_field(username_field).verbose_name,
    })
