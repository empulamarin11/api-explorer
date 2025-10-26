from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# ---------- Conexión a PostgreSQL ----------
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASS')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- Modelos SQL (tablas) ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))
    logged_at = Column(DateTime, default=datetime.utcnow)

class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    book_title = Column(String(200))
    book_authors = Column(Text)
    book_image = Column(Text)
    book_desc_short = Column(Text)
    book_desc_long = Column(Text)
    searched_at = Column(DateTime, default=datetime.utcnow)

# ---------- Crear tablas (si no existen) ----------
Base.metadata.create_all(bind=engine)

# ---------- FastAPI app ----------
app = FastAPI(title="API Explorer – Books + PostgreSQL", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Modelos Pydantic ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class SearchRequest(BaseModel):
    title: str

# ---------- Endpoints ----------
@app.get("/")
def read_root():
    return {"message": "Backend conectado a PostgreSQL 🐘"}

@app.post("/login")
def login(data: LoginRequest):
    if data.username != os.getenv("POSTGRES_USER") or data.password != os.getenv("POSTGRES_PASS"):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    with SessionLocal() as db:
        user = User(username=data.username, password=data.password, logged_at=datetime.utcnow())
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"message": "Login exitoso", "userId": user.id}

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

    # Guardar búsqueda en PostgreSQL
    with SessionLocal() as db:
        search = Search(
            title=data.title,
            book_title=book["title"],
            book_authors=", ".join(book["authors"]),
            book_image=book["image"],
            book_desc_short=book["description_short"],
            book_desc_long=book["description_long"],
            searched_at=datetime.utcnow()
        )
        db.add(search)
        db.commit()
        db.refresh(search)

    return book

# ---------- Ver datos en PostgreSQL (para tu profesor) ----------
@app.get("/data/users")
def get_users():
    with SessionLocal() as db:
        users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "logged_at": u.logged_at.isoformat()} for u in users]

@app.get("/data/searches")
def get_searches():
    with SessionLocal() as db:
        searches = db.query(Search).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "book": {
                "title": s.book_title,
                "authors": s.book_authors,
                "image": s.book_image,
                "description_short": s.book_desc_short,
                "description_long": s.book_desc_long,
            },
            "searched_at": s.searched_at.isoformat(),
        }
        for s in searches
    ]