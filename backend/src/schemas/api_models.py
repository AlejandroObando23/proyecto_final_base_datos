from pydantic import BaseModel, Field
from typing import List, Optional

class UserLocationRequest(BaseModel):
    latitude: float = Field(..., description="Latitud GPS del usuario")
    longitude: float = Field(..., description="Longitud GPS del usuario")
    servicios_requeridos: Optional[List[str]] = Field(default=[], description="Ej: ['Retiro', 'Depósito']")

class ATMResponse(BaseModel):
    id: str
    codigo: str
    nombre_ubicacion: str
    latitud: float
    longitud: float
    estado: str
    saldo_disponible: float
    tipo: str
    servicios_ofrecidos: List[str]
    distancia_metros: Optional[float] = None

class ATMCreate(BaseModel):
    codigo: str
    nombre_ubicacion: str
    latitud: float
    longitud: float
    estado: str
    saldo_disponible: float
    tipo: str
    servicios_ofrecidos: List[str] = []

class ATMUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre_ubicacion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: Optional[str] = None
    saldo_disponible: Optional[float] = None
    tipo: Optional[str] = None
    servicios_ofrecidos: Optional[List[str]] = None

# --- NUEVOS MODELOS PARA AUTH Y HISTORIAL ---

class UsuarioCreate(BaseModel):
    username: str
    email: str
    nombre: str
    password: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class UsuarioResponse(BaseModel):
    id: str
    username: str
    email: str
    nombre: str
    es_admin: bool = False

class HistorialCreate(BaseModel):
    tipo_accion: str
    descripcion: str

class HistorialResponse(BaseModel):
    id: str
    tipo_accion: str
    descripcion: str
    fecha: str

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
