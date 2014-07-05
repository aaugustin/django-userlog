from django.contrib.auth import get_user_model


class AdminAutoLoginMiddleware:
    """
    Automatically creates and logs in an "admin" user.

    Replaces ``django.contrib.auth.middleware.AuthenticationMiddleware``.

    Works with any admin-compliant user model i.e. subclass of AbstractUser.

    Designed for personal applications that only exist on your own computer.
    """

    USERNAME = 'admin'

    def process_request(self, request):
        User = get_user_model()
        username_condition = {User.USERNAME_FIELD: self.USERNAME}
        try:
            user = User.objects.get(**username_condition)
        except User.DoesNotExist:
            user = User(**username_condition)
            user.is_staff = True
            user.is_superuser = True
            user.set_unusable_password()
            user.save()
        request.user = user
