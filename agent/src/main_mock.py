import redis
import json
import os
import time

# Getting env vars, otherwise default to localhost and default list
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
REDIS_QUEUE_NAME = os.environ.get('REDIS_QUEUE_NAME', 'queue:ai_tasks')

try:
    r = redis.from_url(REDIS_URL, decode_responses = True)
    r.ping()
    print(f"Connected to Redis on: {REDIS_URL}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    exit(1)

def worker():

    while True:
        try:
            result = r.brpop(REDIS_QUEUE_NAME, timeout=0)

            if result: 
                _, message = result
                data = json.loads(message)

                print(f"Received: {data}")

        except Exception as e:
            print(f"Error reading: {e}")
            time.sleep(2)

        
if __name__ == "__main__":
    worker()