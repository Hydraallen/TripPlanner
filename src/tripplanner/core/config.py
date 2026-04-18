from pydantic_settings import BaseSettings, SettingsConfigDict

VISIT_DURATION_BY_KIND: dict[str, int] = {
    "museum": 120,
    "gallery": 90,
    "zoo": 180,
    "attraction": 90,
    "viewpoint": 45,
    "park": 60,
    "garden": 60,
    "monument": 45,
    "castle": 90,
    "church": 45,
    "cathedral": 60,
    "palace": 90,
    "fort": 75,
    "place_of_worship": 45,
    "theatre": 150,
    "cinema": 150,
    "restaurant": 60,
    "cafe": 30,
    "bar": 45,
    "beach": 120,
    "nightclub": 120,
    "mall": 90,
    "library": 60,
    "arts_centre": 90,
    "nature_reserve": 120,
    "wood": 90,
    "peak": 60,
}


class Settings(BaseSettings):
    # No API key needed — uses Overpass API (OSM) + Nominatim (free)
    openmeteo_base_url: str = "https://api.open-meteo.com/v1"
    wikipedia_base_url: str = "https://en.wikipedia.org/api/rest_v1"
    database_url: str = "sqlite+aiosqlite:///./trips.db"
    max_places_per_trip: int = 20
    default_search_radius: int = 10000
    cache_ttl: int = 86400
    default_visit_duration: int = 90
    walking_speed_kmh: float = 5.0
    transit_speed_kmh: float = 25.0
    driving_speed_kmh: float = 30.0

    amap_api_key: str = ""
    amap_base_url: str = "https://restapi.amap.com"

    geoapify_api_key: str = ""

    openai_endpoint: str = ""
    openai_api_key: str = ""
    openai_model_name: str = "glm-5.1"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 16384

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    return Settings()


def get_visit_duration(kinds: str) -> int:
    """Look up visit duration by attraction category.

    Splits the comma-separated kinds string and returns the first
    matching duration from VISIT_DURATION_BY_KIND, or the default.
    """
    if not kinds:
        return Settings().default_visit_duration
    for kind in kinds.split(","):
        kind = kind.strip().lower()
        if kind in VISIT_DURATION_BY_KIND:
            return VISIT_DURATION_BY_KIND[kind]
    return Settings().default_visit_duration
