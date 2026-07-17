from fastapi import APIRouter, HTTPException, status
import uuid
import hashlib
from src.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, UsuarioLogin
from src.core.database import db

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register_usuario(usuario: UsuarioCreate):
    # 1. Verificar si el usuario ya existe
    check_query = "MATCH (u:Usuario {username: $username}) RETURN u.username as username"
    
    try:
        async with db.driver.session() as session:
            result = await session.run(check_query, username=usuario.username)
            record = await result.single()
            if record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre de usuario ya está registrado"
                )
                
            # 2. Crear el nuevo usuario
            new_id = str(uuid.uuid4())
            pwd_hash = hash_password(usuario.password)
            
            create_query = """
            CREATE (u:Usuario {
                id: $id,
                username: $username,
                password_hash: $password_hash,
                email: $email,
                nombre: $nombre,
                es_admin: false,
                fecha_registro: datetime()
            })
            RETURN u.id as id, u.username as username, u.email as email, u.nombre as nombre, u.es_admin as es_admin
            """
            
            result_create = await session.run(
                create_query,
                id=new_id,
                username=usuario.username,
                password_hash=pwd_hash,
                email=usuario.email,
                nombre=usuario.nombre
            )
            created_record = await result_create.single()
            if not created_record:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo registrar el usuario en la base de datos"
                )
                
            return {
                "id": created_record["id"],
                "username": created_record["username"],
                "email": created_record["email"],
                "nombre": created_record["nombre"],
                "es_admin": created_record["es_admin"] or False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el registro en la base de datos"
        )

@router.post("/login", response_model=UsuarioResponse)
async def login_usuario(usuario: UsuarioLogin):
    query = """
    MATCH (u:Usuario {username: $username})
    RETURN u.id as id, u.username as username, u.password_hash as password_hash, u.email as email, u.nombre as nombre, u.es_admin as es_admin
    """
    
    try:
        async with db.driver.session() as session:
            result = await session.run(query, username=usuario.username)
            record = await result.single()
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Nombre de usuario o contraseña incorrectos"
                )
                
            pwd_hash = hash_password(usuario.password)
            if record["password_hash"] != pwd_hash:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Nombre de usuario o contraseña incorrectos"
                )
                
            return {
                "id": record["id"],
                "username": record["username"],
                "email": record["email"],
                "nombre": record["nombre"],
                "es_admin": record["es_admin"] or False
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el inicio de sesión en la base de datos"
        )
