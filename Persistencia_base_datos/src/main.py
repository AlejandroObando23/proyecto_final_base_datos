from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.database import db
from src.api.v1 import cajeros, usuarios, historial

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.close()

app = FastAPI(
    title="API CRUD Persistencia Neo4j - Produbanco",
    lifespan=lifespan
)

app.include_router(cajeros.router, prefix="/api/v1/cajeros", tags=["Cajeros"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(historial.router, prefix="/api/v1/usuarios", tags=["Historial"])

@app.get("/")
def root():
    return {"message": "API CRUD Database Online"}
