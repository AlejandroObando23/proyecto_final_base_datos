import httpx
from typing import List
from src.schemas.api_models import ATMResponse, ATMCreate, ATMUpdate
from src.core.config import settings

async def fetch_nearest_atms(lat: float, lon: float, limit: int = 3) -> List[ATMResponse]:
    """Llama a la API CRUD para obtener los cajeros más cercanos en bruto"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.CRUD_API_URL}/api/v1/cajeros/nearest",
                params={"lat": lat, "lon": lon, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            return [ATMResponse(**atm) for atm in data]
        except Exception as e:
            print(f"Error conectando a API CRUD: {e}")
            return []

async def fetch_all_atms() -> List[ATMResponse]:
    """Obtiene todos los cajeros en la base de datos"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.CRUD_API_URL}/api/v1/cajeros")
            response.raise_for_status()
            data = response.json()
            return [ATMResponse(**atm) for atm in data]
        except Exception as e:
            print(f"Error conectando a API CRUD para obtener todos: {e}")
            return []

async def fetch_atm_by_id(atm_id: str) -> ATMResponse:
    """Obtiene un cajero por su ID"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.CRUD_API_URL}/api/v1/cajeros/{atm_id}")
            response.raise_for_status()
            return ATMResponse(**response.json())
        except Exception as e:
            print(f"Error conectando a API CRUD para obtener por ID {atm_id}: {e}")
            raise

async def create_atm(cajero: ATMCreate) -> ATMResponse:
    """Crea un nuevo cajero"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.CRUD_API_URL}/api/v1/cajeros",
                json=cajero.model_dump()
            )
            response.raise_for_status()
            return ATMResponse(**response.json())
        except Exception as e:
            print(f"Error conectando a API CRUD para crear: {e}")
            raise

async def update_atm(atm_id: str, cajero: ATMUpdate) -> ATMResponse:
    """Actualiza un cajero existente"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.CRUD_API_URL}/api/v1/cajeros/{atm_id}",
                json=cajero.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            return ATMResponse(**response.json())
        except Exception as e:
            print(f"Error conectando a API CRUD para actualizar: {e}")
            raise

async def delete_atm(atm_id: str) -> bool:
    """Elimina un cajero"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{settings.CRUD_API_URL}/api/v1/cajeros/{atm_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error conectando a API CRUD para eliminar: {e}")
            raise
