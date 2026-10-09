import { useEffect, useState } from 'react';
import { Pressable, ScrollView, Text, TextInput, View } from 'react-native';

import type { SavedLocation } from '../types/hazard';
import { styles } from '../styles';
import { validateSavedLocation } from '../services/savedLocations';
import { validateApiBaseUrl } from '../services/settings';

type SavedLocationsScreenProps = {
  locations: SavedLocation[];
  apiBaseUrl: string;
  onSaveLocation: (location: Omit<SavedLocation, 'id'>) => Promise<void>;
  onDeleteLocation: (id: string) => Promise<void>;
  onSaveApiBaseUrl: (value: string) => Promise<void>;
};

export default function SavedLocationsScreen({
  locations,
  apiBaseUrl,
  onSaveLocation,
  onDeleteLocation,
  onSaveApiBaseUrl,
}: SavedLocationsScreenProps) {
  const [name, setName] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [radius, setRadius] = useState('25');
  const [locationError, setLocationError] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState(apiBaseUrl);
  const [apiUrlError, setApiUrlError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => setApiUrl(apiBaseUrl), [apiBaseUrl]);

  async function addLocation() {
    setLocationError(null);
    setSavedMessage(null);
    const location = {
      name,
      latitude: latitude.trim() ? Number(latitude) : Number.NaN,
      longitude: longitude.trim() ? Number(longitude) : Number.NaN,
      radius_km: radius.trim() ? Number(radius) : Number.NaN,
    };
    const validationError = validateSavedLocation(location);
    if (validationError !== null) {
      setLocationError(validationError);
      return;
    }

    try {
      await onSaveLocation(location);
      setName('');
      setLatitude('');
      setLongitude('');
      setRadius('25');
      setSavedMessage('Location saved on this device.');
    } catch {
      setLocationError('Could not save this location on the device. Please try again.');
    }
  }

  async function saveApiUrl() {
    setApiUrlError(null);
    setSavedMessage(null);
    const validationError = validateApiBaseUrl(apiUrl);
    if (validationError !== null) {
      setApiUrlError(validationError);
      return;
    }

    try {
      await onSaveApiBaseUrl(apiUrl);
      setSavedMessage('API URL saved on this device.');
    } catch {
      setApiUrlError('Could not save the API URL on this device. Please try again.');
    }
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Saved locations</Text>
      <Text style={styles.muted}>
        Enter coordinates and a radius. Location data stays on this device.
      </Text>

      {locations.map((location) => (
        <View key={location.id} style={styles.card}>
          <Text style={styles.body}>{location.name}</Text>
          <Text style={styles.muted}>
            {location.latitude}, {location.longitude} · within {location.radius_km} km
          </Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => void onDeleteLocation(location.id)}
            style={styles.secondaryButton}
          >
            <Text style={styles.dangerText}>Remove</Text>
          </Pressable>
        </View>
      ))}

      <View style={styles.card}>
        <Text style={styles.body}>Add a location</Text>
        <Text style={styles.label}>Name</Text>
        <TextInput
          accessibilityLabel="Location name"
          onChangeText={setName}
          placeholder="Home or work"
          style={styles.input}
          value={name}
        />
        <Text style={styles.label}>Latitude</Text>
        <TextInput
          accessibilityLabel="Latitude"
          keyboardType="decimal-pad"
          onChangeText={setLatitude}
          placeholder="14.5995"
          style={styles.input}
          value={latitude}
        />
        <Text style={styles.label}>Longitude</Text>
        <TextInput
          accessibilityLabel="Longitude"
          keyboardType="decimal-pad"
          onChangeText={setLongitude}
          placeholder="120.9842"
          style={styles.input}
          value={longitude}
        />
        <Text style={styles.label}>Alert radius (1–500 km)</Text>
        <TextInput
          accessibilityLabel="Alert radius in kilometers"
          keyboardType="decimal-pad"
          onChangeText={setRadius}
          style={styles.input}
          value={radius}
        />
        <Pressable accessibilityRole="button" onPress={() => void addLocation()} style={styles.actionButton}>
          <Text style={styles.actionText}>Save location</Text>
        </Pressable>
        {locationError ? <Text style={styles.error}>{locationError}</Text> : null}
      </View>

      <View style={styles.card}>
        <Text style={styles.body}>Hazard data API</Text>
        <Text style={styles.muted}>
          Enter a device-reachable URL ending in /api/v1.
        </Text>
        <TextInput
          accessibilityLabel="API base URL"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          onChangeText={setApiUrl}
          placeholder="http://192.168.1.20:8000/api/v1"
          style={styles.input}
          value={apiUrl}
        />
        <Pressable accessibilityRole="button" onPress={() => void saveApiUrl()} style={styles.actionButton}>
          <Text style={styles.actionText}>Save API URL</Text>
        </Pressable>
        {apiUrlError ? <Text style={styles.error}>{apiUrlError}</Text> : null}
      </View>

      {savedMessage ? <Text style={styles.success}>{savedMessage}</Text> : null}
    </ScrollView>
  );
}
