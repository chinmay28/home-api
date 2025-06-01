from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import time
from datetime import datetime
from collections import defaultdict

app = FastAPI()

# Setup static and templates directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    return ' '.join(parts) + " ago"

templates.env.filters["datetime_human"] = datetime_human

DB_PATH = "kv_store.db"
request_counts = defaultdict(int)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                host TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)", ('stats_start_time', str(int(time.time()))))

init_db()

@app.middleware("http")
async def track_requests(request: Request, call_next):
    host = request.client.host
    request_counts[host] += 1
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO stats (host, count) VALUES (?, 1) ON CONFLICT(host) DO UPDATE SET count = count + 1", (host,))
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value FROM kv").fetchall()
    return templates.TemplateResponse("form.html", {"request": request, "data": rows})

@app.post("/submit")
async def submit_form(key: str = Form(...), value: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value))
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete")
async def delete_form(key: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM kv WHERE key = ?", (key,))
    return RedirectResponse(url="/", status_code=303)

@app.get("/search", response_class=JSONResponse)
async def search_values(q: str = ""):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value FROM kv WHERE key LIKE ? OR value LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
    return rows

@app.get("/api/{key}")
async def get_value(key: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        if row:
            return {"key": key, "value": row[0]}
        raise HTTPException(status_code=404, detail="Key not found")

@app.post("/api/{key}")
async def set_value(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value))
    return {"key": key, "value": value}

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
        hosts = conn.execute("SELECT host, count FROM stats ORDER BY count DESC").fetchall()
        start_time_row = conn.execute("SELECT value FROM metadata WHERE key = 'stats_start_time'").fetchone()
        stats_since = int(start_time_row[0]) if start_time_row else int(time.time())
    uptime_seconds = int(time.time() - stats_since)
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "hosts": hosts,
        "uptime": uptime_seconds,
        "since": stats_since
    })
