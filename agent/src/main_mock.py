import redis
import json
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

# Getting env vars, otherwise default to localhost and default list
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
REDIS_QUEUE_NAME = os.environ.get('REDIS_QUEUE_NAME', 'queue:ai_tasks')
REDIS_CHANNEL_NAME = os.environ.get('REDIS_CHANNEL_NAME', 'channel:task_updates')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/dbname')

try:
    r = redis.from_url(REDIS_URL, decode_responses = True)
    r.ping()
    print(f"Connected to Redis on: {REDIS_URL}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    exit(1)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def worker():

    while True:
        try:
            result = r.brpop(REDIS_QUEUE_NAME, timeout=5)

            if result: 
                _, message = result
                data = json.loads(message)

                print(f"Received: {data}")
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        insert_query = "INSERT INTO ai_tasks_results (raw_payload) VALUES (%s) RETURNING id;"
                        cur.execute(insert_query, (json.dumps(data),))
                        new_id = cur.fetchone()[0]
                        conn.commit()

                r.publish(REDIS_CHANNEL_NAME, json.dumps({"db_id": str(new_id), "status": "updated"}))

                print(f"Task {new_id} complete.")

        except Exception as e:
            print(f"Error reading: {e}")
            time.sleep(2)

        
if __name__ == "__main__":
    worker()