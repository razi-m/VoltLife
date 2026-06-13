import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ManualSettings:
    def __init__(self):
        self.PROJECT_NAME = "VoltLife Backend"
        self.API_V1_STR = "/api/v1"
        self.DATABASE_URL = os.environ["DATABASE_URL"]  # Raises KeyError immediately if missing

        self.DEMO_KEY = os.getenv("DEMO_KEY", "volt_secret_key")
        self.PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        self.PUBLIC_FRONTEND_URL = os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:3000")
        self.PACE_S = float(os.getenv("PACE_S", "0.15"))

        # Parse autonomy mode safely
        autonomy_mode_raw = os.getenv("AUTONOMY_MODE", "true").lower()
        self.AUTONOMY_MODE = autonomy_mode_raw in ("true", "1", "yes")

        self.MODEL_PATH = os.getenv("MODEL_PATH", "app/ml/models/model_v1.pkl")

settings = ManualSettings()
