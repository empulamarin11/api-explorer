from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Explorer", version="0.1.0")

# Permitir que el frontend (3000) hable con el backend (8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hola desde FastAPI 👋"}

# Endpoint de prueba que ya consume PokéAPI
@app.get("/pokemon/{name}")
async def get_pokemon(name: str):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Pokémon no encontrado")
        data = resp.json()
        return {
            "id": data["id"],
            "name": data["name"],
            "types": [t["type"]["name"] for t in data["types"]],
            "image": data["sprites"]["front_default"],
        }