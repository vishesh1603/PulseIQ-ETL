#!/usr/bin/env bash
set -e

echo "Starting Superset setup..."

# 1. Initialize metadata database
superset db upgrade

# 2. Create admin user if not exists
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname "PulseIQ" \
  --lastname "Admin" \
  --email "admin@pulseiq.local" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true

# 3. Initialize roles and permissions
superset init

# 4. Connect to warehouse using read-only role superset_ro
echo "Setting up warehouse connection for superset_ro..."
python3 - <<EOF
import os
from superset.app import create_app

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database
    
    ro_user = os.environ.get("SUPERSET_RO_USER", "superset_ro")
    ro_password = os.environ.get("SUPERSET_RO_PASSWORD", "superset_ro_pass")
    host = os.environ.get("WAREHOUSE_HOST", "warehouse")
    port = os.environ.get("WAREHOUSE_PORT", "5432")
    dbname = os.environ.get("WAREHOUSE_DB", "pulseiq")
    uri = f"postgresql://{ro_user}:{ro_password}@{host}:{port}/{dbname}"
    
    existing = db.session.query(Database).filter_by(database_name="PulseIQ Warehouse").first()
    if existing:
        existing.sqlalchemy_uri = uri
        print("Updated existing PulseIQ Warehouse connection.")
    else:
        new_db = Database(
            database_name="PulseIQ Warehouse",
            sqlalchemy_uri=uri,
            expose_in_sqllab=True,
            allow_run_async=False
        )
        db.session.add(new_db)
        print("Created PulseIQ Warehouse connection.")
    db.session.commit()
EOF

echo "Superset initialization complete. Starting server on 0.0.0.0:8088..."
exec /usr/bin/run-server.sh
