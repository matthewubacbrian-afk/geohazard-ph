import { Pressable, ScrollView, Text } from 'react-native';

import HazardMatchList from '../components/HazardMatchList';
import { registerForPushNotifications } from '../services/pushNotifications';
import { styles } from '../styles';
import type { NearbyScreenProps } from './NearbyHazardsScreen';

export default function AlertsScreen({
  matches,
  locations,
  hasLocations,
  isLoading,
  isOffline,
  errorMessage,
  isConfigured,
  onRefresh,
}: NearbyScreenProps) {
  const pushStatus = registerForPushNotifications();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Nearby alerts</Text>
      <Text style={styles.notice}>
        This in-app list checks for events when you refresh. Background push is {pushStatus.status}.
      </Text>
      {!isConfigured ? (
        <Text style={styles.notice}>Add the API URL in Saved locations to refresh hazard data.</Text>
      ) : null}
      {isOffline ? <Text style={styles.notice}>Offline · showing the last saved event data.</Text> : null}
      {isLoading ? <Text style={styles.muted}>Loading hazard events…</Text> : null}
      {errorMessage ? <Text accessibilityRole="alert" style={styles.error}>{errorMessage}</Text> : null}
      {!hasLocations ? <Text style={styles.body}>Save a location to create nearby alerts.</Text> : null}
      {hasLocations && matches.length === 0 && !isLoading && !errorMessage ? (
        <Text style={styles.body}>No events are within your saved radii.</Text>
      ) : null}
      {matches.length > 0 ? <HazardMatchList locations={locations} matches={matches} /> : null}
      <Pressable
        accessibilityRole="button"
        disabled={!isConfigured || isLoading}
        onPress={onRefresh}
        style={styles.secondaryButton}
      >
        <Text style={styles.secondaryText}>{isLoading ? 'Refreshing…' : 'Refresh events'}</Text>
      </Pressable>
    </ScrollView>
  );
}
