import redis
import json
from .cache import AbstractCacheStore

class RedisCache(AbstractCacheStore):
    def __init__(self, url='redis://localhost:6379', db=0, password=None):
        """
        Initialize the RedisCache class.

        Args:
            url (str, optional): The URL of the Redis server.
            db (int, optional): The database number.
            password (str, optional): The password to authenticate with the server.
        """
        self.r = redis.Redis.from_url(url, db=db, password=password)
        

    def set(self, key, value, expires=None):
        """
        Store a value in the cache.

        Args:
            key (str): The key under which to store the value.
            value: The value to store.
            expires (int, optional): Expiration time in seconds.
        """
        value = json.dumps(value)  # Serialize the value to a JSON string
        if expires:
            self.r.setex(key, expires, value)
        else:
            self.r.set(key, value)

    def get(self, key):
        """
        Retrieve a value from the cache.

        Args:
            key (str): The key of the value to retrieve.

        Returns:
            The value or None if the key does not exist.
        """
        result = self.r.get(key)
        if result:
            return json.loads(result)  # Deserialize the JSON back to Python object
        return None

    def delete(self, key):
        """
        Delete a value from the cache.

        Args:
            key (str): The key of the value to delete.
        """
        self.r.delete(key)
