from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # English comments only

    SERVICE_NAME: str = "agent-service"
    SERVICE_VERSION: str = "0.1.0"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    REQUEST_TIMEOUT_S: int = 30

    # LLM provider selection
    LLM_PROVIDER: str = "mock"  # mock | vertex
    VERTEX_PROJECT_ID: str = ""
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL: str = "gemini-2.5-flash"

    # Downstream services (later)
    KNOWLEDGE_SERVICE_URL: str = "http://knowledge-service:8000"
    WORKFLOW_SERVICE_URL: str = "http://workflow-service:8000"
    GOVERNANCE_SERVICE_URL: str = "http://governance-service:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()