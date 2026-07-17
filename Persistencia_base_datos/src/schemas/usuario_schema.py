from pydantic import BaseModel

class UsuarioBase(BaseModel):
    username: str
    email: str
    nombre: str

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class UsuarioResponse(UsuarioBase):
    id: str
    es_admin: bool = False
