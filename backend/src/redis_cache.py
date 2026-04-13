import redis

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def set(self, key, value, expire=None):
        self.client.set(key, value, ex=expire)

    def get(self, key):
        return self.client.get(key)

    def delete(self, key):
        self.client.delete(key)

    def exists(self, key):
        return self.client.exists(key) == 1

    def flush(self):
        self.client.flushdb()

cache = RedisCache()