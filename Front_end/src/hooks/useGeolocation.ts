import { useState } from 'react';
import { UserLocation } from '../types';

export const useGeolocation = () => {
    const [location, setLocation] = useState<UserLocation | null>(null);
    const [error, setError] = useState<string | null>(null);

    const getLocation = () => {
        if (!navigator.geolocation) {
            setError('Geolocation is not supported by your browser');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLocation({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                });
                setError(null);
            },
            () => {
                setError('Unable to retrieve your location');
            }
        );
    };

    return { location, error, getLocation };
};
