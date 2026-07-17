from fastapi import APIRouter, HTTPException
import httpx
from src.schemas.api_models import UserLocationRequest, ATMResponse
from src.services.crud_client import fetch_nearest_atms
from src.core.config import settings

router = APIRouter()

@router.post("/nearest", response_model=ATMResponse)
async def locate_nearest_atm(request: UserLocationRequest):
    # 1. Llamar a la API CRUD para obtener los más cercanos (limite alto para tener cobertura completa)
    atms = await fetch_nearest_atms(request.latitude, request.longitude, limit=100)
    
    if not atms:
        raise HTTPException(status_code=404, detail="No se encontraron cajeros registrados en el sistema")
        
    # Nivel 1: Activo, saldo > 0, tipo Fijo, y cumple servicios requeridos (si se solicitan)
    for atm in atms:
        if atm.estado == "Activo" and atm.saldo_disponible > 0 and atm.tipo == "Fijo":
            if request.servicios_requeridos:
                has_services = all(service in atm.servicios_ofrecidos for service in request.servicios_requeridos)
                if not has_services:
                    continue
            return atm
            
    # Nivel 2: Activo, saldo > 0, tipo Fijo (ignorando servicios)
    for atm in atms:
        if atm.estado == "Activo" and atm.saldo_disponible > 0 and atm.tipo == "Fijo":
            return atm
            
    # Nivel 3: Activo, tipo Fijo (ignorando saldo y servicios)
    for atm in atms:
        if atm.estado == "Activo" and atm.tipo == "Fijo":
            return atm
            
    # Nivel 4: Cualquier cajero Fijo (ignorando estado, saldo y servicios)
    for atm in atms:
        if atm.tipo == "Fijo":
            return atm
            
    # Nivel 5: Cualquier cajero disponible (Fijo o Móvil)
    return atms[0]

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
