from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render

from userlog.util import get_log, get_token


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
            messages.error(request, "User {} not found.".format(username))
        else:
            token = get_token(username)
            messages.info(request, "Streaming logs for {}.".format(username))

    return render(request, 'userlog/live.html', {
        'title': "Live user logs",
        'token': token,
        'username_field': username_field,
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
            messages.error(request, "User {} not found.".format(username))
        else:
            log = get_log(username)
            if log:
                messages.info(request, "Logs found for {}.".format(username))
            else:
                messages.warning(request, "No logs for {}.".format(username))

    return render(request, 'userlog/static.html', {
        'title': "Static user logs",
        'log': log,
        'username_field': username_field,
    })
