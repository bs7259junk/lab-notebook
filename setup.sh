#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
#  ELN — one-command setup
# ──────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Dependency checks ──────────────────────
if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker is not installed or not on PATH." >&2
  echo "       Install Docker Desktop from https://www.docker.com/products/docker-desktop/" >&2
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo "ERROR: 'docker compose' (v2) is not available." >&2
  echo "       Update Docker Desktop or install the Compose plugin." >&2
  exit 1
fi

# ── 2. .env ───────────────────────────────────
if [ ! -f "$REPO_ROOT/.env" ]; then
  echo "Creating .env from .env.example..."
  cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
else
  echo ".env already exists — skipping."
fi

# ── 3. Required directories ───────────────────
for dir in uploads logs; do
  if [ ! -d "$REPO_ROOT/$dir" ]; then
    echo "Creating $dir/ directory..."
    mkdir -p "$REPO_ROOT/$dir"
  fi
done

# ── 4. Demo placeholder files ─────────────────
if [ ! -f "$REPO_ROOT/uploads/sample_bioreactor_log.txt" ]; then
cat > "$REPO_ROOT/uploads/sample_bioreactor_log.txt" <<'EOF'
# Bioreactor Run Log — EXP-2026-006 G-Rex 10 Scale-Up Run 1
# Format: Time(h) | pH | DO(%) | Agitation(RPM) | Temp(°C) | Volume(mL)
0.0   7.20  85.0  0    37.0  40.0
2.0   7.19  78.3  0    37.0  40.0
4.0   7.18  71.6  0    37.1  40.0
6.0   7.19  65.2  0    37.0  40.0
12.0  7.18  52.1  0    37.0  40.0
24.0  7.17  41.8  0    37.1  40.0
48.0  7.16  33.5  0    37.0  40.0
72.0  7.15  28.9  0    37.0  40.0
96.0  7.18  55.3  0    37.0  40.0
120.0 7.19  61.2  0    37.1  40.0
144.0 7.20  67.8  0    37.0  40.0
168.0 7.20  72.4  0    37.0  40.0
# Day 7 feed added at 168 h; IL-2 replenished to 200 IU/mL
EOF
fi

if [ ! -f "$REPO_ROOT/uploads/chromatography_trace.txt" ]; then
cat > "$REPO_ROOT/uploads/chromatography_trace.txt" <<'EOF'
# Protein A Affinity Chromatography — UV280 Absorbance Trace
# EXP-2026-010 mAb Capture Step
# Format: Volume(mL) | UV280(mAU) | Conductivity(mS/cm) | %Buffer_B
0.0    2.1   15.2  0.0
1.0    2.3   15.1  0.0
2.0    2.4   15.2  0.0
3.0    2.2   15.1  0.0
4.0    2.1   15.0  0.0
5.0    3.8   15.2  0.0
6.0   18.4   15.1  0.0
7.0   95.2   15.0  0.0
8.0  312.7   14.9  0.0
9.0  687.4   14.8  0.0
10.0 998.3   14.7  0.0
11.0 1245.6  14.6  0.0
12.0 1187.2  14.5  0.0
13.0  834.5  14.4  0.0
14.0  421.3  14.3  0.0
15.0  198.7  14.2  0.0
16.0   87.6  14.1  0.0
17.0   32.4  14.0  0.0
18.0   12.1  13.9  0.0
19.0    4.2   4.8  100.0
20.0    3.1   4.6  100.0
# Peak at ~11 mL corresponds to IgG1 mAb elution
# Elution buffer: 0.1 M glycine pH 3.5
EOF
fi

if [ ! -f "$REPO_ROOT/uploads/pbmc_viability_counts.txt" ]; then
cat > "$REPO_ROOT/uploads/pbmc_viability_counts.txt" <<'EOF'
# PBMC Hemocytometer Viability Counts — EXP-2026-001
# Donor buffy coats processed by Ficoll density gradient centrifugation
# Format: Sample | Total_cells/mL | Viable_cells/mL | Viability(%) | Notes
Donor-1-A  2.40e6  2.28e6  95.0  Buffy coat lot BC-2026-031
Donor-1-B  2.35e6  2.21e6  94.0  Technical replicate
Donor-2-A  3.10e6  2.98e6  96.1  Buffy coat lot BC-2026-032
Donor-2-B  3.08e6  2.94e6  95.5  Technical replicate
Donor-3-A  2.75e6  2.64e6  96.0  Buffy coat lot BC-2026-033
Donor-3-B  2.72e6  2.61e6  95.9  Technical replicate
# Mean viability across all donors: 95.4 ± 0.7%
# All samples exceed minimum viability threshold (>90%) — approved for downstream use
EOF
fi

# ── 5. Start containers ───────────────────────
echo ""
echo "Starting containers..."
cd "$REPO_ROOT"
docker compose up --build -d

# ── 6. Wait for healthy/running ───────────────
echo "Waiting for containers to be ready (timeout: 120s)..."
TIMEOUT=120
ELAPSED=0
EXPECTED=3

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
  RUNNING=$(docker compose ps 2>/dev/null | grep -cE "Up " || true)
  if [ "$RUNNING" -ge "$EXPECTED" ]; then
    break
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  printf "  [%ds] waiting for %d/%d containers...\n" "$ELAPSED" "$RUNNING" "$EXPECTED"
done

if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
  echo ""
  echo "WARNING: Timed out waiting for containers. They may still be starting."
  echo "Run 'docker compose ps' to check status."
  echo "Run 'docker compose logs' to diagnose any issues."
else
  echo "  All containers are up."
fi

# ── 7. Final URLs ─────────────────────────────
echo ""
echo "============================================"
echo "  ELN is ready!"
echo "============================================"
echo "  Frontend:    http://localhost:3000"
echo "  Backend API: http://localhost:8003"
echo "  API Docs:    http://localhost:8003/docs"
echo "============================================"
echo "  Demo users (password: Lab2026!)"
echo "  admin      - Administrator"
echo "  alice      - Scientist"
echo "  bob        - Technician"
echo "  carol      - Research Associate / Scientist"
echo "  dave       - Reviewer"
echo "============================================"
echo "  Stop:  docker compose down"
echo "  Reset: docker compose down -v && bash setup.sh"
echo "============================================"
