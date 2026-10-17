import os

ROW_LIMIT = 5000
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "pulseiq_superset_secret_key_change_in_production_32char")

# Superset internal application database (stored in volume for clean separation from warehouse dw schema)
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_METADATA_DB_URI",
    "sqlite:////app/superset_home/superset.db"
)

# Feature flags
FEATURE_FLAGS = {
    "ALERT_REPORTS": False,
    "EMBEDDED_SUPERSET": True,
}

# CSRF & Security
WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False
