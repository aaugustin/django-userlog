from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render

from userlog.util import get_log


@user_passes_test(lambda user: user.is_superuser)
def search(request):
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

    return render(request, 'userlog/search.html', {
        'title': "Search user logs",
        'log': log,
        'username_field': username_field,
    })
