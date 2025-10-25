from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Explorer – Libros", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hola desde FastAPI – Libros 👋"}

@app.get("/books")
async def get_books(title: str):
    """
    Busca libros en Google Books API y devuelve tarjeta lista para mostrar.
    """
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}&maxResults=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        data = resp.json()
        if not data.get("items"):
            raise HTTPException(status_code=404, detail="Sin resultados")

        info = data["items"][0]["volumeInfo"]
        raw = info.get("description")
        description = raw if raw else "Resumen no disponible."
        return {
            "title": info.get("title", "Sin título"),
            "authors": info.get("authors", ["Anónimo"]),
            "image": info.get("imageLinks", {}).get("thumbnail", "").replace("http://", "https://"),
            "description_short": description[:120] + "…" if len(description) > 120 else description,
            "description_long": description,
        }