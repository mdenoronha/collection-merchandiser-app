import os

import redis
from rq import Worker, Queue, Connection


listen = ['high', 'default', 'low'] # while scheduling the task in views.py we sent it to default

redis_url = os.getenv('REDISTOGO_URL', 'redis://redistogo:b8b8ce0e7548ee29c447d4d8eb84c63a@porgy.redistogo.com:11667/')
print("Redis URL", redis_url)

conn = redis.from_url(redis_url)


if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
