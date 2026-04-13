"""
IMDBON Buoy Data Downloader
============================
Downloads all available meteorological and oceanographic parameters
for buoys M1–M6 from the Marine Institute's ERDDAP server.

Two datasets are pulled per buoy and merged:
  1. Bulk parameters  — wind speed, Hs, wave period, SST, pressure, etc.
  2. Spectral parameters — Hm0, Tp, Tm01, Tm02, directional spread, etc.

Output: one CSV per buoy, saved to ./imdbon_data/

Marine Institute ERDDAP: https://erddap.marine.ie/erddap
"""

import os
import time
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────

BASE_URL = "https://erddap.marine.ie/erddap/tabledap"

# Dataset IDs on the Marine Institute ERDDAP
DATASETS = {
    "bulk": "IWBNetwork",
    # IWaveBNetwork_spectral covers coastal wave buoys only, not the IMDBON M-buoys
}

# All buoys. M1 was decommissioned in 2007 but historical data is available.
BUOYS = ["M1", "M2", "M3", "M4", "M5", "M6"]

# Full record start
START_DATE = "2001-01-01T00:00:00Z"
END_DATE   = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

OUTPUT_DIR = "./imdbon_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {"Accept": "text/csv"}
RETRY_WAIT = 10   # seconds between retries
MAX_RETRIES = 3

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_available_variables(dataset_id: str) -> list[str]:
    """
    Fetch variable names from the ERDDAP DDS endpoint.
    Returns a list of column names (excluding coordinate axes which
    are always returned).
    """
    url = f"{BASE_URL}/{dataset_id}.dds"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        # DDS lists variables as "    Float32 varname;" — extract names
        variables = []
        for line in r.text.splitlines():
            line = line.strip()
            if line and not line.startswith("Dataset") and not line.startswith("}") \
               and not line.startswith("Sequence") and not line.startswith("String time"):
                parts = line.rstrip(";").split()
                if len(parts) == 2:
                    variables.append(parts[1])
        return variables
    except Exception as e:
        print(f"    Warning: could not fetch DDS for {dataset_id}: {e}")
        return []


def get_station_id_field(dataset_id: str) -> str:
    """
    The bulk dataset uses 'station_id'; the spectral dataset uses 'buoy_id'.
    Detect by reading the DDS — fall back to 'station_id' if unreachable.
    """
    url = f"{BASE_URL}/{dataset_id}.dds"
    try:
        r = requests.get(url, timeout=20)
        if "buoy_id" in r.text:
            return "buoy_id"
    except Exception:
        pass
    return "station_id"


def build_erddap_url(dataset_id: str, buoy_id: str,
                     start: str, end: str,
                     id_field: str = "station_id",
                     file_format: str = "csv") -> str:
    """
    Build an ERDDAP tabledap URL for a specific buoy and time range.
    All variables are returned (no variable selection = ERDDAP returns all).
    """
    constraints = (
        f'&time>={start}'
        f'&time<={end}'
        f'&{id_field}="{buoy_id}"'
    )
    return f"{BASE_URL}/{dataset_id}.{file_format}?{constraints}"


def fetch_erddap_csv(url: str, buoy_id: str, dataset_label: str) -> pd.DataFrame | None:
    """
    Fetch CSV from ERDDAP with retry logic. Returns a DataFrame or None.
    ERDDAP CSV has two header rows: variable names + units.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"    [{dataset_label}] Fetching (attempt {attempt})...")
            r = requests.get(url, headers=HEADERS, timeout=300)

            # ERDDAP returns 404 or error text if no data for that buoy
            if r.status_code == 404 or "Error" in r.text[:200]:
                print(f"    [{dataset_label}] No data found for {buoy_id}.")
                return None

            r.raise_for_status()

            # Row 0 = column names, Row 1 = units (skip units row for clean df)
            df = pd.read_csv(StringIO(r.text), skiprows=[1], low_memory=False)

            # Standardise time column
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
                df = df.sort_values("time").reset_index(drop=True)

            print(f"    [{dataset_label}] {len(df):,} rows retrieved.")
            return df

        except requests.exceptions.Timeout:
            print(f"    [{dataset_label}] Timeout on attempt {attempt}.")
        except requests.exceptions.RequestException as e:
            print(f"    [{dataset_label}] Request error: {e}")

        if attempt < MAX_RETRIES:
            print(f"    Retrying in {RETRY_WAIT}s...")
            time.sleep(RETRY_WAIT)

    print(f"    [{dataset_label}] Failed after {MAX_RETRIES} attempts.")
    return None


def merge_bulk_and_spectral(df_bulk: pd.DataFrame | None,
                             df_spectral: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Merge bulk and spectral DataFrames on nearest timestamp (1-hour tolerance).
    If only one exists, return that one alone.
    """
    if df_bulk is None and df_spectral is None:
        return None
    if df_bulk is None:
        return df_spectral
    if df_spectral is None:
        return df_bulk

    # Merge on time using merge_asof (nearest match within 30 min)
    df_bulk     = df_bulk.sort_values("time")
    df_spectral = df_spectral.sort_values("time")

    # Drop columns duplicated between datasets before merging
    shared_cols = [c for c in df_spectral.columns
                   if c in df_bulk.columns and c != "time"]
    df_spectral_clean = df_spectral.drop(columns=shared_cols, errors="ignore")

    merged = pd.merge_asof(
        df_bulk,
        df_spectral_clean,
        on="time",
        tolerance=pd.Timedelta("30min"),
        direction="nearest"
    )
    print(f"    Merged shape: {merged.shape}")
    return merged


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("IMDBON Buoy Data Downloader")
    print(f"Period : {START_DATE} → {END_DATE}")
    print(f"Buoys  : {', '.join(BUOYS)}")
    print(f"Output : {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)

    summary = []

    print("\nDetecting station ID field...")
    id_field = get_station_id_field(DATASETS["bulk"])
    print(f"  IWBNetwork → '{id_field}'")

    for buoy in BUOYS:
        print(f"\n▶ Buoy {buoy}")

        url = build_erddap_url(DATASETS["bulk"], buoy, START_DATE, END_DATE,
                               id_field=id_field)
        df = fetch_erddap_csv(url, buoy, "IWBNetwork")

        if df is None or df.empty:
            print(f"  ✗ No data retrieved for {buoy}. Skipping.")
            summary.append({"buoy": buoy, "rows": 0, "columns": 0, "status": "no data"})
            continue

        # -- Save --
        outpath = os.path.join(OUTPUT_DIR, f"{buoy}_imdbon_full.csv")
        df.to_csv(outpath, index=False)
        print(f"  ✓ Saved → {outpath}  ({len(df):,} rows × {len(df.columns)} columns)")

        summary.append({
            "buoy":    buoy,
            "rows":    len(df),
            "columns": len(df.columns),
            "start":   str(df["time"].min()) if "time" in df.columns else "N/A",
            "end":     str(df["time"].max()) if "time" in df.columns else "N/A",
            "status":  "ok",
            "file":    outpath,
        })

        time.sleep(2)  # polite pause between buoys

    # -- Summary table --
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    df_summary = pd.DataFrame(summary)
    print(df_summary.to_string(index=False))

    summary_path = os.path.join(OUTPUT_DIR, "download_summary.csv")
    df_summary.to_csv(summary_path, index=False)
    print(f"\nSummary saved → {summary_path}")


if __name__ == "__main__":
    main()
