import { Pressable, ScrollView, Text, View } from 'react-native';

import HazardMatchList from '../components/HazardMatchList';
import { styles } from '../styles';
import type { NearbyHazard, SavedLocation } from '../types/hazard';

export type NearbyScreenProps = {
  matches: NearbyHazard[];
  locations: SavedLocation[];
  hasLocations: boolean;
  isLoading: boolean;
  isOffline: boolean;
  errorMessage: string | null;
  isConfigured: boolean;
  onRefresh: () => void;
};

export default function NearbyHazardsScreen({
  matches,
  locations,
  hasLocations,
  isLoading,
  isOffline,
  errorMessage,
  isConfigured,
  onRefresh,
}: NearbyScreenProps) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Nearby hazards</Text>
      <Text style={styles.muted}>Events matched to your saved locations and radii.</Text>
      {!isConfigured ? (
        <Text style={styles.notice}>Add the API URL in Saved locations to refresh hazard data.</Text>
      ) : null}
      {isOffline ? <Text style={styles.notice}>Offline · showing the last saved event data.</Text> : null}
      {isLoading ? <Text style={styles.muted}>Loading hazard events…</Text> : null}
      {errorMessage ? <Text accessibilityRole="alert" style={styles.error}>{errorMessage}</Text> : null}
      {!hasLocations ? <Text style={styles.body}>Save a location to see nearby events.</Text> : null}
      {hasLocations && matches.length === 0 && !isLoading && !errorMessage ? (
        <Text style={styles.body}>No events are within your saved radii.</Text>
      ) : null}
      {matches.length > 0 ? <HazardMatchList locations={locations} matches={matches} /> : null}
      <View>
        <Pressable
          accessibilityRole="button"
          disabled={!isConfigured || isLoading}
          onPress={onRefresh}
          style={styles.secondaryButton}
        >
          <Text style={styles.secondaryText}>{isLoading ? 'Refreshing…' : 'Refresh events'}</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}
