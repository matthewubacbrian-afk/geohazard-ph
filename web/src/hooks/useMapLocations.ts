import { useEffect, useRef, useState } from 'react';

import {
  DEFAULT_RADIUS_KM, SAVED_LOCATIONS_KEY, readSavedLocations,
  type LocationPoint, type SavedLocation,
} from '../lib/savedLocations';

type LocationMode = 'idle' | 'locating' | 'picking';

export function useMapLocations() {
  const [point, setPoint] = useState<LocationPoint | null>(null);
  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM);
  const [mode, setMode] = useState<LocationMode>('idle');
  const [message, setMessage] = useState('');
  const [savedLocations, setSavedLocations] = useState(() => {
    try {
      return readSavedLocations();
    } catch {
      return [];
    }
  });
  const locationRequest = useRef(0);
  useEffect(() => () => { locationRequest.current += 1; }, []);

  function changeMode(nextMode: LocationMode) {
    locationRequest.current += 1;
    setMode(nextMode);
    setMessage('');
  }

  function selectPoint(nextPoint: LocationPoint | null) {
    changeMode('idle');
    setPoint(nextPoint);
  }

  function useCurrentLocation() {
    changeMode('locating');
    const request = locationRequest.current;
    if (!navigator.geolocation) {
      setMode('idle');
      setMessage('Device location is unavailable here. You can drop a pin on the map.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude, longitude } }) => {
        if (request === locationRequest.current) selectPoint({ latitude, longitude });
      },
      ({ code }) => {
        if (request !== locationRequest.current) return;
        setMode('idle');
        setMessage(code === 1
          ? 'Location permission was denied. You can drop a pin on the map.'
          : 'Could not get your device location. Try again or drop a pin on the map.');
      },
      { timeout: 10000 },
    );
  }

  function updateSavedLocations(update: (rows: SavedLocation[]) => SavedLocation[] | null) {
    try {
      const next = update(readSavedLocations());
      if (!next) return false;
      localStorage.setItem(SAVED_LOCATIONS_KEY, JSON.stringify(next));
      setSavedLocations(next);
      setMessage('');
      return true;
    } catch {
      setMessage('This browser could not update your saved locations.');
      return false;
    }
  }

  function saveLocation(value: string) {
    const name = value.trim();
    if (!point || !name) {
      setMessage('Enter a name for this location.');
      return false;
    }
    return updateSavedLocations((rows) => {
      if (rows.some((row) => row.name.toLowerCase() === name.toLowerCase())) {
        setMessage('You already have a location with that name.');
        return null;
      }
      return [...rows, { ...point, name, radius_km: radiusKm }];
    });
  }

  function openLocation({ latitude, longitude, radius_km }: SavedLocation) {
    setRadiusKm(radius_km);
    selectPoint({ latitude, longitude });
  }

  function removeLocation(name: string) {
    updateSavedLocations((rows) => rows.filter((row) => row.name !== name));
  }

  return {
    point, radiusKm, mode, message, savedLocations, setRadiusKm, changeMode,
    selectPoint, useCurrentLocation, saveLocation, openLocation, removeLocation,
  };
}
