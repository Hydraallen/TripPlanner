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

export async function generatePlan(params: {
  city: string;
  start_date: string;
  end_date: string;
  interests: string[];
  transport_mode: string;
  radius?: number;
}): Promise<TripPlan> {
  const { data } = await api.post("/plans/generate", params);
  return data;
}

export async function generateLLMPlan(params: {
  city: string;
  start_date: string;
  end_date: string;
  interests: string[];
  transport_mode: string;
  preferences?: string;
  radius?: number;
}): Promise<TripPlan> {
  const { data } = await api.post("/plans/generate-llm", params);
  return data;
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
