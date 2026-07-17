from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import locator, auth, historial, cajeros

app = FastAPI(
    title="Business Rules API - Cajeros Produbanco",
    description="API Gateway para reglas de negocio",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locator.router, prefix="/api/v1/locator", tags=["Locator"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(historial.router, prefix="/api/v1/historial", tags=["Historial"])
app.include_router(cajeros.router, prefix="/api/v1/cajeros", tags=["Cajeros"])

@app.get("/")
def root():
    return {"message": "Business Rules API Online"}
