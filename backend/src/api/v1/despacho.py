from fastapi import APIRouter, HTTPException, status
import httpx
from src.schemas.api_models import SolicitudCreate, SolicitudResponse
from src.core.config import settings

router = APIRouter()

@router.post("/solicitar", response_model=SolicitudResponse)
async def solicitar_cajero_movil(req: SolicitudCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.CRUD_API_URL}/api/v1/cajeros/solicitar",
                json=req.model_dump()
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al solicitar cajero móvil")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )

@router.get("/solicitud/{s_id}", response_model=SolicitudResponse)
async def get_solicitud(s_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.CRUD_API_URL}/api/v1/cajeros/solicitud/{s_id}"
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al consultar la solicitud")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )

@router.put("/solicitud/{s_id}", response_model=SolicitudResponse)
async def update_solicitud(s_id: str, estado: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.CRUD_API_URL}/api/v1/cajeros/solicitud/{s_id}",
                params={"estado": estado}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al actualizar la solicitud")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )
