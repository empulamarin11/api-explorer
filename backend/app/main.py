from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os

# ---------- Conexión a MongoDB ----------
client = MongoClient(
    host=os.getenv("MONGO_HOST"),
    port=int(os.getenv("MONGO_PORT")),
    username=os.getenv("MONGO_USER"),
    password=os.getenv("MONGO_PASS"),
    authSource=os.getenv("MONGO_DB")
)
db = client[os.getenv("MONGO_DB")]
users_collection = db["users"]
searches_collection = db["searches"]

# ---------- Modelos ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class SearchRequest(BaseModel):
    title: str

# ---------- FastAPI app ----------
app = FastAPI(title="API Explorer – Books + MongoDB", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend conectado a MongoDB 🎉"}

# ---------- Login (guarda en BD) ----------
@app.post("/login")
def login(data: LoginRequest):
    if data.username != "admin" or data.password != "admin":
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    user = {"username": data.username, "loggedAt": datetime.utcnow()}
    users_collection.insert_one(user)
    return {"message": "Login exitoso", "userId": str(user["_id"])}

# ---------- Búsqueda de libro + guardado ----------
@app.post("/search")
async def search_book(data: SearchRequest):
    # Llamar a Google Books API
    import httpx
    url = f"https://www.googleapis.com/books/v1/volumes?q={data.title}&maxResults=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        data_api = resp.json()
        if not data_api.get("items"):
            raise HTTPException(status_code=404, detail="Sin resultados")

    info = data_api["items"][0]["volumeInfo"]
    description = info.get("description", "Sin descripción")
    book = {
        "title": info.get("title", "Sin título"),
        "authors": info.get("authors", ["Anónimo"]),
        "image": info.get("imageLinks", {}).get("thumbnail", "").replace("http://", "https://"),
        "description_short": description[:120] + "…" if len(description) > 120 else description,
        "description_long": description,
    }

    # Guardar búsqueda en BD
    search = {
        "title": data.title,
        "book": book,
        "searchedAt": datetime.utcnow()
    }
    searches_collection.insert_one(search)

    return book

# ---------- Ver datos en BD (para tu profesor) ----------
@app.get("/data/users")
def get_users():
    return list(users_collection.find({}, {"_id": 0}))

@app.get("/data/searches")
def get_searches():
    return list(searches_collection.find({}, {"_id": 0}))