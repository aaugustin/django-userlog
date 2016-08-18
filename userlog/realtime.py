import asyncio
import json
import logging

import asyncio_redis
import django
import websockets
from django.conf import settings

from .util import get_userlog_settings

if settings.DEBUG:                                          # pragma: no cover
    logger = logging.getLogger('websockets.server')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


@asyncio.coroutine
def redis_connection():
    userlog = settings.CACHES['userlog']
    options = userlog.get('OPTIONS', {})
    if ':' in userlog['LOCATION']:
        host, port = userlog['LOCATION'].rsplit(':', 1)
        port = int(port)
    else:
        host = userlog['LOCATION']
        port = 0
    db = options.get('DB', 1)
    password = options.get('PASSWORD', None)
    redis = yield from asyncio_redis.Connection.create(
        host=host, port=port, password=password, db=db)
    return redis


@asyncio.coroutine
def userlog(websocket, uri):
    token = yield from websocket.recv()

    redis = yield from redis_connection()

    token_key = 'token:{}'.format(token)

    # Access control
    username = yield from redis.get(token_key)
    if username is None:
        return

    log_key = 'log:{}'.format(username)
    channel = 'userlog:{}'.format(log_key)

    try:
        if channel.endswith('*'):       # logs for several users
            # Stream new lines
            subscriber = yield from redis.start_subscribe()
            yield from subscriber.psubscribe([channel])
            while True:
                reply = yield from subscriber.next_published()
                data = json.loads(reply.value)
                data['username'] = reply.channel.rpartition(':')[2]
                line = json.dumps(data)
                try:
                    yield from websocket.send(line)
                except websockets.ConnectionClosed:
                    return

        else:                           # logs for a single user
            # Send backlock
            log = yield from redis.lrange(log_key, 0, -1)
            for item in reversed(list(log)):
                line = yield from item
                try:
                    yield from websocket.send(line)
                except websockets.ConnectionClosed:
                    return

            # Stream new lines
            subscriber = yield from redis.start_subscribe()
            yield from subscriber.subscribe([channel])
            while True:
                reply = yield from subscriber.next_published()
                line = reply.value
                try:
                    yield from websocket.send(line)
                except websockets.ConnectionClosed:
                    return

    finally:
        redis.close()
        # Loop one more time to complete the cancellation of redis._reader_f,
        # which runs redis._reader_coroutine(), after redis.connection_lost().
        yield from asyncio.sleep(0)


if __name__ == '__main__':                                  # pragma: no cover
    django.setup()

    uri = websockets.parse_uri(get_userlog_settings().websocket_address)
    if uri.secure:
        raise ValueError("SSL support requires explicit configuration")
    start_server = websockets.serve(userlog, uri.host, uri.port)
    asyncio.get_event_loop().run_until_complete(start_server)

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
