import axios from 'axios';
import { UserLocation, ATM, User, HistoryEntry } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'; // Puerto de API Business Rules

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getNearestATM = async (location: UserLocation): Promise<ATM> => {
    const response = await api.post<ATM>('/locator/nearest', {
        latitude: location.latitude,
        longitude: location.longitude,
        servicios_requeridos: []
    });
    return response.data;
};

// --- AUTHENTICATION ---
export const registerUser = async (userData: any): Promise<User> => {
    const response = await api.post<User>('/auth/register', userData);
    return response.data;
};

export const loginUser = async (credentials: any): Promise<User> => {
    const response = await api.post<User>('/auth/login', credentials);
    return response.data;
};

// --- DATABASE SEEDER ---
export const seedDatabase = async (): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/locator/seed');
    return response.data;
};

// --- USAGE HISTORY ---
export const logUserHistory = async (userId: string, tipo: string, desc: string): Promise<HistoryEntry | null> => {
    try {
        const response = await api.post<HistoryEntry>(`/historial/${userId}`, {
            tipo_accion: tipo,
            descripcion: desc
        });
        return response.data;
    } catch (err) {
        console.warn('Error al registrar historial (no crítico):', err);
        return null;
    }
};

export const getUserHistory = async (userId: string): Promise<HistoryEntry[]> => {
    const response = await api.get<HistoryEntry[]>(`/historial/${userId}`);
    return response.data;
};

// --- ATM CRUD OPERATIONS ---
export const getAllATMs = async (): Promise<ATM[]> => {
    const response = await api.get<ATM[]>('/cajeros');
    return response.data;
};

export const createATM = async (atmData: Omit<ATM, 'id' | 'distancia_metros'> & { servicios_ofrecidos: string[] }): Promise<ATM> => {
    const response = await api.post<ATM>('/cajeros', atmData);
    return response.data;
};

export const updateATM = async (atmId: string, atmData: Partial<ATM> & { servicios_ofrecidos?: string[] }): Promise<ATM> => {
    const response = await api.put<ATM>(`/cajeros/${atmId}`, atmData);
    return response.data;
};

export const deleteATM = async (atmId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/cajeros/${atmId}`);
    return response.data;
};
