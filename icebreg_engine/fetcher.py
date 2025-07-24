import csv
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import requests

from .config import load_hosts, load_watchlist, CONFIG_DIR

log = logging.getLogger(__name__)

DATE_FMT = "%Y-%m-%d"


class FetchThread(threading.Thread):
    def __init__(self, update_callback=None):
        super().__init__(daemon=True)
        self.update_callback = update_callback
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        hosts = load_hosts()
        watchlist = load_watchlist()
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        for host in hosts:
            if self._stop_event.is_set():
                break
            url = host.get("url")
            apikey = host.get("apikey")
            intervals = host.get("intervals", ["5s"])
            host_dir = CONFIG_DIR / sanitize_host(url)
            for interval in intervals:
                interval_dir = host_dir / interval.upper()
                interval_dir.mkdir(parents=True, exist_ok=True)
                for stock in watchlist:
                    if self._stop_event.is_set():
                        break
                    symbol = stock.get("symbol")
                    exchange = stock.get("exchange")
                    csv_path = interval_dir / f"{symbol}.csv"
                    last_date = get_last_date(csv_path)
                    req_start = last_date + timedelta(days=1) if last_date else start_date
                    data = fetch_history(url, apikey, symbol, exchange, interval, req_start, end_date)
                    append_csv(csv_path, data)
                    progress = f"{symbol} {interval} done"
                    if self.update_callback:
                        self.update_callback(progress)
        if self.update_callback:
            self.update_callback("Fetch completed")


def sanitize_host(url: str) -> str:
    return url.replace("http://", "").replace("https://", "").replace("/", "_")


def get_last_date(csv_path: Path):
    if not csv_path.exists():
        return None
    try:
        with csv_path.open("r", newline="") as f:
            rows = list(csv.DictReader(f))
            if not rows:
                return None
            last = rows[-1]
            return datetime.strptime(last["date"], DATE_FMT).date()
    except Exception:
        return None


def fetch_history(host: str, apikey: str, symbol: str, exchange: str, interval: str, start_date: datetime.date, end_date: datetime.date):
    url = f"{host}/api/v1/history"
    payload = {
        "apikey": apikey,
        "symbol": symbol,
        "exchange": exchange,
        "interval": interval,
        "start_date": start_date.strftime(DATE_FMT),
        "end_date": end_date.strftime(DATE_FMT),
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        res = resp.json()
        if res.get("status") == "success":
            return res.get("data", [])
    except Exception as e:
        log.error("Fetch error for %s: %s", symbol, e)
    return []


def append_csv(csv_path: Path, data: List[Dict]):
    if not data:
        return
    new_rows = []
    for d in data:
        ts = datetime.fromtimestamp(d["timestamp"])
        row = {
            "date": ts.strftime(DATE_FMT),
            "timestamp": d["timestamp"],
            "open": d["open"],
            "high": d["high"],
            "low": d["low"],
            "close": d["close"],
            "volume": d.get("volume", 0),
            "oi": d.get("oi", 0),
        }
        new_rows.append(row)
    write_header = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(new_rows[0].keys()))
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)

