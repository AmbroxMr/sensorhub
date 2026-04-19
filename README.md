# SensorHub

REST API for IoT environmental monitoring. Sensors send temperature, humidity and CO2 readings which are stored in MongoDB and aggregated into hourly CSV reports uploaded to MinIO. Includes a Streamlit dashboard to visualise data in real time.

## Stack

- **FastAPI** — Python 3.12
- **MongoDB** — readings storage
- **MinIO** — report storage (S3-compatible)
- **RabbitMQ** — message queue for sensor ingestion
- **Streamlit** — web dashboard

## Architecture

```
IoT Devices → RabbitMQ → Worker → MongoDB
                                      │
                          FastAPI (REST API)
                                      │
                         ┌────────────┴───────────┐
                       MinIO                  Streamlit
                    (CSV reports)            (dashboard)
```

## Quickstart

```bash
cp .env.example .env   # fill in credentials
docker compose up -d
```

| Service | URL |
|---------|-----|
| API | `http://localhost:8001` |
| Dashboard (Streamlit) | `http://localhost:8501` |
| MinIO console | `http://localhost:9001` |
| RabbitMQ management | `http://localhost:15672` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/readings` | Store a sensor reading |
| GET | `/readings` | List readings (`?device_id=` `&limit=`) |
| GET | `/readings/stats` | Aggregated stats per device |
| GET | `/export` | Download all readings as CSV |
| POST | `/reports/generate` | Generate hourly report and upload to MinIO (`?hour=`) |
| GET | `/reports` | List available reports in MinIO |
| GET | `/reports/{report_name}` | Download a report |

## Development

```bash
just dev          # run API with hot reload
just frontend     # run Streamlit dashboard
just test         # unit tests
just test-integration  # integration tests (requires Docker)
just lint         # ruff
just check        # lint + format + types + tests
```

### Frontend only (without Docker)

```bash
uv sync --group frontend
just frontend
# Dashboard available at http://localhost:8501
# Set API_URL env var if the API is not on localhost:8001
```

## Simulate sensor data

```bash
uv run python simulator.py            # 100 readings at default rate
uv run python simulator.py --rate 2   # 2 readings/second
uv run python simulator.py --total 50 # stop after 50 readings
```

## Bump & release

```bash
just bump-patch   # 0.1.0 → 0.1.1
git push          # release created automatically on merge to main
```
