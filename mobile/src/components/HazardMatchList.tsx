import { Text, View } from 'react-native';

import type { NearbyHazard, SavedLocation } from '../types/hazard';
import { styles } from '../styles';

type HazardMatchListProps = {
  matches: NearbyHazard[];
  locations: SavedLocation[];
};

export default function HazardMatchList({ matches, locations }: HazardMatchListProps) {
  const locationNames = new Map(locations.map((location) => [location.id, location.name]));

  return (
    <View>
      {matches.map(({ event, location_id, distance_km }) => (
        <View key={`${event.id}-${location_id}`} style={styles.card}>
          <Text style={styles.body}>{event.placeName}</Text>
          <Text style={styles.muted}>{locationNames.get(location_id) ?? 'Saved location'}</Text>
          <Text style={styles.muted}>
            {event.hazardType} · {event.source}
          </Text>
          <Text style={styles.muted}>
            {event.magnitude === null ? 'Magnitude not reported' : `Magnitude ${event.magnitude}`}
            {' · '}
            {distance_km < 1 ? `${Math.round(distance_km * 1000)} m` : `${distance_km.toFixed(1)} km`}
          </Text>
          <Text style={styles.muted}>{new Date(event.occurredAt).toLocaleString()}</Text>
        </View>
      ))}
    </View>
  );
}
