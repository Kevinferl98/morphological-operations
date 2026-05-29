import json
import redis
from app.config import config

class RedisClient:
    def __init__(self, redis_instance=None):
        self.redis = redis_instance or redis.Redis.from_url(config.REDIS_URL)

    def create_job(self, job_key, job_data, ttl_seconds=3600):
        self.redis.set(job_key, json.dumps(job_data), ex=ttl_seconds)

    def get_job(self, job_key):
        return self.redis.get(job_key)