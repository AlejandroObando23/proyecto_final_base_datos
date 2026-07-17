from pydantic import BaseModel
from typing import List, Optional

class CajeroBase(BaseModel):
    codigo: str
    nombre_ubicacion: str
    latitud: float
    longitud: float
    estado: str
    saldo_disponible: float
    tipo: str

class CajeroCreate(CajeroBase):
    servicios_ofrecidos: List[str] = []

class CajeroUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre_ubicacion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: Optional[str] = None
    saldo_disponible: Optional[float] = None
    tipo: Optional[str] = None
    servicios_ofrecidos: Optional[List[str]] = None

class CajeroResponse(CajeroBase):
    id: str
    servicios_ofrecidos: List[str] = []
    distancia_metros: Optional[float] = None
