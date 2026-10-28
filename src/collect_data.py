"""Collect SpaceX launch data from the API, with a historical CSV fallback."""

import csv
import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.spacexdata.com/v4/launches"
FALLBACK_URL = (
    "https://raw.githubusercontent.com/ArivAfonso/spacex-datasets/"
    "9db84fdda3d52a0659a5fd19a9465cb60f1ddf0b/data/csv/launches.csv"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
USER_AGENT = "SpaceX-Falcon9-Landing-Prediction/1.0"
TIMEOUT_SECONDS = 35
FALLBACK_REQUIRED_COLUMNS = {
    "Date",
    "Booster Version",
    "Mission",
    "Landing Outcome",
}


def download(url: str) -> bytes:
    """Download a URL and return its response bytes."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def save_new_file(path: Path, contents: bytes) -> None:
    """Save data without replacing a file that already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output_file:
        output_file.write(contents)


def collect_from_api() -> int:
    """Download, validate, and save the SpaceX API launch records."""
    launches = json.loads(download(API_URL).decode("utf-8"))
    if (
        not isinstance(launches, list)
        or not launches
        or not all(isinstance(launch, dict) for launch in launches)
    ):
        raise ValueError("Unexpected SpaceX API response: expected launch records.")

    output_path = RAW_DATA_DIR / "launches.json"
    contents = (json.dumps(launches, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    save_new_file(output_path, contents)
    print(f"Saved {len(launches)} API launch records to {output_path}")
    return len(launches)


def collect_from_fallback() -> int:
    """Download, validate, and save the pinned historical CSV snapshot."""
    contents = download(FALLBACK_URL)
    text = contents.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text, newline=""))

    if not reader.fieldnames or not FALLBACK_REQUIRED_COLUMNS.issubset(
        reader.fieldnames
    ):
        raise ValueError("Unexpected fallback CSV: required launch columns are missing.")

    row_count = sum(1 for _ in reader)
    if row_count == 0:
        raise ValueError("Unexpected fallback CSV: it contains no launch records.")

    output_path = RAW_DATA_DIR / "launches.csv"
    save_new_file(output_path, contents)
    print(f"Saved {row_count} historical launch records to {output_path}")
    print("The fallback is a community dataset snapshot current through 2021-12-18.")
    return row_count


def collect_launches() -> int:
    """Prefer the live API and use the historical CSV if its request fails."""
    try:
        return collect_from_api()
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"SpaceX API request failed ({error}); trying historical CSV fallback.")

    return collect_from_fallback()


if __name__ == "__main__":
    collect_launches()
