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

# 5 years, only first 3 active now. To activate year 4, change enabled to True.
YEARS_CONFIG = {
    "first_year": {"label": "First Year", "label_ar": "السنة الأولى", "enabled": True, "order": 1},
    "second_year": {"label": "Second Year", "label_ar": "السنة الثانية", "enabled": True, "order": 2},
    "third_year": {"label": "Third Year", "label_ar": "السنة الثالثة", "enabled": True, "order": 3},
    "fourth_year": {"label": "Fourth Year", "label_ar": "السنة الرابعة", "enabled": False, "order": 4},
    "fifth_year": {"label": "Fifth Year", "label_ar": "السنة الخامسة", "enabled": False, "order": 5},
}
ACADEMIC_YEARS: list[str] = [k for k, v in YEARS_CONFIG.items() if v["enabled"]]
ALL_YEARS: list[str] = list(YEARS_CONFIG.keys())

GRADE_THRESHOLDS: list[tuple[float, str, str]] = [
    (90.0, "Excellent", "ممتاز"),
    (80.0, "Very Good", "جيد جداً"),
    (70.0, "Good", "جيد"),
    (60.0, "Pass", "مقبول"),
    (0.0, "Fail", "راسب"),
]
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://smart-results.vercel.app",
    "https://kwader-smart-results-frontend.vercel.app"
]