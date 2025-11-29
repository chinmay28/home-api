from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import time
import json
from datetime import datetime
from collections import defaultdict

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def datetime_format(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

templates.env.filters["datetime"] = datetime_format

def datetime_human(timestamp):
    delta = int(time.time() - timestamp)
    days, rem = divmod(delta, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    return ' '.join(parts)

templates.env.filters["datetime_human"] = datetime_human

DB_PATH = "kv_store.db"
request_counts = defaultdict(int)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                host TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
        """)

init_db()

@app.middleware("http")
async def track_requests(request: Request, call_next):
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value, updated FROM kv").fetchall()
    return templates.TemplateResponse("form.html", {"request": request, "data": rows})

@app.post("/submit")
async def submit_form(request: Request):
    form = await request.form()
    key = form.get("key")
    value = form.get("value")
    host = request.client.host
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("REPLACE INTO kv (key, value, updated) VALUES (?, ?, strftime('%s','now'))", (key, value))
        conn.execute(
            "INSERT INTO stats (host, count) VALUES (?, 1) "
            "ON CONFLICT(host) DO UPDATE SET count = count + 1",
            (host,)
        )
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete")
async def delete_form(key: str = Request):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM kv WHERE key = ?", (key,))
    return RedirectResponse(url="/", status_code=303)

@app.get("/search", response_class=JSONResponse)
async def search_values(q: str = "", request: Request = None):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value, updated FROM kv WHERE key LIKE ? OR value LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
    return rows

@app.get("/api/{key}")
async def get_value(key: str, request: Request):
    host = request.client.host
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        if row:
            conn.execute(
                "INSERT INTO stats (host, count) VALUES (?, 1) "
                "ON CONFLICT(host) DO UPDATE SET count = count + 1",
                (host,)
            )
            return {"key": key, "value": row[0]}
        raise HTTPException(status_code=404, detail="Key not found")

class KVBody(BaseModel):
    value: dict

@app.post("/api/{key}")
async def set_value(key: str, payload: KVBody, request: Request):
    host = request.client.host
    value_str = json.dumps(payload.value)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("REPLACE INTO kv (key, value, updated) VALUES (?, ?, strftime('%s','now'))", (key, value_str))
        conn.execute(
            "INSERT INTO stats (host, count) VALUES (?, 1) "
            "ON CONFLICT(host) DO UPDATE SET count = count + 1",
            (host,)
        )
    return {"key": key, "value": payload.value}

@app.delete("/api/{key}")
async def delete_value(key: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM kv WHERE key = ?", (key,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Key not found")
    return {"message": "Deleted"}

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT host, count FROM stats ORDER BY count DESC").fetchall()
        result = conn.execute("SELECT MIN(updated) FROM kv").fetchone()
        tracking_since = result[0] if result and result[0] else int(time.time())
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "stats": rows,
        "since": tracking_since
    })
