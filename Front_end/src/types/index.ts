export interface UserLocation {
    latitude: number;
    longitude: number;
}

export interface ATM {
    id: string;
    codigo: string;
    nombre_ubicacion: string;
    latitud: number;
    longitud: number;
    estado: string;
    saldo_disponible: number;
    tipo: string;
    servicios_ofrecidos: string[];
    distancia_metros: number;
}

export interface User {
    id: string;
    username: string;
    email: string;
    nombre: string;
    es_admin: boolean;
}

export interface HistoryEntry {
    id: string;
    tipo_accion: string;
    descripcion: string;
    fecha: string;
}

export interface DispatchStatus {
    id: string;
    usuario_id: string;
    monto: number;
    latitud_usuario: number;
    longitud_usuario: number;
    estado: string;
    fecha: string;
    cajero_id: string;
    cajero_nombre: string;
    cajero_codigo: string;
    cajero_latitud: number;
    cajero_longitud: number;
    distancia_metros: number;
}
