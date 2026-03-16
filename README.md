# SensorHub mkñasjdlñas

REST API for IoT environmental monitoring. Sensors send temperature, humidity and CO2 readings which are stored in MongoDB and aggregated into hourly CSV reports uploaded to MinIO.

## Stack

- **FastAPI** — Python 3.12
- **MongoDB** — readings storage
- **MinIO** — report storage (S3-compatible)

## Quickstart

```bash
cp .env.example .env   # fill in credentials
docker compose up -d
```

API available at `http://localhost:8000` · MinIO console at `http://localhost:9001`

## Endpoints

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
just dev          # run with hot reload
just test         # unit tests
just test-integration  # integration tests (requires Docker)
just lint         # ruff
just check        # lint + format + types + tests
```

## Bump & release

```bash
just bump-patch   # 0.1.0 → 0.1.1
git push          # release created automatically on merge to main
```
A