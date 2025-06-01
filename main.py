from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()

# Setup static and templates directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "kv_store.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

init_db()

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
