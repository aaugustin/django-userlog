import json
import time

from .util import get_redis_client, get_userlog_settings


class UserLogMiddleware:

    def process_response(self, request, response):
        if not request.user.is_authenticated():
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
