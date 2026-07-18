import { useState, useEffect } from 'react';
import { useGeolocation } from './hooks/useGeolocation';
import { 
    getNearestATM, 
    loginUser, 
    registerUser, 
    seedDatabase, 
    logUserHistory, 
    getUserHistory, 
    getAllATMs,
    createATM,
    updateATM,
    deleteATM
} from './services/api';
import { ATM, User, HistoryEntry } from './types';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
    LocateFixed, 
    Navigation, 
    AlertCircle, 
    Loader2, 
    User as UserIcon, 
    History as HistoryIcon, 
    LogOut, 
    Database, 
    MapPin, 
    Sparkles, 
    X, 
    ChevronUp, 
    Crosshair 
} from 'lucide-react';

// Custom Icons
const userIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const atmIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const mobileAtmIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Component to handle map view updates
function MapUpdater({ center }: { center: [number, number] | null }) {
    const map = useMap();
    useEffect(() => {
        if (center) {
            map.flyTo(center, 15, { animate: true, duration: 1.5 });
        }
    }, [center, map]);
    return null;
}

// Component to handle clicks on map when in pick-location mode
function MapClickHandler({ enabled, onPick }: { enabled: boolean; onPick: (lat: number, lng: number) => void }) {
    const map = useMap();
    useEffect(() => {
        if (!enabled) return;
        const handler = (e: L.LeafletMouseEvent) => {
            onPick(e.latlng.lat, e.latlng.lng);
        };
        map.on('click', handler);
        return () => { map.off('click', handler); };
    }, [enabled, onPick, map]);
    return null;
}

