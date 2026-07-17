from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import uuid
import hashlib
from src.schemas.cajero_schema import CajeroResponse, CajeroCreate, CajeroUpdate
from src.schemas.solicitud_schema import SolicitudCreate, SolicitudResponse
from src.core.database import db

router = APIRouter()

@router.get("/nearest", response_model=List[CajeroResponse])
async def get_nearest_atms(lat: float, lon: float, limit: int = 3):
    query = """
    WITH point({latitude: $lat, longitude: $lon}) AS ubicacion_usuario
    MATCH (c:Cajero)
    OPTIONAL MATCH (c)-[:OFRECE]->(s:ServicioBancario)
    WITH c, point.distance(c.coordenadas, ubicacion_usuario) AS distancia_metros, collect(s.nombre) as servicios_ofrecidos
    ORDER BY distancia_metros ASC
    LIMIT toInteger($limit)
    RETURN 
        c.id AS id, 
        c.codigo AS codigo, 
        c.nombre_ubicacion AS nombre_ubicacion, 
        c.coordenadas.latitude AS latitud, 
        c.coordenadas.longitude AS longitud,
        c.estado AS estado, 
        c.saldo_disponible AS saldo_disponible, 
        c.tipo AS tipo, 
        servicios_ofrecidos, 
        distancia_metros
    """
    
    try:
        async with db.driver.session() as session:
            result = await session.run(query, lat=lat, lon=lon, limit=limit)
            records = await result.data()
            return records
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_database():
    try:
        async with db.driver.session() as session:
            # 1. Limpiar base de datos
            await session.run("MATCH (n) DETACH DELETE n")
            
            # 2. Crear servicios bancarios
            services = ["Retiro", "Depósito", "Consulta de Saldo", "Pago de Servicios"]
            for svc in services:
                await session.run("CREATE (:ServicioBancario {nombre: $nombre})", nombre=svc)
                
            # 3. Datos de Cajeros Fijos (Coordenadas en Quito)
            cajeros_fijos = [
                {
                    "codigo": "ATMF-001",
                    "nombre": "Cajero Centro Comercial Iñaquito (CCI)",
                    "lat": -0.1772, "lon": -78.4801,
                    "saldo": 18500.0,
                    "servicios": ["Retiro", "Consulta de Saldo", "Pago de Servicios"]
                },
                {
                    "codigo": "ATMF-002",
                    "nombre": "Cajero El Recreo Shopping",
                    "lat": -0.2483, "lon": -78.5147,
                    "saldo": 24000.0,
                    "servicios": ["Retiro", "Depósito", "Consulta de Saldo"]
                },
                {
                    "codigo": "ATMF-003",
                    "nombre": "Cajero Plaza Foch (La Mariscal)",
                    "lat": -0.2027, "lon": -78.4908,
                    "saldo": 8000.0,
                    "servicios": ["Retiro", "Consulta de Saldo"]
                },
                {
                    "codigo": "ATMF-004",
                    "nombre": "Cajero Universidad Central (Uce)",
                    "lat": -0.2005, "lon": -78.5029,
                    "saldo": 12000.0,
                    "servicios": ["Retiro", "Consulta de Saldo", "Pago de Servicios"]
                },
                {
                    "codigo": "ATMF-005",
                    "nombre": "Cajero Quicentro Shopping Norte",
                    "lat": -0.1764, "lon": -78.4795,
                    "saldo": 32000.0,
                    "servicios": ["Retiro", "Depósito", "Consulta de Saldo", "Pago de Servicios"]
                },
                {
                    "codigo": "ATMF-006",
                    "nombre": "Cajero Paseo San Francisco (Cumbayá)",
                    "lat": -0.2012, "lon": -78.4354,
                    "saldo": 15000.0,
                    "servicios": ["Retiro", "Consulta de Saldo"]
                },
                {
                    "codigo": "ATMF-007",
                    "nombre": "Cajero Parque La Carolina",
                    "lat": -0.1852, "lon": -78.4841,
                    "saldo": 19000.0,
                    "servicios": ["Retiro", "Depósito", "Consulta de Saldo"]
                }
            ]
            
            # Insertar cajeros fijos
            for c in cajeros_fijos:
                c_id = str(uuid.uuid4())
                # Crear cajero
                await session.run("""
                CREATE (c:Cajero {
                    id: $id,
                    codigo: $codigo,
                    nombre_ubicacion: $nombre,
                    coordenadas: point({latitude: $lat, longitude: $lon}),
                    estado: 'Activo',
                    saldo_disponible: $saldo,
                    tipo: 'Fijo'
                })
                """, id=c_id, codigo=c["codigo"], nombre=c["nombre"], lat=c["lat"], lon=c["lon"], saldo=c["saldo"])
                
                # Relacionar servicios
                for svc in c["servicios"]:
                    await session.run("""
                    MATCH (c:Cajero {id: $c_id}), (s:ServicioBancario {nombre: $s_name})
                    CREATE (c)-[:OFRECE]->(s)
                    """, c_id=c_id, s_name=svc)
            
            # 4. Datos de Cajeros Móviles (Uber Cajero)
            cajeros_moviles = [
                {
                    "codigo": "ATMM-901",
                    "nombre": "Cajero Móvil Norte (Camioneta D-Max)",
                    "lat": -0.1700, "lon": -78.4700,
                    "saldo": 45000.0,
                    "servicios": ["Retiro"]
                },
                {
                    "codigo": "ATMM-902",
                    "nombre": "Cajero Móvil Centro (Furgoneta H1)",
                    "lat": -0.1900, "lon": -78.4950,
                    "saldo": 60000.0,
                    "servicios": ["Retiro", "Consulta de Saldo"]
                },
                {
                    "codigo": "ATMM-903",
                    "nombre": "Cajero Móvil Sur (Blindado Mediano)",
                    "lat": -0.2300, "lon": -78.5100,
                    "saldo": 50000.0,
                    "servicios": ["Retiro"]
                }
            ]
            
            # Insertar cajeros móviles
            for c in cajeros_moviles:
                c_id = str(uuid.uuid4())
                await session.run("""
                CREATE (c:Cajero {
                    id: $id,
                    codigo: $codigo,
                    nombre_ubicacion: $nombre,
                    coordenadas: point({latitude: $lat, longitude: $lon}),
                    estado: 'Activo',
                    saldo_disponible: $saldo,
                    tipo: 'Móvil'
                })
                """, id=c_id, codigo=c["codigo"], nombre=c["nombre"], lat=c["lat"], lon=c["lon"], saldo=c["saldo"])
                
                for svc in c["servicios"]:
                    await session.run("""
                    MATCH (c:Cajero {id: $c_id}), (s:ServicioBancario {nombre: $s_name})
                    CREATE (c)-[:OFRECE]->(s)
                    """, c_id=c_id, s_name=svc)
                    
            # 5. Crear usuario de prueba por defecto (admin / password123)
            admin_id = str(uuid.uuid4())
            admin_pwd_hash = hashlib.sha256("password123".encode()).hexdigest()
            await session.run("""
            CREATE (u:Usuario {
                id: $id,
                username: 'admin',
                password_hash: $pwd_hash,
                email: 'admin@produbanco.com',
                nombre: 'Admin Produbanco',
                es_admin: true,
                fecha_registro: datetime()
            })
            """, id=admin_id, pwd_hash=admin_pwd_hash)
            
            # Registrar entrada de historial para el seed
            await session.run("""
            MATCH (u:Usuario {username: 'admin'})
            CREATE (h:HistorialUso {
                id: $h_id,
                tipo_accion: 'Sistema',
                descripcion: 'Reestablecimiento de datos Neo4j (Seeding)',
                fecha: datetime()
            })
            CREATE (u)-[:REALIZO]->(h)
            """, h_id=str(uuid.uuid4()))
            
            return {"message": "Base de datos sembrada con éxito. Usuario administrador creado ('admin' / 'password123')"}
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")

