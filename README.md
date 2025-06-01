# 🏠 Home API

A lightweight FastAPI-based key-value store with a REST API, web UI, live search, edit/delete functionality, and a stats dashboard.

---

## 🚀 Features

- Web UI for adding/updating key-value pairs
- Live search, delete, and edit support
- Statistics page showing:
  - Client request counts by IP
  - Uptime
- SQLite for persistent backend
- RESTful API access

---

## 📦 Installation

```bash
pip install fastapi uvicorn jinja2
```

---

## 🧪 Running the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then visit:

- Web UI: http://localhost:8000/
- Stats Page: http://localhost:8000/stats

---

## 📡 REST API Endpoints

| Method | Endpoint         | Description             |
|--------|------------------|-------------------------|
| GET    | `/api/{key}`     | Retrieve a value by key |
| POST   | `/api/{key}`     | Set value for a key     |
| DELETE | `/api/{key}`     | Delete a key            |
| GET    | `/search?q=...`  | Search key/value pairs  |

### 🧪 Examples using curl

```bash
# Set value
curl -X POST "http://localhost:8000/api/greeting" -d "value=hello"

# Get value
curl http://localhost:8000/api/greeting

# Delete key
curl -X DELETE http://localhost:8000/api/greeting

# Search
curl "http://localhost:8000/search?q=greet"
```

---

## 📷 Screenshots

### Web UI
![Web UI](https://via.placeholder.com/800x400.png?text=Home+API+Web+UI)

### Stats Page
![Stats Page](https://via.placeholder.com/800x300.png?text=Home+API+Stats)

---

## 📁 Project Structure

```
.
├── main.py               # FastAPI app
├── static/
│   └── style.css         # UI styling
└── templates/
    ├── form.html         # Key-value UI
    └── stats.html        # Statistics page
```

---

## 📝 License

MIT – use freely and modify as needed.
