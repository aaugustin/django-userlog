import json
import time

from django.contrib.auth import get_user_model

from .util import get_redis_client, get_userlog_settings

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class UserLogMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        if not (hasattr(request, 'user') and request.user.is_authenticated()):
            return response

        options = get_userlog_settings()

        for pattern in options.ignore_urls:
            if pattern.search(request.path):
                return response

        log = self.get_log(request, response)
        raw_log = json.dumps(log).encode()
        log_key = 'log:{}'.format(request.user.get_username())
        channel = 'userlog:{}'.format(log_key)

        redis = get_redis_client()
        pipe = redis.pipeline()
        pipe.lpush(log_key, raw_log)
        pipe.ltrim(log_key, 0, options.max_size)
        pipe.expire(log_key, options.timeout)
        if options.publish:
            pipe.publish(channel, raw_log)
        pipe.execute()

        return response

    def get_log(self, request, response):
        """
        Return a dict of data to log for a given request and response.

        Override this method if you need to log a different set of values.
        """
        return {
            'method': request.method,
            'path': request.get_full_path(),
            'code': response.status_code,
            'time': time.time(),
        }


class AdminAutoLoginMiddleware(MiddlewareMixin):
    """
    Automatically creates and logs in an "admin" user.

    Replaces ``django.contrib.auth.middleware.AuthenticationMiddleware``.

    Works with any admin-compliant user model i.e. subclass of AbstractUser.

    Designed for personal applications that only exist on your own computer.

    Used in the tests.
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
