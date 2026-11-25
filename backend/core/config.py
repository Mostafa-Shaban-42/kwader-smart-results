"""Application configuration. No secrets in code."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SMART RESULTS - KAWADER NURSING SCHOOL"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5500"
    FIREBASE_PROJECT_ID: str = ""
    MAX_UPLOAD_SIZE_MB: int = 10
    RATE_LIMIT_ENABLED: bool = True
    JWT_SECRET: str = "CHANGE_ME_32_CHARS_MIN"
    JWT_EXPIRE_MINUTES: int = 120

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
ACADEMIC_YEARS: list[str] = ["first_year", "second_year", "third_year"]
YEAR_LABELS_AR: dict[str, str] = {
    "first_year": "السنة الأولى",
    "second_year": "السنة الثانية",
    "third_year": "السنة الثالثة",
}
# School-approved grading. Single source of truth.
GRADE_THRESHOLDS: list[tuple[float, str, str]] = [
    (90.0, "Excellent", "ممتاز"),
    (80.0, "Very Good", "جيد جداً"),
    (70.0, "Good", "جيد"),
    (60.0, "Pass", "مقبول"),
    (0.0, "Fail", "راسب"),
]
# Allowed CORS origins for production (Render + Vercel + Firebase Hosting)
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://smart-results.vercel.app",
    "https://smart-results.web.app",
    "https://smart-results.firebaseapp.com",
]