import asyncio
import json
import logging

import asyncio_redis
import websockets

from django.conf import settings


if settings.DEBUG:
    logger = logging.getLogger('websockets.server')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


@asyncio.coroutine
def redis_connection():
    userlog = settings.CACHES['userlog']
    options = userlog.get('OPTIONS', {})
    host, port = userlog['LOCATION'].rsplit(':', 1)
    port = int(port)
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
                if not websocket.open:
                    break
                data = json.loads(reply.value)
                data['username'] = reply.channel.rpartition(':')[2]
                yield from websocket.send(json.dumps(data))

        else:                           # logs for a single user
            # Send backlock
            log = yield from redis.lrange(log_key, 0, -1)
            for item in reversed(list(log)):
                item = yield from item
                yield from websocket.send(item)

            # Stream new lines
            subscriber = yield from redis.start_subscribe()
            yield from subscriber.subscribe([channel])
            while True:
                reply = yield from subscriber.next_published()
                if not websocket.open:
                    break
                yield from websocket.send(reply.value)

    finally:
        redis.close()


if __name__ == '__main__':
    start_server = websockets.serve(userlog, 'localhost', 8080)
    asyncio.get_event_loop().run_until_complete(start_server)
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
