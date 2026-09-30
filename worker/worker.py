import os
import time

import psycopg
import redis

r = redis.Redis.from_url(
    os.environ["REDIS_URL"],
    decode_responses=True,
    socket_timeout=30,  # must be longer than the brpop timeout below
)

while True:
    try:
        item = r.brpop("clicks", timeout=5)
        if item:
            with psycopg.connect(os.environ["DATABASE_URL"]) as c:
                c.execute(
                    "UPDATE links SET clicks = clicks + 1 WHERE code = %s",
                    (item[1],),
                )
    except (redis.exceptions.RedisError, psycopg.Error) as e:
        print(f"worker error, retrying in 2s: {e}", flush=True)
        time.sleep(2)