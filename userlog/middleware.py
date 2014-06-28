import json

from .util import get_redis_client, get_userlog_settings


class UserLogMiddleware(object):

    def process_response(self, request, response):
        if not request.user.is_authenticated():
            return response

        redis = get_redis_client()
        options = get_userlog_settings()

        log = self.get_log(request, response)
        log_key = 'log:{}'.format(request.user.get_username())

        pipe = redis.pipeline()
        pipe.lpush(log_key, json.dumps(log))
        pipe.ltrim(log_key, 0, options.max_size)
        pipe.expire(log_key, options.timeout)
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
        }
