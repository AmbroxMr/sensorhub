import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8001")


def get_health() -> dict:
    r = requests.get(f"{API_URL}/health", timeout=5)
    r.raise_for_status()
    return r.json()


def get_readings(device_id: str | None = None, limit: int | None = None) -> list[dict]:
    params = {}
    if device_id:
        params["device_id"] = device_id
    if limit:
        params["limit"] = limit
    r = requests.get(f"{API_URL}/readings", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_stats() -> list[dict]:
    r = requests.get(f"{API_URL}/readings/stats", timeout=10)
    r.raise_for_status()
    return r.json()


def export_csv() -> bytes:
    r = requests.get(f"{API_URL}/export", timeout=30)
    r.raise_for_status()
    return r.content


def post_reading(data: dict) -> dict:
    r = requests.post(f"{API_URL}/readings", json=data, timeout=5)
    r.raise_for_status()
    return r.json()


def generate_report(hour: str | None = None) -> dict:
    params = {"hour": hour} if hour else {}
    r = requests.post(f"{API_URL}/reports/generate", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def list_reports() -> list[dict]:
    r = requests.get(f"{API_URL}/reports", timeout=10)
    r.raise_for_status()
    return r.json()


def get_report(report_name: str) -> bytes:
    r = requests.get(f"{API_URL}/reports/{report_name}", timeout=15)
    r.raise_for_status()
    return r.content