function App() {
    // --- AUTHENTICATION STATE ---
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [validatingUser, setValidatingUser] = useState(true);
    const [isLoginTab, setIsLoginTab] = useState(true);
    const [authUsername, setAuthUsername] = useState('');
    const [authPassword, setAuthPassword] = useState('');
    const [authEmail, setAuthEmail] = useState('');
    const [authNombre, setAuthNombre] = useState('');
    const [authError, setAuthError] = useState<string | null>(null);
    const [authLoading, setAuthLoading] = useState(false);

    // --- MAIN INTERFACE STATE ---
    const [activeTab, setActiveTab] = useState<'locator' | 'cajeros' | 'history' | 'account'>('locator');
    const { location, error, getLocation } = useGeolocation();
    const [atm, setAtm] = useState<ATM | null>(null);
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);
    const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);

    // --- GESTIÓN DE CAJEROS STATE ---
    const [atmsList, setAtmsList] = useState<ATM[]>([]);
    const [atmsLoading, setAtmsLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('todos');
    const [typeFilter, setTypeFilter] = useState<string>('todos');
    const [selectedServiceFilter, setSelectedServiceFilter] = useState<string>('todos');
    const [selectedAtmForEdit, setSelectedAtmForEdit] = useState<ATM | null>(null);
    const [isCreateMode, setIsCreateMode] = useState(false);
    const [sheetCollapsed, setSheetCollapsed] = useState(false);
    const [pickMapMode, setPickMapMode] = useState(false);
    const [pickedLocation, setPickedLocation] = useState<[number, number] | null>(null);

    // Form inputs for Create / Edit — use strings so number inputs are freely editable
    const [formCodigo, setFormCodigo] = useState('');
    const [formNombre, setFormNombre] = useState('');
    const [formLatitud, setFormLatitud] = useState<string>('-0.1807');
    const [formLongitud, setFormLongitud] = useState<string>('-78.4678');
    const [formEstado, setFormEstado] = useState('Activo');
    const [formSaldo, setFormSaldo] = useState<string>('10000');
    const [formTipo, setFormTipo] = useState('Fijo');
    const [formServicios, setFormServicios] = useState<string[]>([]);

    // --- HISTORY STATE ---
    const [historyList, setHistoryList] = useState<HistoryEntry[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    // --- ADMIN STATE ---
    const [seedLoading, setSeedLoading] = useState(false);
    const [seedSuccessMsg, setSeedSuccessMsg] = useState<string | null>(null);

    const defaultCenter: [number, number] = [-0.1807, -78.4678]; // Quito, Ecuador

    // Validate stored user on mount
    useEffect(() => {
        const stored = localStorage.getItem('currentUser');
        if (stored) {
            const parsed = JSON.parse(stored);
            getUserHistory(parsed.id)
                .then(() => {
                    setCurrentUser(parsed);
                })
                .catch(() => {
                    localStorage.removeItem('currentUser');
                    setCurrentUser(null);
                })
                .finally(() => setValidatingUser(false));
        } else {
            setValidatingUser(false);
        }
    }, []);

    // Load all ATMs on mount for map display
    useEffect(() => {
        getAllATMs()
            .then(data => setAtmsList(data))
            .catch(err => console.warn('Error cargando cajeros para el mapa:', err));
    }, []);

    // Initial load map centering
    useEffect(() => {
        if (location && !atm && !loading) {
            setMapCenter([location.latitude, location.longitude]);
        }
    }, [location]);

    // Fetch history when tab is opened
    useEffect(() => {
        if (currentUser && activeTab === 'history') {
            loadHistory();
        }
    }, [activeTab, currentUser]);

    // Fetch ATMs when tab is opened — only admins can access this tab
    useEffect(() => {
        if (currentUser && activeTab === 'cajeros') {
            if (!currentUser.es_admin) {
                setActiveTab('locator');
                return;
            }
            loadATMs();
        }
    }, [activeTab, currentUser]);

    const loadATMs = async () => {
        setAtmsLoading(true);
        try {
            const data = await getAllATMs();
            setAtmsList(data);
        } catch (err) {
            console.error('Error cargando cajeros:', err);
        } finally {
            setAtmsLoading(false);
        }
    };

    const loadHistory = async () => {
        if (!currentUser) return;
        setHistoryLoading(true);
        try {
            const data = await getUserHistory(currentUser.id);
            setHistoryList(data);
        } catch (err) {
            console.error('Error cargando historial:', err);
        } finally {
            setHistoryLoading(false);
        }
    };

    // --- AUTHENTICATION HANDLERS ---
    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setAuthError(null);
        setAuthLoading(true);
        setPickMapMode(false);
        setPickedLocation(null);
        setSheetCollapsed(false);

        try {
            if (isLoginTab) {
                const user = await loginUser({ username: authUsername, password: authPassword });
                localStorage.setItem('currentUser', JSON.stringify(user));
                setCurrentUser(user);
                await logUserHistory(user.id, "Inicio de Sesión", "El usuario inició sesión en el dispositivo móvil");
            } else {
                if (!authEmail || !authNombre) {
                    throw new Error("Por favor completa todos los campos.");
                }
                const user = await registerUser({
                    username: authUsername,
                    password: authPassword,
                    email: authEmail,
                    nombre: authNombre
                });
                localStorage.setItem('currentUser', JSON.stringify(user));
                setCurrentUser(user);
                await logUserHistory(user.id, "Registro de Usuario", "Nuevo usuario registrado exitosamente");
            }
            // Limpiar campos
            setAuthUsername('');
            setAuthPassword('');
            setAuthEmail('');
            setAuthNombre('');
        } catch (err: any) {
            setAuthError(err.response?.data?.detail || err.message || 'Error en la autenticación');
        } finally {
            setAuthLoading(false);
        }
    };

    const handleLogout = async () => {
        if (currentUser) {
            try {
                await logUserHistory(currentUser.id, "Cierre de Sesión", "El usuario cerró sesión voluntariamente");
            } catch (e) {
                console.error(e);
            }
        }
        localStorage.removeItem('currentUser');
        setCurrentUser(null);
        setActiveTab('locator');
        setAtm(null);
        setSelectedAtmForEdit(null);
        setIsCreateMode(false);
    };

    // --- SEED DATABASE HANDLER ---
    const handleSeed = async () => {
        setSeedLoading(true);
        setSeedSuccessMsg(null);
        try {
            const res = await seedDatabase();
            setSeedSuccessMsg(res.message);
            if (currentUser) {
                await logUserHistory(currentUser.id, "Reestablecimiento de Base Datos", "Se ejecutó el sembrado de datos en Neo4j.");
            }
        } catch (err: any) {
            alert(err.response?.data?.detail || "Error al sembrar la base de datos");
        } finally {
            setSeedLoading(false);
        }
    };

    // --- LOCATOR TAB HANDLER ---
    const handleLocate = async () => {
        if (!location) {
            getLocation();
            return;
        }

        setLoading(true);
        setApiError(null);
        try {
            const nearestAtm = await getNearestATM(location);
            setAtm(nearestAtm);
            setMapCenter([nearestAtm.latitud - 0.002, nearestAtm.longitud]);
            if (currentUser) {
                await logUserHistory(
                    currentUser.id, 
                    "Búsqueda Cajero", 
                    `Buscó el cajero más cercano. Encontrado: ${nearestAtm.nombre_ubicacion} a ${(nearestAtm.distancia_metros / 1000).toFixed(2)} km`
                );
            }
        } catch (err: any) {
            setApiError(err.response?.data?.detail || 'No se encontraron cajeros cercanos en tu zona.');
        } finally {
            setLoading(false);
        }
    };

    const handleRecenter = () => {
        if (location) {
            setMapCenter([location.latitude, location.longitude]);
        } else {
            getLocation();
        }
    };

    const handleMapPick = (lat: number, lng: number) => {
        setFormLatitud(lat.toFixed(6));
        setFormLongitud(lng.toFixed(6));
        setPickedLocation([lat, lng]);
        setPickMapMode(false);
        setSheetCollapsed(false);
    };

    // --- GESTIÓN DE CAJEROS CRUD HANDLERS ---
    const handleCreateATM = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formCodigo || !formNombre) {
            alert('Por favor complete el código y nombre del cajero.');
            return;
        }
        try {
            await createATM({
                codigo: formCodigo,
                nombre_ubicacion: formNombre,
                latitud: parseFloat(formLatitud),
                longitud: parseFloat(formLongitud),
                estado: formEstado,
                saldo_disponible: parseFloat(formSaldo),
                tipo: formTipo,
                servicios_ofrecidos: formServicios
            });
            if (currentUser) {
                await logUserHistory(currentUser.id, "Creación Cajero", `Creó un nuevo cajero: ${formNombre} (${formCodigo})`);
            }
            alert('Cajero creado con éxito');
            setIsCreateMode(false);
            setPickMapMode(false);
            setPickedLocation(null);
            resetForm();
            loadATMs();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error al crear el cajero');
        }
    };

    const handleUpdateATM = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedAtmForEdit) return;
        try {
            await updateATM(selectedAtmForEdit.id, {
                codigo: formCodigo,
                nombre_ubicacion: formNombre,
                latitud: parseFloat(formLatitud),
                longitud: parseFloat(formLongitud),
                estado: formEstado,
                saldo_disponible: parseFloat(formSaldo),
                tipo: formTipo,
                servicios_ofrecidos: formServicios
            });
            if (currentUser) {
                await logUserHistory(currentUser.id, "Edición Cajero", `Editó el cajero: ${formNombre} (${formCodigo})`);
            }
            alert('Cajero actualizado con éxito');
            setSelectedAtmForEdit(null);
            setPickMapMode(false);
            setPickedLocation(null);
            resetForm();
            loadATMs();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error al actualizar el cajero');
        }
    };

    const handleDeleteATM = async (id: string, nombre: string) => {
        if (!window.confirm(`¿Estás seguro de que deseas eliminar el cajero ${nombre}?`)) {
            return;
        }
        try {
            await deleteATM(id);
            if (currentUser) {
                await logUserHistory(currentUser.id, "Eliminación Cajero", `Eliminó el cajero: ${nombre}`);
            }
            alert('Cajero eliminado con éxito');
            loadATMs();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error al eliminar el cajero');
        }
    };

    const resetForm = () => {
        setFormCodigo('');
        setFormNombre('');
        setFormLatitud(String(location?.latitude ?? -0.1807));
        setFormLongitud(String(location?.longitude ?? -78.4678));
        setFormEstado('Activo');
        setFormSaldo('10000');
        setFormTipo('Fijo');
        setFormServicios([]);
    };

    const startEdit = (atmItem: ATM) => {
        setSelectedAtmForEdit(atmItem);
        setIsCreateMode(false);
        setFormCodigo(atmItem.codigo);
        setFormNombre(atmItem.nombre_ubicacion);
        setFormLatitud(String(atmItem.latitud));
        setFormLongitud(String(atmItem.longitud));
        setFormEstado(atmItem.estado);
        setFormSaldo(String(atmItem.saldo_disponible));
        setFormTipo(atmItem.tipo);
        setFormServicios(atmItem.servicios_ofrecidos || []);
    };

    // --- RENDER PIECES ---
    if (validatingUser) {
        return (
            <div className="auth-overlay">
                <div className="auth-card" style={{ alignItems: 'center', textAlign: 'center' }}>
                    <Loader2 className="animate-spin" size={32} color="#008A4B" />
                    <p style={{ color: '#a0aec0', marginTop: '1rem' }}>Validando sesión...</p>
                </div>
            </div>
        );
    }

    if (!currentUser) {
        return (
            <div className="auth-overlay">
                <div className="auth-card">
                    <div className="auth-header">
                        <h2 style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: '#008A4B' }}>
                            <Sparkles /> Produbanco
                        </h2>
                        <p>{isLoginTab ? 'Ingresa tus credenciales para continuar' : 'Crea tu cuenta de servicios bancarios'}</p>
                    </div>

                    {authError && (
                        <div style={{ color: '#ff6b6b', background: 'rgba(255,107,107,0.1)', padding: '0.8rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <AlertCircle size={16} /> {authError}
                        </div>
                    )}

                    <form className="auth-form" onSubmit={handleAuth}>
                        {!isLoginTab && (
                            <div className="form-group">
                                <label htmlFor="auth-name">Nombre Completo</label>
                                <input 
                                    id="auth-name"
                                    type="text" 
                                    className="form-input" 
                                    placeholder="Ej. Juan Pérez" 
                                    value={authNombre}
                                    onChange={(e) => setAuthNombre(e.target.value)}
                                    required
                                />
                            </div>
                        )}
                        
                        <div className="form-group">
                            <label htmlFor="auth-user">Usuario</label>
                            <input 
                                id="auth-user"
                                type="text" 
                                className="form-input" 
                                placeholder="Ej. juan12" 
                                value={authUsername}
                                onChange={(e) => setAuthUsername(e.target.value)}
                                required
                            />
                        </div>

                        {!isLoginTab && (
                            <div className="form-group">
                                <label htmlFor="auth-email">Correo Electrónico</label>
                                <input 
                                    id="auth-email"
                                    type="email" 
                                    className="form-input" 
                                    placeholder="Ej. juan@mail.com" 
                                    value={authEmail}
                                    onChange={(e) => setAuthEmail(e.target.value)}
                                    required
                                />
                            </div>
                        )}

                        <div className="form-group">
                            <label htmlFor="auth-pass">Contraseña</label>
                            <input 
                                id="auth-pass"
                                type="password" 
                                className="form-input" 
                                placeholder="******" 
                                value={authPassword}
                                onChange={(e) => setAuthPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button type="submit" className="btn-primary" style={{ marginTop: '0.5rem' }} disabled={authLoading}>
                            {authLoading ? (
                                <><Loader2 className="animate-spin" size={18} /> Procesando...</>
                            ) : (
                                isLoginTab ? 'Iniciar Sesión' : 'Registrarse'
                            )}
                        </button>
                    </form>

                    <div className="auth-toggle" onClick={() => { setIsLoginTab(!isLoginTab); setAuthError(null); }}>
                        {isLoginTab ? (
                            <>¿No tienes cuenta? ¡Registrate <span>aquí</span>!</>
                        ) : (
                            <>¿Ya tienes cuenta? Inicia sesión <span>aquí</span></>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ height: '100%', width: '100%', position: 'relative', display: 'flex', flexDirection: 'column' }}>
            {/* Top Bar */}
            <div className="top-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.8rem 1rem' }}>
                <h1 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 'bold' }}>Localizador Produbanco</h1>
                <span style={{ fontSize: '0.85rem', color: '#ccc', fontStyle: 'italic' }}>Hola, {currentUser.nombre.split(' ')[0]}</span>
            </div>

            {/* Main Interactive Screen */}
            <div className="map-container" style={{ position: 'relative', flexGrow: 1 }}>
                
                {/* LEAFLET MAP WORKSPACE */}
                <MapContainer 
                    center={defaultCenter} 
                    zoom={13} 
                    zoomControl={false}
                    style={{ height: '100%', width: '100%' }}
                >
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        attribution='&copy; OpenStreetMap'
                    />
                    <MapUpdater center={mapCenter} />
                    <MapClickHandler enabled={pickMapMode} onPick={handleMapPick} />

                    {/* User GPS location */}
                    {location && (
                        <Marker position={[location.latitude, location.longitude]} icon={userIcon}>
                            <Popup>Tu ubicación actual</Popup>
                        </Marker>
                    )}

                    {/* Nearest ATM marker (Tab Localizador) */}
                    {activeTab === 'locator' && atm && (
                        <Marker position={[atm.latitud, atm.longitud]} icon={atmIcon}>
                            <Popup>
                                <strong>{atm.nombre_ubicacion}</strong><br/>
                                {atm.tipo} - Saldo: ${atm.saldo_disponible}<br/>
                                A {(atm.distancia_metros / 1000).toFixed(2)} km<br/>
                                <button 
                                    onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${atm.latitud},${atm.longitud}`)}
                                    style={{marginTop:'6px', padding:'6px 12px', background:'#008A4B', color:'#fff', border:'none', borderRadius:'6px', cursor:'pointer', fontSize:'0.8rem', fontWeight:600}}
                                >
                                    Abrir en Google Maps
                                </button>
                            </Popup>
                        </Marker>
                    )}

                    {/* All ATMs markers (always visible on map) */}
                    {atmsList.map((atmItem) => (
                        <Marker 
                            key={atmItem.id} 
                            position={[atmItem.latitud, atmItem.longitud]} 
                            icon={atmItem.tipo === 'Móvil' ? mobileAtmIcon : atmIcon}
                        >
                            <Popup>
                                <strong>{atmItem.nombre_ubicacion}</strong><br/>
                                Código: {atmItem.codigo}<br/>
                                Tipo: {atmItem.tipo} ({atmItem.estado})<br/>
                                Saldo: ${atmItem.saldo_disponible}<br/>
                                Servicios: {atmItem.servicios_ofrecidos?.join(', ')}<br/>
                                <button 
                                    onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${atmItem.latitud},${atmItem.longitud}`)}
                                    style={{marginTop:'6px', padding:'6px 12px', background:'#008A4B', color:'#fff', border:'none', borderRadius:'6px', cursor:'pointer', fontSize:'0.8rem', fontWeight:600}}
                                >
                                    Abrir en Google Maps
                                </button>
                            </Popup>
                        </Marker>
                    ))}

                    {/* Picked location marker (when creating/editing ATM) */}
                    {pickedLocation && (
                        <Marker position={pickedLocation} icon={userIcon}>
                            <Popup>Ubicación seleccionada para el cajero</Popup>
                        </Marker>
                    )}
                </MapContainer>

                {/* FAB Recenter Button */}
                {(activeTab === 'locator' || activeTab === 'cajeros') && (
                    <button className="fab-recenter" onClick={handleRecenter} title="Mi ubicación">
                        <LocateFixed size={22} />
                    </button>
                )}

                {/* Tab specific overlay panels */}
                {!sheetCollapsed && (
                <div className="bottom-sheet-wrapper">
                    
                    <button className="sheet-close-btn" onClick={() => setSheetCollapsed(true)} title="Cerrar panel">
                        <X size={16} />
                    </button>

                    {/* TAB 1: LOCALIZADOR BANCO */}
                    {activeTab === 'locator' && (
                        <div className="bottom-sheet">
                            <div className="sheet-handle"></div>
                            
                            {error && (
                                <div style={{ color: '#d93025', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                                    <AlertCircle size={18} /> GPS Desactivado: {error}
                                </div>
                            )}
                            {apiError && (
                                <div style={{ color: '#d93025', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                                    <AlertCircle size={18} /> {apiError}
                                </div>
                            )}

                            {!atm ? (
                                <>
                                    <h2 style={{ margin: 0, color: '#003366', fontSize: '1.15rem', fontWeight: 700 }}>
                                        Encuentra tu Cajero más Cercano
                                    </h2>
                                    <p style={{ margin: 0, color: '#555', fontSize: '0.85rem' }}>
                                        Localiza de forma segura cajeros automáticos del banco Produbanco.
                                    </p>
                                    <button className="btn-primary" onClick={handleLocate} disabled={loading}>
                                        {loading ? <><Loader2 className="animate-spin" size={18} /> Buscando...</> : 'Buscar Cajero Fijo'}
                                    </button>
                                </>
                            ) : (
                                <div className="atm-info">
                                    <h3>{atm.nombre_ubicacion}</h3>
                                    <p>
                                        <Navigation size={15} color="#008A4B" /> 
                                        A {(atm.distancia_metros / 1000).toFixed(2)} km de ti
                                    </p>
                                    <div style={{ marginTop: '0.4rem', marginBottom: '0.6rem' }}>
                                        <span className={`status-badge ${atm.estado.toLowerCase() === 'activo' ? 'status-active' : 'status-inactive'}`}>
                                            {atm.estado}
                                        </span>
                                        <span style={{ fontSize: '0.8rem', color: '#777', marginLeft: '0.8rem' }}>
                                            Disponible: ${atm.saldo_disponible}
                                        </span>
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.8rem' }}>
                                        {atm.servicios_ofrecidos.map((s, idx) => (
                                            <span key={idx} style={{ background: '#edf2f7', color: '#4a5568', padding: '3px 7px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 500 }}>
                                                {s}
                                            </span>
                                        ))}
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button className="btn-primary" style={{ flex: 2, padding: '0.7rem' }} onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${atm.latitud},${atm.longitud}`)}>
                                            Trazar Ruta (Google Maps)
                                        </button>
                                        <button className="btn-secondary" style={{ flex: 1, padding: '0.7rem', border: '1px solid #ccc', background: 'none', borderRadius: '8px', cursor: 'pointer' }} onClick={() => setAtm(null)}>
                                            Cerrar
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* TAB 2: GESTIÓN DE CAJEROS (CRUD + CONSULTAS) */}
                    {activeTab === 'cajeros' && (
                        <div className="bottom-sheet" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
                            <div className="sheet-handle"></div>
                            
                            <div className="tab-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <h2 style={{ margin: 0, color: '#003366', fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <Database color="#008A4B" /> Gestión de Cajeros
                                </h2>
                                {!isCreateMode && !selectedAtmForEdit && (
                                    <button 
                                        className="btn-primary" 
                                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', width: 'auto' }}
                                        onClick={() => { setIsCreateMode(true); resetForm(); }}
                                    >
                                        + Nuevo Cajero
                                    </button>
                                )}
                            </div>

                            {/* CREATE OR EDIT FORM */}
                            {(isCreateMode || selectedAtmForEdit) && (
                                <form onSubmit={isCreateMode ? handleCreateATM : handleUpdateATM} className="crud-form" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', background: '#f7fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1rem' }}>
                                    <h3 style={{ margin: 0, color: '#003366', fontSize: '1rem' }}>
                                        {isCreateMode ? 'Crear Nuevo Cajero' : `Editar Cajero: ${formCodigo}`}
                                    </h3>
                                    
                                    <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
                                        <div className="form-group">
                                            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Código</label>
                                            <input 
                                                type="text" 
                                                className="form-input" 
                                                value={formCodigo} 
                                                onChange={(e) => setFormCodigo(e.target.value)} 
                                                placeholder="Ej. ATMF-100" 
                                                required 
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Nombre / Ubicación</label>
                                            <input 
                                                type="text" 
                                                className="form-input" 
                                                value={formNombre} 
                                                onChange={(e) => setFormNombre(e.target.value)} 
                                                placeholder="Ej. Cajero Supermaxi" 
                                                required 
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Latitud</label>
                                            <input 
                                                type="number" 
                                                step="any" 
                                                className="form-input" 
                                                value={formLatitud} 
                                                onChange={(e) => setFormLatitud(e.target.value)} 
                                                placeholder="Ej. -0.1807"
                                                required 
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Longitud</label>
                                            <input 
                                                type="number" 
                                                step="any" 
                                                className="form-input" 
                                                value={formLongitud} 
                                                onChange={(e) => setFormLongitud(e.target.value)} 
                                                placeholder="Ej. -78.4678"
                                                required 
                                            />
                                        </div>
                                    </div>

                                    {pickMapMode ? (
                                        <div className="pick-map-banner">
                                            <Crosshair size={18} />
                                            <p>Toca en el mapa para seleccionar la ubicación del cajero</p>
                                            <button onClick={() => { setPickMapMode(false); setPickedLocation(null); }}>Cancelar</button>
                                        </div>
                                    ) : (
                                        <button 
                                            type="button" 
                                            style={{ background: '#edf2f7', border: '1px dashed #003366', borderRadius: '8px', padding: '0.6rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', fontSize: '0.85rem', fontWeight: 600, color: '#003366', width: '100%' }}
                                            onClick={() => { setPickMapMode(true); setSheetCollapsed(true); }}
                                        >
                                            <MapPin size={16} /> Seleccionar ubicación en el mapa
                                        </button>
                                    )}

                                    <div className="form-group">
                                        <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Saldo Disponible ($)</label>
                                        <input 
                                            type="number" 
                                            className="form-input" 
                                            value={formSaldo} 
                                            onChange={(e) => setFormSaldo(e.target.value)} 
                                            placeholder="Ej. 10000"
                                            required 
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Tipo</label>
                                        <select className="form-input" value={formTipo} onChange={(e) => setFormTipo(e.target.value)}>
                                            <option value="Fijo">Fijo</option>
                                            <option value="Móvil">Móvil</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Estado</label>
                                        <select className="form-input" value={formEstado} onChange={(e) => setFormEstado(e.target.value)}>
                                            <option value="Activo">Activo</option>
                                            <option value="Inactivo">Inactivo</option>
                                        </select>
                                    </div>

                                    <div className="form-group">
                                        <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Servicios Ofrecidos</label>
                                        <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
                                            {["Retiro", "Depósito", "Consulta de Saldo", "Pago de Servicios"].map((service) => {
                                                const checked = formServicios.includes(service);
                                                return (
                                                    <label key={service} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem', cursor: 'pointer' }}>
                                                        <input 
                                                            type="checkbox" 
                                                            checked={checked} 
                                                            onChange={() => {
                                                                if (checked) {
                                                                    setFormServicios(formServicios.filter(s => s !== service));
                                                                } else {
                                                                    setFormServicios([...formServicios, service]);
                                                                }
                                                            }} 
                                                        />
                                                        {service}
                                                    </label>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                                        <button type="submit" className="btn-primary" style={{ flex: 1, padding: '0.5rem' }}>
                                            {isCreateMode ? 'Guardar Cajero' : 'Actualizar Cajero'}
                                        </button>
                                        <button 
                                            type="button" 
                                            className="btn-secondary" 
                                            style={{ border: '1px solid #ccc', padding: '0.5rem', background: '#fff', color: '#333' }}
                                            onClick={() => { setIsCreateMode(false); setSelectedAtmForEdit(null); setPickMapMode(false); setPickedLocation(null); resetForm(); }}
                                        >
                                            Cancelar
                                        </button>
                                    </div>
                                </form>
                            )}

                            {/* FILTERS AND SEARCH PANEL (CONSULTAS) */}
                            {!isCreateMode && !selectedAtmForEdit && (
                                <div className="filters-panel" style={{ background: '#f7fafc', padding: '0.8rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                    <div style={{ position: 'relative' }}>
                                        <input 
                                            type="text" 
                                            className="form-input" 
                                            placeholder="Buscar por código o nombre..." 
                                            value={searchTerm} 
                                            onChange={(e) => setSearchTerm(e.target.value)} 
                                            style={{ paddingLeft: '0.8rem' }}
                                        />
                                    </div>
                                    <div className="filter-selects" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.4rem' }}>
                                        <select className="form-input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ padding: '0.3rem', fontSize: '0.75rem' }}>
                                            <option value="todos">Todos los Estados</option>
                                            <option value="Activo">Activo</option>
                                            <option value="Inactivo">Inactivo</option>
                                        </select>
                                        <select className="form-input" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} style={{ padding: '0.3rem', fontSize: '0.75rem' }}>
                                            <option value="todos">Todos los Tipos</option>
                                            <option value="Fijo">Fijo</option>
                                            <option value="Móvil">Móvil</option>
                                        </select>
                                        <select className="form-input" value={selectedServiceFilter} onChange={(e) => setSelectedServiceFilter(e.target.value)} style={{ padding: '0.3rem', fontSize: '0.75rem' }}>
                                            <option value="todos">Todos los Servicios</option>
                                            <option value="Retiro">Retiro</option>
                                            <option value="Depósito">Depósito</option>
                                            <option value="Consulta de Saldo">Consulta</option>
                                            <option value="Pago de Servicios">Pago Servicios</option>
                                        </select>
                                    </div>
                                </div>
                            )}

                            {/* LIST / TABLE OF CAJEROS */}
                            {!isCreateMode && !selectedAtmForEdit && (
                                <div className="cajeros-list-wrapper" style={{ maxHeight: '40vh', overflowY: 'auto' }}>
                                    {atmsLoading ? (
                                        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                            <Loader2 className="animate-spin" color="#003366" size={24} />
                                        </div>
                                    ) : (
                                        (() => {
                                            const filteredAtms = atmsList.filter(atmItem => {
                                                const matchesSearch = atmItem.nombre_ubicacion.toLowerCase().includes(searchTerm.toLowerCase()) || 
                                                                      atmItem.codigo.toLowerCase().includes(searchTerm.toLowerCase());
                                                const matchesStatus = statusFilter === 'todos' || atmItem.estado === statusFilter;
                                                const matchesType = typeFilter === 'todos' || atmItem.tipo === typeFilter;
                                                const matchesService = selectedServiceFilter === 'todos' || (atmItem.servicios_ofrecidos && atmItem.servicios_ofrecidos.includes(selectedServiceFilter));
                                                return matchesSearch && matchesStatus && matchesType && matchesService;
                                            });

                                            if (filteredAtms.length === 0) {
                                                return (
                                                    <div style={{ textAlign: 'center', padding: '2rem', color: '#718096', fontSize: '0.9rem' }}>
                                                        No se encontraron cajeros que coincidan con la búsqueda.
                                                    </div>
                                                );
                                            }

                                            return (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                                    {filteredAtms.map((atmItem) => (
                                                        <div 
                                                            key={atmItem.id} 
                                                            style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.8rem', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', cursor: 'pointer' }}
                                                            onClick={() => setMapCenter([atmItem.latitud - 0.002, atmItem.longitud])}
                                                            title="Haz click para centrar en el mapa"
                                                        >
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', flex: 1 }}>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#2d3748' }}>{atmItem.nombre_ubicacion}</span>
                                                                    <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#718096', background: '#edf2f7', padding: '1px 5px', borderRadius: '3px' }}>{atmItem.codigo}</span>
                                                                </div>
                                                                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
                                                                    <span className={`status-badge ${atmItem.estado.toLowerCase() === 'activo' ? 'status-active' : 'status-inactive'}`} style={{ fontSize: '0.7rem', padding: '1px 5px' }}>
                                                                        {atmItem.estado}
                                                                    </span>
                                                                    <span style={{ fontSize: '0.75rem', color: '#4a5568', background: '#e2e8f0', padding: '1px 5px', borderRadius: '3px' }}>
                                                                        {atmItem.tipo}
                                                                    </span>
                                                                    <span style={{ fontSize: '0.75rem', color: '#718096' }}>
                                                                        Saldo: ${atmItem.saldo_disponible}
                                                                    </span>
                                                                </div>
                                                                <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap', marginTop: '0.3rem' }}>
                                                                    {atmItem.servicios_ofrecidos?.map((s, idx) => (
                                                                        <span key={idx} style={{ background: '#edf2f7', color: '#4a5568', padding: '1px 4px', borderRadius: '3px', fontSize: '0.65rem' }}>
                                                                            {s}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                            <div style={{ display: 'flex', gap: '0.3rem', marginLeft: '0.5rem' }} onClick={(e) => e.stopPropagation()}>
                                                                <button 
                                                                    className="btn-secondary" 
                                                                    style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', border: '1px solid #cbd5e0', background: '#fff', color: '#4a5568', cursor: 'pointer' }}
                                                                    onClick={() => startEdit(atmItem)}
                                                                >
                                                                    Editar
                                                                </button>
                                                                <button 
                                                                    className="btn-primary" 
                                                                    style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', background: '#e53e3e', color: '#fff', cursor: 'pointer' }}
                                                                    onClick={() => handleDeleteATM(atmItem.id, atmItem.nombre_ubicacion)}
                                                                >
                                                                    Eliminar
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            );
                                        })()
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* TAB 3: TIMELINE DE HISTORIAL DE USO */}
                    {activeTab === 'history' && (
                        <div className="bottom-sheet" style={{ maxHeight: '75vh' }}>
                            <div className="sheet-handle"></div>
                            <div className="tab-header">
                                <h2>Historial de Actividad</h2>
                                <button style={{ background: 'none', border: 'none', color: '#008A4B', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }} onClick={loadHistory}>
                                    Actualizar
                                </button>
                            </div>

                            {historyLoading ? (
                                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                    <Loader2 className="animate-spin" color="#003366" size={24} />
                                </div>
                            ) : historyList.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#718096', fontSize: '0.9rem' }}>
                                    No hay registros de uso en esta cuenta todavía.
                                </div>
                            ) : (
                                <div className="timeline">
                                    {historyList.map((item) => {
                                        // Formatear fecha legible
                                        const cleanDate = item.fecha.split('.')[0].replace('T', ' ');
                                        return (
                                            <div className="timeline-item" key={item.id}>
                                                <div className="timeline-badge">
                                                    {item.tipo_accion.includes("Sesión") ? <UserIcon size={14} /> : item.tipo_accion.includes("Cajero") ? <Database size={14} /> : <HistoryIcon size={14} />}
                                                </div>
                                                <div className="timeline-content">
                                                    <div className="timeline-header">
                                                        <span className="timeline-title">{item.tipo_accion}</span>
                                                        <span className="timeline-time">{cleanDate}</span>
                                                    </div>
                                                    <p className="timeline-desc">{item.descripcion}</p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    {/* TAB 4: CONFIGURACIÓN DE CUENTA / ADMIN SEEDER */}
                    {activeTab === 'account' && (
                        <div className="bottom-sheet" style={{ maxHeight: '70vh' }}>
                            <div className="sheet-handle"></div>
                            <div className="tab-header">
                                <h2>Mi Cuenta</h2>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                                {/* User Details Card */}
                                <div style={{ background: '#f7fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                                    <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#003366', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.2rem' }}>
                                        {currentUser.nombre.charAt(0)}
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <span style={{ fontWeight: 600, color: '#2d3748', fontSize: '0.95rem' }}>{currentUser.nombre}</span>
                                        <span style={{ fontSize: '0.8rem', color: '#718096' }}>@{currentUser.username} • {currentUser.email}</span>
                                    </div>
                                </div>

                                {/* Administrative Database Seeder */}
                                <div className="admin-card">
                                    <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#003366', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700 }}>
                                        <Database size={16} /> Zona Administrativa (Neo4j)
                                    </h3>
                                    <p style={{ margin: 0, fontSize: '0.75rem', color: '#4a5568', lineHeight: 1.4 }}>
                                        ¿Base de datos de Neo4j vacía o desconfigurada? Genera cajeros fijos, cajeros móviles, servicios bancarios y relaciones en Quito con un solo click.
                                    </p>
                                    
                                    {seedSuccessMsg && (
                                        <span style={{ fontSize: '0.75rem', color: '#1e8e3e', fontWeight: 600 }}>
                                            ✓ {seedSuccessMsg}
                                        </span>
                                    )}

                                    <button 
                                        className="btn-primary" 
                                        style={{ background: '#4a5568', padding: '0.6rem', fontSize: '0.85rem', display: 'flex', gap: '0.4rem', justifyContent: 'center', width: 'fit-content' }}
                                        onClick={handleSeed}
                                        disabled={seedLoading}
                                    >
                                        {seedLoading ? <><Loader2 className="animate-spin" size={14} /> Generando...</> : 'Generar / Resetear Datos'}
                                    </button>
                                </div>

                                {/* Logout button */}
                                <button className="btn-primary" style={{ background: '#d93025', boxShadow: 'none', display: 'flex', gap: '0.5rem', justifyContent: 'center' }} onClick={handleLogout}>
                                    <LogOut size={18} /> Cerrar Sesión
                                </button>
                            </div>
                        </div>
                    )}

                </div>
                )}
            </div>

            {sheetCollapsed && (
                <button className="sheet-reopen-btn" onClick={() => setSheetCollapsed(false)}>
                    <ChevronUp size={16} /> Abrir panel
                </button>
            )}
            <div className="bottom-nav">
                <button 
                    className={`nav-tab ${activeTab === 'locator' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('locator'); }}
                >
                    <MapPin size={22} />
                    <span>Localizador</span>
                </button>
                {currentUser?.es_admin && (
                <button 
                    className={`nav-tab ${activeTab === 'cajeros' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('cajeros'); }}
                >
                    <Database size={22} />
                    <span>Gestionar</span>
                </button>
                )}
                <button 
                    className={`nav-tab ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('history'); }}
                >
                    <HistoryIcon size={22} />
                    <span>Historial</span>
                </button>
                <button 
                    className={`nav-tab ${activeTab === 'account' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('account'); }}
                >
                    <UserIcon size={22} />
                    <span>Mi Cuenta</span>
                </button>
            </div>
        </div>
    );
}

export default App;
