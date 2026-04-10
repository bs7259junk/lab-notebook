#!/bin/bash
set -e

echo "Running migrations..."
alembic upgrade head

echo "Checking if seed needed..."
python - <<'PYEOF'
from app.db import SessionLocal
from app.models.models import User
db = SessionLocal()
count = db.query(User).count()
db.close()
if count == 0:
    print("Database empty — seeding...")
    import subprocess
    result = subprocess.run(["python", "-m", "app.etl.seed"], check=True)
else:
    print(f"Database has {count} users — skipping seed.")
PYEOF

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
