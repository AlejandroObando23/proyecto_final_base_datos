from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid
from src.schemas.historial_schema import HistorialCreate, HistorialResponse
from src.core.database import db

router = APIRouter()

@router.post("/{user_id}/historial", response_model=HistorialResponse, status_code=status.HTTP_201_CREATED)
async def create_historial_entry(user_id: str, entry: HistorialCreate):
    # Verificar si el usuario existe
    user_check = "MATCH (u:Usuario {id: $user_id}) RETURN u.id as id"
    
    query = """
    MATCH (u:Usuario {id: $user_id})
    CREATE (h:HistorialUso {
        id: $id,
        tipo_accion: $tipo_accion,
        descripcion: $descripcion,
        fecha: datetime()
    })
    CREATE (u)-[:REALIZO]->(h)
    RETURN h.id as id, h.tipo_accion as tipo_accion, h.descripcion as descripcion, toString(h.fecha) as fecha
    """
    
    try:
        async with db.driver.session() as session:
            check_result = await session.run(user_check, user_id=user_id)
            user_exists = await check_result.single()
            if not user_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
                
            new_id = str(uuid.uuid4())
            result = await session.run(
                query,
                user_id=user_id,
                id=new_id,
                tipo_accion=entry.tipo_accion,
                descripcion=entry.descripcion
            )
            record = await result.single()
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo registrar la entrada en el historial"
                )
                
            return {
                "id": record["id"],
                "tipo_accion": record["tipo_accion"],
                "descripcion": record["descripcion"],
                "fecha": record["fecha"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el historial en la base de datos"
        )

@router.get("/{user_id}/historial", response_model=List[HistorialResponse])
async def get_usuario_historial(user_id: str):
    query = """
    MATCH (u:Usuario {id: $user_id})-[:REALIZO]->(h:HistorialUso)
    RETURN h.id as id, h.tipo_accion as tipo_accion, h.descripcion as descripcion, toString(h.fecha) as fecha
    ORDER BY h.fecha DESC
    """
    
    try:
        async with db.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            records = await result.data()
            return records
    except Exception as e:
        print(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar el historial desde la base de datos"
        )
