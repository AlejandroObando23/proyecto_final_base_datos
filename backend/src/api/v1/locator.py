from fastapi import APIRouter, HTTPException
import httpx
from typing import List
from src.schemas.api_models import UserLocationRequest, ATMResponse
from src.services.crud_client import fetch_nearest_atms
from src.core.config import settings

router = APIRouter()

def _score_atm(atm: ATMResponse, servicios_requeridos: list) -> int:
    """Puntúa un cajero según nivel de prioridad (menor = mejor)"""
    if atm.estado == "Activo" and atm.saldo_disponible > 0 and atm.tipo == "Fijo":
        if servicios_requeridos:
            if all(s in atm.servicios_ofrecidos for s in servicios_requeridos):
                return 1  # Nivel 1
        else:
            return 1  # Nivel 1 sin servicios requeridos
    if atm.estado == "Activo" and atm.saldo_disponible > 0 and atm.tipo == "Fijo":
        return 2  # Nivel 2
    if atm.estado == "Activo" and atm.tipo == "Fijo":
        return 3  # Nivel 3
    if atm.tipo == "Fijo":
        return 4  # Nivel 4
    return 5  # Nivel 5

@router.post("/nearest", response_model=ATMResponse)
async def locate_nearest_atm(request: UserLocationRequest):
    atms = await fetch_nearest_atms(request.latitude, request.longitude, limit=100)
    if not atms:
        raise HTTPException(status_code=404, detail="No se encontraron cajeros registrados en el sistema")
    atms.sort(key=lambda a: (_score_atm(a, request.servicios_requeridos), a.distancia_metros or 0))
    return atms[0]

@router.post("/nearest-list", response_model=List[ATMResponse])
async def locate_nearest_atms_list(request: UserLocationRequest):
    atms = await fetch_nearest_atms(request.latitude, request.longitude, limit=100)
    if not atms:
        raise HTTPException(status_code=404, detail="No se encontraron cajeros registrados en el sistema")
    atms.sort(key=lambda a: (_score_atm(a, request.servicios_requeridos), a.distancia_metros or 0))
    return atms[:3]

@router.post("/seed")
async def seed_database():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.CRUD_API_URL}/api/v1/cajeros/seed")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al sembrar la base de datos")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )

@router.post("/seed")
async def seed_database():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.CRUD_API_URL}/api/v1/cajeros/seed")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Error al sembrar la base de datos")
                )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo conectar con el servicio de base de datos: {str(e)}"
            )
