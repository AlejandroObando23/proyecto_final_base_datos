from pydantic import BaseModel
from typing import Optional

class HistorialBase(BaseModel):
    tipo_accion: str
    descripcion: str

class HistorialCreate(HistorialBase):
    pass

class HistorialResponse(HistorialBase):
    id: str
    fecha: str
