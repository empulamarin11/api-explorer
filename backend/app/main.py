from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import httpx, os

# ---------- SQLAlchemy ----------
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASS')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- Modelos ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)

class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    book_title = Column(String(200))
    book_authors = Column(Text)
    book_image = Column(Text)
    book_desc_short = Column(Text)
    book_desc_long = Column(Text)
    searched_at = Column(DateTime, default=datetime.utcnow)

# ---------- Crear tablas ----------
Base.metadata.create_all(bind=engine)

# ---------- FastAPI ----------
app = FastAPI(title="API Explorer – Login simple", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Dependencias ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Endpoints ----------
@app.get("/")
def root():
    return {"message": "Backend conectado a PostgreSQL – login simple"}

@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:   # comparación directa
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    user.logged_at = datetime.utcnow()
    db.commit()
    return {"user_id": user.id, "username": user.username}

@app.post("/register")   # para crear usuarios rápido
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    return {"message": "Usuario creado", "user_id": user.id}

@app.get("/books")
async def books(title: str):
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}&maxResults=1"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200 or not r.json().get("items"):
            raise HTTPException(status_code=404, detail="Libro no encontrado")
    info = r.json()["items"][0]["volumeInfo"]
    desc = info.get("description", "Sin descripción")
    return {
        "title": info.get("title", "Sin título"),
        "authors": info.get("authors", ["Anónimo"]),
        "image": info.get("imageLinks", {}).get("thumbnail", "").replace("http://", "https://"),
        "description_short": desc[:120] + "…" if len(desc) > 120 else desc,
        "description_long": desc,
    }

@app.post("/search")
async def search(title: str, user_id: int, db: Session = Depends(get_db)):
    # comprobar que el usuario existe
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # traer libro
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}&maxResults=1"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200 or not r.json().get("items"):
            raise HTTPException(status_code=404, detail="Libro no encontrado")
    info = r.json()["items"][0]["volumeInfo"]
    desc = info.get("description", "Sin descripción")
    book = {
        "title": info.get("title", "Sin título"),
        "authors": info.get("authors", ["Anónimo"]),
        "image": info.get("imageLinks", {}).get("thumbnail", "").replace("http://", "https://"),
        "description_short": desc[:120] + "…" if len(desc) > 120 else desc,
        "description_long": desc,
    }
    # guardar búsqueda
    search = Search(
        user_id=user_id,
        title=title,
        book_title=book["title"],
        book_authors=", ".join(book["authors"]),
        book_image=book["image"],
        book_desc_short=book["description_short"],
        book_desc_long=book["description_long"]
    )
    db.add(search)
    db.commit()
    return book

@app.get("/history")
def history(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(Search).filter(Search.user_id == user_id).order_by(Search.searched_at.desc()).all()
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
        for s in rows
    ]