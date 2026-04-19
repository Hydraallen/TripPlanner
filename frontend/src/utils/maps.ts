export interface LatLng {
  latitude: number;
  longitude: number;
}

export function googleMapsSearchUrl(name: string, lat: number, lon: number): string {
  const params = new URLSearchParams({
    api: "1",
    query: name,
    ll: `${lat},${lon}`,
  });
  return `https://www.google.com/maps/search/?${params.toString()}`;
}

export function googleMapsDirectionsUrl(
  from: LatLng,
  to: LatLng,
  mode: "walking" | "transit" | "driving" = "walking",
): string {
  const params = new URLSearchParams({
    api: "1",
    origin: `${from.latitude},${from.longitude}`,
    destination: `${to.latitude},${to.longitude}`,
    travelmode: mode,
  });
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function extractWikipediaUrl(description: string | null): string | null {
  if (!description) return null;
  const match = description.match(/https?:\/\/[a-z]+\.wikipedia\.org\/wiki\/[^\s|]+/i);
  return match ? match[0] : null;
}
