import json
from pathlib import Path
from typing import List, Dict

CONFIG_DIR = Path("data")
CONFIG_DIR.mkdir(exist_ok=True)
HOSTS_FILE = CONFIG_DIR / "hosts.json"
WATCHLIST_FILE = CONFIG_DIR / "watchlist.json"


def load_json(path: Path, default):
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_hosts() -> List[Dict]:
    return load_json(HOSTS_FILE, [])


def save_hosts(hosts: List[Dict]):
    save_json(HOSTS_FILE, hosts)


def load_watchlist() -> List[Dict]:
    return load_json(WATCHLIST_FILE, [])


def save_watchlist(watchlist: List[Dict]):
    save_json(WATCHLIST_FILE, watchlist)
