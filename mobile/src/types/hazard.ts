export type HazardEvent = {
  id: string;
  hazardType: 'earthquake' | 'volcanic' | 'landslide';
  latitude: number;
  longitude: number;
  placeName: string;
};
