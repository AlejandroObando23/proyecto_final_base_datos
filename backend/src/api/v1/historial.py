from fastapi import APIRouter, HTTPException, status
from typing import List
import httpx
from src.schemas.api_models import HistorialCreate, HistorialResponse
from src.core.config import settings

router = APIRouter()

@router.post("/{user_id}", response_model=HistorialResponse, status_code=status.HTTP_201_CREATED)
async def add_historial(user_id: str, entry: HistorialCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.CRUD_API_URL}/api/v1/usuarios/{user_id}/historial",
                json=entry.model_dump()
            )
            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al registrar el historial")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )

@router.get("/{user_id}", response_model=List[HistorialResponse])
async def get_historial(user_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.CRUD_API_URL}/api/v1/usuarios/{user_id}/historial"
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al obtener el historial")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )
