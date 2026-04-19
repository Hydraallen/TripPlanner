import type { LatLng } from "./maps";

export interface RouteInfo {
  mode: "foot" | "car" | "bike";
  durationMinutes: number;
  distanceKm: number;
}

const OSRM_BASE = "https://router.project-osrm.org/route/v1";

const SPEED_KMH: Record<string, number> = {
  foot: 5.0,
  car: 30.0,
  bike: 15.0,
};

// Cache: "mode:lat1,lon1-lat2,lon2" → RouteInfo
const cache = new Map<string, RouteInfo>();

function cacheKey(from: LatLng, to: LatLng, mode: string): string {
  const k1 = `${from.latitude.toFixed(5)},${from.longitude.toFixed(5)}`;
  const k2 = `${to.latitude.toFixed(5)},${to.longitude.toFixed(5)}`;
  return `${mode}:${k1}-${k2}`;
}

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function fallbackEstimate(from: LatLng, to: LatLng, mode: "foot" | "car" | "bike"): RouteInfo {
  const dist = haversineKm(from.latitude, from.longitude, to.latitude, to.longitude);
  const speed = SPEED_KMH[mode];
  return {
    mode,
    durationMinutes: Math.round((dist / speed) * 60),
    distanceKm: Math.round(dist * 10) / 10,
  };
}

export async function fetchRoute(
  from: LatLng,
  to: LatLng,
  mode: "foot" | "car" | "bike",
): Promise<RouteInfo> {
  const key = cacheKey(from, to, mode);
  const cached = cache.get(key);
  if (cached) return cached;

  try {
    const url = `${OSRM_BASE}/${mode}/${from.longitude},${from.latitude};${to.longitude},${to.latitude}?overview=false`;
    const resp = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error(`OSRM ${resp.status}`);
    const data = await resp.json();
    const route = data.routes?.[0];
    if (!route) throw new Error("No route");

    const info: RouteInfo = {
      mode,
      durationMinutes: Math.round(route.duration / 60),
      distanceKm: Math.round((route.distance / 1000) * 10) / 10,
    };
    cache.set(key, info);
    return info;
  } catch {
    const fallback = fallbackEstimate(from, to, mode);
    cache.set(key, fallback);
    return fallback;
  }
}

export async function fetchAllModes(from: LatLng, to: LatLng): Promise<RouteInfo[]> {
  const modes: ("foot" | "car" | "bike")[] = ["foot", "car", "bike"];
  const results = await Promise.all(modes.map((m) => fetchRoute(from, to, m)));
  return results;
}
