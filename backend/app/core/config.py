import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ManualSettings:
    def __init__(self):
        self.PROJECT_NAME = "VoltLife Backend"
        self.API_V1_STR = "/api/v1"
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

        self.DEMO_KEY = os.getenv("DEMO_KEY", "volt_secret_key")
        self.PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        self.PUBLIC_FRONTEND_URL = os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:3000")
        self.PACE_S = float(os.getenv("PACE_S", "0.15"))

        # Parse autonomy mode safely
        autonomy_mode_raw = os.getenv("AUTONOMY_MODE", "true").lower()
        self.AUTONOMY_MODE = autonomy_mode_raw in ("true", "1", "yes")

        self.MODEL_PATH = os.getenv("MODEL_PATH", "app/ml/models/model_v1.pkl")

        # Parse n8n configuration
        n8n_enabled_raw = os.getenv("N8N_ENABLED", "false").lower()
        self.N8N_ENABLED = n8n_enabled_raw in ("true", "1", "yes")
        self.N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
        self.BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

settings = ManualSettings()

