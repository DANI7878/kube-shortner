import os, random, string
from contextlib import asynccontextmanager

import psycopg, redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

def db():
    return psycopg.connect(os.environ["DATABASE_URL"])

@asynccontextmanager
async def lifespan(app):
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY, url TEXT NOT NULL,
            clicks INT NOT NULL DEFAULT 0)""")
    yield

app = FastAPI(lifespan=lifespan)

class Link(BaseModel):
    url: str

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/shorten")
def shorten(link: Link):
    code = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    with db() as c:
        c.execute("INSERT INTO links (code, url) VALUES (%s, %s)", (code, link.url))
    return {"code": code}

@app.get("/stats/{code}")
def stats(code: str):
    with db() as c:
        row = c.execute("SELECT url, clicks FROM links WHERE code=%s", (code,)).fetchone()
    if not row:
        raise HTTPException(404)
    return {"url": row[0], "clicks": row[1]}

@app.get("/{code}")
def go(code: str):
    with db() as c:
        row = c.execute("SELECT url FROM links WHERE code=%s", (code,)).fetchone()
    if not row:
        raise HTTPException(404)
    r.lpush("clicks", code)
    return RedirectResponse(row[0])