import { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import AlertsScreen from '../screens/AlertsScreen';
import NearbyHazardsScreen from '../screens/NearbyHazardsScreen';
import SavedLocationsScreen from '../screens/SavedLocationsScreen';
import { API_BASE_URL } from '../config';
import { isHazardEvent, loadEventFeed } from '../services/eventFeed';
import { loadSavedLocations, saveSavedLocations } from '../services/savedLocations';
import { loadApiBaseUrl, saveApiBaseUrl } from '../services/settings';
import { readOfflineValue } from '../services/offlineCache';
import { findNearbyHazards } from '../services/proximity';
import { ApiError } from '../services/api';
import { styles } from '../styles';
import type { HazardEvent, SavedLocation } from '../types/hazard';

type AppTab = 'Nearby' | 'Saved locations' | 'Alerts';
const TABS: AppTab[] = ['Nearby', 'Saved locations', 'Alerts'];
const LATEST_EVENTS_KEY = 'mobile.latestEvents';

export default function RootNavigator() {
  const [selectedTab, setSelectedTab] = useState<AppTab>('Nearby');
  const [apiBaseUrl, setApiBaseUrl] = useState(API_BASE_URL);
  const [locations, setLocations] = useState<SavedLocation[]>([]);
  const [events, setEvents] = useState<HazardEvent[]>([]);
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function restoreSavedState() {
      const results = await Promise.allSettled([
        loadApiBaseUrl(),
        loadSavedLocations(),
        readOfflineValue<unknown>(LATEST_EVENTS_KEY),
      ]);
      if (!isActive) return;

      const [apiUrlResult, locationsResult, eventsResult] = results;
      const restoredUrl = apiUrlResult.status === 'fulfilled' ? apiUrlResult.value : API_BASE_URL;
      const restoredLocations = locationsResult.status === 'fulfilled' ? locationsResult.value : [];
      const restoredEvents = eventsResult.status === 'fulfilled' && Array.isArray(eventsResult.value)
        ? eventsResult.value.filter(isHazardEvent)
        : [];

      setApiBaseUrl(restoredUrl);
      setLocations(restoredLocations);
      setEvents(restoredEvents);
      setIsOffline(restoredEvents.length > 0);
      if (results.some((result) => result.status === 'rejected')) {
        setStorageWarning('Some saved mobile data could not be read from this device.');
      }
      setIsReady(true);
    }

    void restoreSavedState();
    return () => {
      isActive = false;
    };
  }, []);

  const refreshEvents = useCallback(async (url = apiBaseUrl) => {
    if (!url.trim()) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const feed = await loadEventFeed(url);
      setEvents(feed.events);
      setIsOffline(feed.isOffline);
    } catch (error) {
      setIsOffline(true);
      setErrorMessage(error instanceof ApiError
        ? error.message
        : 'Could not save recent hazard data on this device.');
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    if (isReady && apiBaseUrl) void refreshEvents(apiBaseUrl);
  }, [apiBaseUrl, isReady, refreshEvents]);

  const matches = useMemo(() => findNearbyHazards(events, locations), [events, locations]);

  async function addLocation(input: Omit<SavedLocation, 'id'>) {
    const nextLocations = [...locations, {
      ...input,
      name: input.name.trim(),
      id: `location-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    }];
    try {
      await saveSavedLocations(nextLocations);
      setLocations(nextLocations);
      setStorageWarning(null);
    } catch {
      setStorageWarning('Could not save this location on the device. Please try again.');
      throw new Error('Could not save location');
    }
  }

  async function deleteLocation(id: string) {
    const nextLocations = locations.filter((location) => location.id !== id);
    try {
      await saveSavedLocations(nextLocations);
      setLocations(nextLocations);
      setStorageWarning(null);
    } catch {
      setStorageWarning('Could not update saved locations on this device. Please try again.');
    }
  }

  async function persistApiBaseUrl(value: string) {
    try {
      await saveApiBaseUrl(value);
      const normalized = value.trim().replace(/\/+$/, '');
      setApiBaseUrl(normalized);
      setStorageWarning(null);
    } catch {
      setStorageWarning('Could not save the API URL on this device. Please try again.');
      throw new Error('Could not save API URL');
    }
  }

  const screenProps = {
    matches,
    locations,
    hasLocations: locations.length > 0,
    isLoading,
    isOffline,
    errorMessage,
    isConfigured: Boolean(apiBaseUrl.trim()),
    onRefresh: () => void refreshEvents(),
  };

  return (
    <View style={styles.root}>
      {storageWarning ? <Text accessibilityRole="alert" style={styles.error}>{storageWarning}</Text> : null}
      {!isReady ? <Text style={styles.muted}>Loading saved mobile data…</Text> : null}
      {isReady && selectedTab === 'Nearby' ? <NearbyHazardsScreen {...screenProps} /> : null}
      {isReady && selectedTab === 'Saved locations' ? (
        <SavedLocationsScreen
          apiBaseUrl={apiBaseUrl}
          locations={locations}
          onDeleteLocation={deleteLocation}
          onSaveApiBaseUrl={persistApiBaseUrl}
          onSaveLocation={addLocation}
        />
      ) : null}
      {isReady && selectedTab === 'Alerts' ? <AlertsScreen {...screenProps} /> : null}
      <View style={styles.tabs}>
        {TABS.map((tab) => (
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ selected: selectedTab === tab }}
            key={tab}
            onPress={() => setSelectedTab(tab)}
            style={[styles.tab, selectedTab === tab && styles.activeTab]}
          >
            <Text style={[styles.tabText, selectedTab === tab && styles.activeTabText]}>{tab}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
