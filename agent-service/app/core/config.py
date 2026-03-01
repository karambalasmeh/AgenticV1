from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "agent-service"
    SERVICE_VERSION: str = "1.0.0"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    API_PREFIX: str = "/api/v1"
    REQUEST_TIMEOUT_S: int = 30
    MAX_REPAIR_ATTEMPTS: int = 2
    BLOCK_VIOLATION_THRESHOLD: int = 3

    LLM_PROVIDER: str = "mock"
    VERTEX_PROJECT_ID: str = ""
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL: str = "gemini-2.5-flash"

    DATABASE_URL: str = "sqlite:///./agent_service.db"

    KNOWLEDGE_SERVICE_URL: str = "http://knowledge-service:8000"
    WORKFLOW_SERVICE_URL: str = "http://workflow-service:8000"
    GOVERNANCE_SERVICE_URL: str = "http://governance-service:8000"
    CLIENT_TIMEOUT_S: float = 4.0
    CLIENT_RETRIES: int = 1
    USE_MOCK_SERVICES: bool = True

    REQUIRE_CITATIONS: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
