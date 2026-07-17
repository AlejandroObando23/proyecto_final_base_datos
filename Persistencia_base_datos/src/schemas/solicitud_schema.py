from pydantic import BaseModel
from typing import Optional

class SolicitudCreate(BaseModel):
    usuario_id: str
    monto: float
    latitud_usuario: float
    longitud_usuario: float

class SolicitudResponse(BaseModel):
    id: str
    usuario_id: str
    monto: float
    latitud_usuario: float
    longitud_usuario: float
    estado: str
    fecha: str
    cajero_id: Optional[str] = None
    cajero_nombre: Optional[str] = None
    cajero_codigo: Optional[str] = None
    cajero_latitud: Optional[float] = None
    cajero_longitud: Optional[float] = None
    distancia_metros: Optional[float] = None
