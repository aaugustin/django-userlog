from .example_settings import *  # noqa

CACHES['userlog']['LOCATION'] = os.path.join(BASE_DIR, 'redis.sock')  # noqa
