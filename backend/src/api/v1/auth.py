from fastapi import APIRouter, HTTPException, status
import httpx
from src.schemas.api_models import UsuarioCreate, UsuarioResponse, UsuarioLogin
from src.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(usuario: UsuarioCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.CRUD_API_URL}/api/v1/usuarios/register",
                json=usuario.model_dump()
            )
            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error en el servicio de persistencia")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )

@router.post("/login", response_model=UsuarioResponse)
async def login(usuario: UsuarioLogin):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.CRUD_API_URL}/api/v1/usuarios/login",
                json=usuario.model_dump()
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Credenciales incorrectas")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )
