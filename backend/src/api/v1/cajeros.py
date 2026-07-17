from fastapi import APIRouter, HTTPException, status
from typing import List
from src.schemas.api_models import ATMResponse, ATMCreate, ATMUpdate
from src.services import crud_client

router = APIRouter()

@router.get("", response_model=List[ATMResponse])
async def get_all_cajeros():
    return await crud_client.fetch_all_atms()

@router.get("/{id}", response_model=ATMResponse)
async def get_cajero_by_id(id: str):
    try:
        return await crud_client.fetch_atm_by_id(id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cajero con ID {id} no encontrado"
        )

@router.post("", response_model=ATMResponse, status_code=status.HTTP_201_CREATED)
async def create_cajero(cajero: ATMCreate):
    try:
        return await crud_client.create_atm(cajero)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear cajero: {str(e)}"
        )

@router.put("/{id}", response_model=ATMResponse)
async def update_cajero(id: str, cajero: ATMUpdate):
    try:
        return await crud_client.update_atm(id, cajero)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar cajero: {str(e)}"
        )

@router.delete("/{id}")
async def delete_cajero(id: str):
    try:
        await crud_client.delete_atm(id)
        return {"message": "Cajero eliminado con éxito"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar cajero: {str(e)}"
        )
