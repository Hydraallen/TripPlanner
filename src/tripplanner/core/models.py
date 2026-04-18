from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

# --- Base layer ---


class Location(BaseModel):
    """Geographic coordinates with validation."""

    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

    @field_validator("longitude", "latitude", mode="before")
    @classmethod
    def coerce_numeric(cls, v: object) -> float:
        if isinstance(v, str):
            return float(v.replace(",", "."))
        return float(v)


# --- Entity layer ---


class Attraction(BaseModel):
    """A tourist attraction or point of interest."""

    xid: str
    name: str
    address: str = ""
    location: Location
    categories: list[str] = Field(default_factory=list)
    kinds: str = ""
    visit_duration: int = Field(default=90, gt=0, description="minutes")
    description: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    ticket_price: float = Field(default=0, ge=0)
    score: float = Field(default=0.0, ge=0, le=1)

    @field_validator("rating", mode="before")
    @classmethod
    def clamp_rating(cls, v: object) -> float | None:
        if v is None:
            return None
        val = float(v)
        return min(max(val, 0.0), 5.0)


class Meal(BaseModel):
    """Dining recommendation."""

    type: str = Field(..., description="breakfast/lunch/dinner/snack")
    name: str
    address: str = ""
    location: Location | None = None
    description: str | None = None
    estimated_cost: float = Field(default=0, ge=0)


class Hotel(BaseModel):
    """Accommodation recommendation."""

    name: str
    address: str = ""
    location: Location | None = None
    price_range: str = ""
    rating: float | None = Field(default=None, ge=0, le=5)
    estimated_cost_per_night: float = Field(default=0, ge=0)


# --- Aggregation layer ---


class Budget(BaseModel):
    """Budget breakdown."""

    total_attractions: float = Field(default=0, ge=0)
    total_hotels: float = Field(default=0, ge=0)
    total_meals: float = Field(default=0, ge=0)
    total_transportation: float = Field(default=0, ge=0)
    total: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_total(self) -> Budget:
        computed = (
            self.total_attractions
            + self.total_hotels
            + self.total_meals
            + self.total_transportation
        )
        if self.total == 0 and computed > 0:
            self.total = computed
        return self


class WeatherInfo(BaseModel):
    """Weather forecast for a single day."""

    date: date
    temp_high: float = Field(..., description="Celsius")
    temp_low: float = Field(..., description="Celsius")
    precipitation_prob: float = Field(default=0, ge=0, le=100)
    weather_code: int = Field(default=0, description="WMO code")
    wind_speed: float = Field(default=0, ge=0, description="km/h")

    _WMO_CODES: dict[int, str] = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Drizzle",
        53: "Drizzle",
        55: "Drizzle",
        61: "Rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Showers",
        81: "Showers",
        82: "Heavy showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }

    @property
    def is_rainy(self) -> bool:
        return self.precipitation_prob > 50

    @property
    def description(self) -> str:
        return self._WMO_CODES.get(self.weather_code, "Unknown")


# --- Plan layer ---


class DayPlan(BaseModel):
    """Single day itinerary."""

    date: date
    day_number: int = Field(..., gt=0)
    description: str = ""
    transportation: str = "walking"
    attractions: list[Attraction] = Field(default_factory=list)
    meals: list[Meal] = Field(default_factory=list)
    hotel: Hotel | None = None


class TripPlan(BaseModel):
    """Complete travel plan."""

    city: str
    start_date: date
    end_date: date
    days: list[DayPlan] = Field(default_factory=list)
    weather: list[WeatherInfo] = Field(default_factory=list)
    budget: Budget | None = None
    suggestions: list[str] = Field(default_factory=list)


# --- Persistence layer ---


class Trip(BaseModel):
    """Persisted trip record."""

    id: str
    city: str
    start_date: date
    end_date: date
    interests: list[str]
    transport_mode: str = "walking"
    plan: TripPlan | None = None
    created_at: datetime


# --- Multi-Plan layer ---


class PlanFocus(StrEnum):
    """Focus type for plan alternatives."""

    BUDGET = "budget"
    CULTURE = "culture"
    NATURE = "nature"


class PlanScores(BaseModel):
    """Multi-dimensional scores for a plan alternative."""

    price: float = Field(default=0, ge=0, le=1)
    rating: float = Field(default=0, ge=0, le=1)
    convenience: float = Field(default=0, ge=0, le=1)
    diversity: float = Field(default=0, ge=0, le=1)
    total: float = Field(default=0, ge=0, le=1)


class PlanAlternative(BaseModel):
    """A single plan alternative in a multi-plan generation."""

    id: str
    focus: PlanFocus
    title: str
    description: str = ""
    plan: TripPlan
    scores: PlanScores | None = None
    estimated_cost: float = Field(default=0, ge=0)
    source: str = "llm"


class GenerationProgress(BaseModel):
    """Real-time progress for plan generation."""

    plan_id: str
    status: str = "collecting"
    progress: float = Field(default=0, ge=0, le=100)
    step: str = ""
    preview: dict | None = None
