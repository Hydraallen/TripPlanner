import axios from "axios";
import { message } from "antd";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || "Request failed";
    message.error(msg);
    return Promise.reject(error);
  },
);

export default api;

// --- Types ---

export interface Location {
  longitude: number;
  latitude: number;
}

export interface Attraction {
  xid: string;
  name: string;
  address: string;
  location: Location;
  categories: string[];
  kinds: string;
  visit_duration: number;
  time_slot: string;
  commute_minutes: number;
  description: string | null;
  rating: number | null;
  ticket_price: number;
  score: number;
}

export interface Meal {
  type: string;
  name: string;
  address: string;
  estimated_cost: number;
  time_slot: string;
}

export interface Hotel {
  name: string;
  address: string;
  price_range: string;
  rating: number | null;
  estimated_cost_per_night: number;
}

export interface Budget {
  total_attractions: number;
  total_hotels: number;
  total_meals: number;
  total_transportation: number;
  total: number;
}

export interface WeatherInfo {
  date: string;
  temp_high: number;
  temp_low: number;
  precipitation_prob: number;
  weather_code: number;
  wind_speed: number;
}

export interface DayPlan {
  date: string;
  day_number: number;
  description: string;
  transportation: string;
  attractions: Attraction[];
  meals: Meal[];
  hotel: Hotel | null;
}

export interface TripPlan {
  city: string;
  start_date: string;
  end_date: string;
  days: DayPlan[];
  weather: WeatherInfo[];
  budget: Budget | null;
  suggestions: string[];
  source?: "llm" | "algorithmic";
}

export interface Trip {
  id: string;
  city: string;
  start_date: string;
  end_date: string;
  interests: string[];
  transport_mode: string;
  plan: TripPlan | null;
  created_at: string | null;
}

export interface TripSummary {
  id: string;
  city: string;
  start_date: string;
  end_date: string;
  transport_mode: string;
  created_at: string | null;
}

// --- Multi-Plan Types ---

export type PlanFocus = "budget" | "culture" | "nature" | "food" | "romantic" | "adventure";

export interface PlanScores {
  price: number;
  rating: number;
  convenience: number;
  diversity: number;
  safety: number;
  popularity: number;
  total: number;
}

export interface PlanAlternative {
  id: string;
  focus: PlanFocus;
  title: string;
  description: string;
  plan: TripPlan;
  scores: PlanScores | null;
  estimated_cost: number;
  source: "llm" | "algorithmic";
}

export interface GenerationProgress {
  plan_id: string;
  status: "collecting" | "generating" | "scoring" | "completed" | "failed";
  progress: number;
  step: string;
  preview: Record<string, unknown> | null;
}

// --- API functions ---

export async function listTrips(): Promise<TripSummary[]> {
  const { data } = await api.get("/trips");
  return data;
}

export async function getTrip(id: string): Promise<Trip> {
  const { data } = await api.get(`/trips/${id}`);
  return data;
}

export async function createTrip(params: {
  city: string;
  start_date: string;
  end_date: string;
  interests?: string[];
  transport_mode?: string;
}): Promise<{ id: string }> {
  const { data } = await api.post("/trips", null, { params });
  return data;
}

export async function deleteTrip(id: string): Promise<void> {
  await api.delete(`/trips/${id}`);
}

export async function generateMultiPlan(params: {
  city: string;
  start_date: string;
  end_date: string;
  interests?: string[];
  transport_mode?: string;
  budget?: number;
  radius?: number;
  num_plans?: number;
}): Promise<{ trip_id: string }> {
  const { data } = await api.post("/plans/generate", params);
  return data;
}

export async function getPlanAlternatives(tripId: string): Promise<PlanAlternative[]> {
  const { data } = await api.get(`/plans/${tripId}/plans`);
  return data.plans ?? [];
}

export async function selectPlan(tripId: string, planId: string): Promise<void> {
  await api.post(`/plans/${tripId}/select`, { plan_id: planId });
}

export function createProgressSSE(
  tripId: string,
  onProgress: (progress: GenerationProgress) => void,
  onError?: (error: Event) => void,
): EventSource {
  const es = new EventSource(`/api/plans/${tripId}/progress`);
  es.onmessage = (event) => {
    try {
      const progress = JSON.parse(event.data) as GenerationProgress;
      onProgress(progress);
      if (progress.status === "completed" || progress.status === "failed") {
        es.close();
      }
    } catch {
      // ignore parse errors
    }
  };
  es.onerror = (e) => {
    if (onError) onError(e);
    es.close();
  };
  return es;
}

export async function exportTrip(
  id: string,
  format: "markdown" | "json" | "html",
): Promise<string> {
  const { data } = await api.get(`/trips/${id}/export`, {
    params: { format },
    responseType: "text",
  });
  return data;
}

export async function sendChat(
  messages: { role: string; content: string }[],
  planContext?: string,
): Promise<string> {
  const { data } = await api.post("/chat", { messages, plan_context: planContext });
  return data.response;
}