@router.post("/solicitar", response_model=SolicitudResponse)
async def solicitar_cajero_movil(req: SolicitudCreate):
    # 1. Verificar que el usuario existe
    user_check_query = "MATCH (u:Usuario {id: $u_id}) RETURN u.id as id"
    
    # 2. Buscar el cajero móvil activo más cercano
    find_cajero_query = """
    WITH point({latitude: $lat, longitude: $lon}) AS ubicacion_usuario
    MATCH (c:Cajero {tipo: 'Móvil', estado: 'Activo'})
    WITH c, point.distance(c.coordenadas, ubicacion_usuario) AS distancia_metros
    ORDER BY distancia_metros ASC
    LIMIT 1
    RETURN 
        c.id as id,
        c.nombre_ubicacion as nombre,
        c.codigo as codigo,
        c.coordenadas.latitude as latitud,
        c.coordenadas.longitude as longitud,
        distancia_metros
    """
    
    # 3. Crear solicitud de despacho
    create_solicitud_query = """
    MATCH (u:Usuario {id: $u_id})
    MATCH (c:Cajero {id: $c_id})
    CREATE (s:SolicitudServicio {
        id: $s_id,
        monto: $monto,
        latitud_usuario: $u_lat,
        longitud_usuario: $u_lon,
        estado: 'Solicitado',
        fecha: datetime()
    })
    CREATE (u)-[:SOLICITO]->(s)
    CREATE (s)-[:ASIGNADO_A]->(c)
    RETURN 
        s.id as id,
        u.id as usuario_id,
        s.monto as monto,
        s.latitud_usuario as latitud_usuario,
        s.longitud_usuario as longitud_usuario,
        s.estado as estado,
        toString(s.fecha) as fecha,
        c.id as cajero_id,
        c.nombre_ubicacion as cajero_nombre,
        c.codigo as cajero_codigo,
        c.coordenadas.latitude as cajero_latitud,
        c.coordenadas.longitude as cajero_longitud
    """
    
    try:
        async with db.driver.session() as session:
            # Validar usuario
            user_check = await session.run(user_check_query, u_id=req.usuario_id)
            if not await user_check.single():
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
                
            # Buscar cajero móvil
            cajero_res = await session.run(find_cajero_query, lat=req.latitud_usuario, lon=req.longitud_usuario)
            cajero = await cajero_res.single()
            if not cajero:
                raise HTTPException(status_code=404, detail="No hay cajeros móviles disponibles en este momento")
                
            # Crear la solicitud
            s_id = str(uuid.uuid4())
            solicitud_res = await session.run(
                create_solicitud_query,
                u_id=req.usuario_id,
                c_id=cajero["id"],
                s_id=s_id,
                monto=req.monto,
                u_lat=req.latitud_usuario,
                u_lon=req.longitud_usuario
            )
            sol = await solicitud_res.single()
            
            # Registrar en historial
            hist_id = str(uuid.uuid4())
            await session.run("""
            MATCH (u:Usuario {id: $u_id})
            CREATE (h:HistorialUso {
                id: $h_id,
                tipo_accion: 'Solicitud Cajero Móvil',
                descripcion: 'Solicitó Cajero Móvil por un monto de $' + toString($monto),
                fecha: datetime()
            })
            CREATE (u)-[:REALIZO]->(h)
            """, u_id=req.usuario_id, h_id=hist_id, monto=req.monto)
            
            return {
                "id": sol["id"],
                "usuario_id": sol["usuario_id"],
                "monto": sol["monto"],
                "latitud_usuario": sol["latitud_usuario"],
                "longitud_usuario": sol["longitud_usuario"],
                "estado": sol["estado"],
                "fecha": sol["fecha"],
                "cajero_id": sol["cajero_id"],
                "cajero_nombre": sol["cajero_nombre"],
                "cajero_codigo": sol["cajero_codigo"],
                "cajero_latitud": sol["cajero_latitud"],
                "cajero_longitud": sol["cajero_longitud"],
                "distancia_metros": cajero["distancia_metros"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error requesting mobile ATM: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.get("/solicitud/{s_id}", response_model=SolicitudResponse)
async def get_solicitud_status(s_id: str):
    query = """
    MATCH (u:Usuario)-[:SOLICITO]->(s:SolicitudServicio {id: $s_id})-[:ASIGNADO_A]->(c:Cajero)
    RETURN 
        s.id as id,
        u.id as usuario_id,
        s.monto as monto,
        s.latitud_usuario as latitud_usuario,
        s.longitud_usuario as longitud_usuario,
        s.estado as estado,
        toString(s.fecha) as fecha,
        c.id as cajero_id,
        c.nombre_ubicacion as cajero_nombre,
        c.codigo as cajero_codigo,
        c.coordenadas.latitude as cajero_latitud,
        c.coordenadas.longitude as cajero_longitud,
        point.distance(c.coordenadas, point({latitude: s.latitud_usuario, longitude: s.longitud_usuario})) as distancia_metros
    """
    
    try:
        async with db.driver.session() as session:
            result = await session.run(query, s_id=s_id)
            record = await result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Solicitud no encontrada")
                
            return record
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching request status: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.put("/solicitud/{s_id}", response_model=SolicitudResponse)
async def update_solicitud_status(s_id: str, estado: str):
    query = """
    MATCH (s:SolicitudServicio {id: $s_id})
    SET s.estado = $estado
    WITH s
    MATCH (u:Usuario)-[:SOLICITO]->(s)-[:ASIGNADO_A]->(c:Cajero)
    RETURN 
        s.id as id,
        u.id as usuario_id,
        s.monto as monto,
        s.latitud_usuario as latitud_usuario,
        s.longitud_usuario as longitud_usuario,
        s.estado as estado,
        toString(s.fecha) as fecha,
        c.id as cajero_id,
        c.nombre_ubicacion as cajero_nombre,
        c.codigo as cajero_codigo,
        c.coordenadas.latitude as cajero_latitud,
        c.coordenadas.longitude as cajero_longitud,
        point.distance(c.coordenadas, point({latitude: s.latitud_usuario, longitude: s.longitud_usuario})) as distancia_metros
    """
    
    try:
        async with db.driver.session() as session:
            result = await session.run(query, s_id=s_id, estado=estado)
            record = await result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Solicitud no encontrada")
                
            # Registrar en historial si el estado cambia a completado
            if estado.lower() == "completado":
                hist_id = str(uuid.uuid4())
                await session.run("""
                MATCH (u:Usuario {id: $u_id})
                CREATE (h:HistorialUso {
                    id: $h_id,
                    tipo_accion: 'Cajero Móvil Entregado',
                    descripcion: 'Se completó con éxito el retiro de dinero del cajero móvil ' + $cajero_nombre,
                    fecha: datetime()
                })
                CREATE (u)-[:REALIZO]->(h)
                """, u_id=record["usuario_id"], h_id=hist_id, cajero_nombre=record["cajero_nombre"])
                
            return record
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating request status: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

# --- CRUD ENDPOINTS FOR CAJEROS ---

@router.get("", response_model=List[CajeroResponse])
async def get_all_atms():
    query = """
    MATCH (c:Cajero)
    OPTIONAL MATCH (c)-[:OFRECE]->(s:ServicioBancario)
    WITH c, collect(s.nombre) as servicios_ofrecidos
    RETURN 
        c.id AS id, 
        c.codigo AS codigo, 
        c.nombre_ubicacion AS nombre_ubicacion, 
        c.coordenadas.latitude AS latitud, 
        c.coordenadas.longitude AS longitud,
        c.estado AS estado, 
        c.saldo_disponible AS saldo_disponible, 
        c.tipo AS tipo, 
        servicios_ofrecidos
    """
    try:
        async with db.driver.session() as session:
            result = await session.run(query)
            records = await result.data()
            return records
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.get("/{id}", response_model=CajeroResponse)
async def get_atm(id: str):
    query = """
    MATCH (c:Cajero {id: $id})
    OPTIONAL MATCH (c)-[:OFRECE]->(s:ServicioBancario)
    WITH c, collect(s.nombre) as servicios_ofrecidos
    RETURN 
        c.id AS id, 
        c.codigo AS codigo, 
        c.nombre_ubicacion AS nombre_ubicacion, 
        c.coordenadas.latitude AS latitud, 
        c.coordenadas.longitude AS longitud,
        c.estado AS estado, 
        c.saldo_disponible AS saldo_disponible, 
        c.tipo AS tipo, 
        servicios_ofrecidos
    """
    try:
        async with db.driver.session() as session:
            result = await session.run(query, id=id)
            record = await result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Cajero no encontrado")
            return dict(record)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error querying Neo4j: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.post("", response_model=CajeroResponse, status_code=status.HTTP_201_CREATED)
async def create_atm(cajero: CajeroCreate):
    c_id = str(uuid.uuid4())
    create_query = """
    CREATE (c:Cajero {
        id: $id,
        codigo: $codigo,
        nombre_ubicacion: $nombre_ubicacion,
        coordenadas: point({latitude: $latitud, longitude: $longitud}),
        estado: $estado,
        saldo_disponible: $saldo_disponible,
        tipo: $tipo
    })
    """
    try:
        async with db.driver.session() as session:
            await session.run(
                create_query,
                id=c_id,
                codigo=cajero.codigo,
                nombre_ubicacion=cajero.nombre_ubicacion,
                latitud=cajero.latitud,
                longitud=cajero.longitud,
                estado=cajero.estado,
                saldo_disponible=cajero.saldo_disponible,
                tipo=cajero.tipo
            )
            # Create services relationships
            for svc in cajero.servicios_ofrecidos:
                await session.run("""
                MATCH (c:Cajero {id: $c_id}), (s:ServicioBancario {nombre: $s_name})
                CREATE (c)-[:OFRECE]->(s)
                """, c_id=c_id, s_name=svc)
                
            return {
                "id": c_id,
                "codigo": cajero.codigo,
                "nombre_ubicacion": cajero.nombre_ubicacion,
                "latitud": cajero.latitud,
                "longitud": cajero.longitud,
                "estado": cajero.estado,
                "saldo_disponible": cajero.saldo_disponible,
                "tipo": cajero.tipo,
                "servicios_ofrecidos": cajero.servicios_ofrecidos
            }
    except Exception as e:
        print(f"Error creating ATM in Neo4j: {e}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@router.put("/{id}", response_model=CajeroResponse)
async def update_atm(id: str, cajero: CajeroUpdate):
    check_query = "MATCH (c:Cajero {id: $id}) RETURN c.id as id"
    try:
        async with db.driver.session() as session:
            check_res = await session.run(check_query, id=id)
            if not await check_res.single():
                raise HTTPException(status_code=404, detail="Cajero no encontrado")
            
            set_clauses = []
            params = {"id": id}
            
            if cajero.codigo is not None:
                set_clauses.append("c.codigo = $codigo")
                params["codigo"] = cajero.codigo
            if cajero.nombre_ubicacion is not None:
                set_clauses.append("c.nombre_ubicacion = $nombre_ubicacion")
                params["nombre_ubicacion"] = cajero.nombre_ubicacion
            if cajero.latitud is not None or cajero.longitud is not None:
                if cajero.latitud is not None and cajero.longitud is not None:
                    set_clauses.append("c.coordenadas = point({latitude: $latitud, longitude: $longitud})")
                    params["latitud"] = cajero.latitud
                    params["longitud"] = cajero.longitud
                else:
                    coord_query = "MATCH (c:Cajero {id: $id}) RETURN c.coordenadas.latitude as lat, c.coordenadas.longitude as lon"
                    coord_res = await session.run(coord_query, id=id)
                    coord_rec = await coord_res.single()
                    lat = cajero.latitud if cajero.latitud is not None else coord_rec["lat"]
                    lon = cajero.longitud if cajero.longitud is not None else coord_rec["lon"]
                    set_clauses.append("c.coordenadas = point({latitude: $latitud, longitude: $longitud})")
                    params["latitud"] = lat
                    params["longitud"] = lon
            if cajero.estado is not None:
                set_clauses.append("c.estado = $estado")
                params["estado"] = cajero.estado
            if cajero.saldo_disponible is not None:
                set_clauses.append("c.saldo_disponible = $saldo_disponible")
                params["saldo_disponible"] = cajero.saldo_disponible
            if cajero.tipo is not None:
                set_clauses.append("c.tipo = $tipo")
                params["tipo"] = cajero.tipo
                
            if set_clauses:
                update_query = f"MATCH (c:Cajero {{id: $id}}) SET {', '.join(set_clauses)}"
                await session.run(update_query, **params)
                
            if cajero.servicios_ofrecidos is not None:
                await session.run("MATCH (c:Cajero {id: $id})-[r:OFRECE]->() DELETE r", id=id)
                for svc in cajero.servicios_ofrecidos:
                    await session.run("""
                    MATCH (c:Cajero {id: $c_id}), (s:ServicioBancario {nombre: $s_name})
                    CREATE (c)-[:OFRECE]->(s)
                    """, c_id=id, s_name=svc)
            
            fetch_query = """
            MATCH (c:Cajero {id: $id})
            OPTIONAL MATCH (c)-[:OFRECE]->(s:ServicioBancario)
            WITH c, collect(s.nombre) as servicios_ofrecidos
            RETURN 
                c.id AS id, 
                c.codigo AS codigo, 
                c.nombre_ubicacion AS nombre_ubicacion, 
                c.coordenadas.latitude AS latitud, 
                c.coordenadas.longitude AS longitud,
                c.estado AS estado, 
                c.saldo_disponible AS saldo_disponible, 
                c.tipo AS tipo, 
                servicios_ofrecidos
            """
            res = await session.run(fetch_query, id=id)
            record = await res.single()
            return dict(record)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating ATM in Neo4j: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_atm(id: str):
    check_query = "MATCH (c:Cajero {id: $id}) RETURN c.id as id"
    delete_query = "MATCH (c:Cajero {id: $id}) DETACH DELETE c"
    try:
        async with db.driver.session() as session:
            check_res = await session.run(check_query, id=id)
            if not await check_res.single():
                raise HTTPException(status_code=404, detail="Cajero no encontrado")
            
            await session.run(delete_query, id=id)
            return {"message": "Cajero eliminado con éxito"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting ATM from Neo4j: {e}")
        raise HTTPException(status_code=500, detail="Database Error")
