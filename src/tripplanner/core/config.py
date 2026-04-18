from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    opentripmap_api_key: str = ""
    opentripmap_base_url: str = "https://api.opentripmap.com/0.1/en"
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

    openai_endpoint: str = ""
    openai_api_key: str = ""
    openai_model_name: str = "glm-5.1"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    return Settings()
