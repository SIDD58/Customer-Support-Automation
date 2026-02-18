import time
import redis.asyncio as redis
from fastapi import Request, HTTPException
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file
redis_cache_url=os.getenv("REDIS_CACHE_URL", "redis://localhost:6380/0")


# Connect to your cache Redis (Port 6380)
# This is "outside" the class so it's only created once when the app starts
redis_cache = redis.from_url(redis_cache_url, decode_responses=True)

class RateLimiter:
    def __init__(self, times: int, seconds: int):
        # it defined how many time a user can make a request in a specific time window (seconds)
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        # 1. Identify the user
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        now = time.time()
        # when was the time started 
        window_start = now - self.seconds

        # 2. Run all the Redis commands as a batch (Send multiple commands at once )
        async with redis_cache.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start) # Clean the old requests outside the window from the sorted set
            pipe.zcard(key)                             # Count the number of requests in the current window
            pipe.zadd(key, {str(now): now})             # Add the new request with the current timestamp as both the score and the value
            pipe.expire(key, self.seconds)              # Set expiration to automatically clean up the key after the window has passed
            results = await pipe.execute()
        
        # 3. Check the count (the answer to zcard is at index 1)
        request_count = results[1]
        
        if request_count >= self.times:
            raise HTTPException(
                status_code=429, 
                detail="Too many requests. Slow down!"
            )