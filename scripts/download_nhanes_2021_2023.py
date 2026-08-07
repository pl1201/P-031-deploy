#!/usr/bin/env python3
"""
Download NHANES 2021-2023 cycle XPT files from CDC.

Retrieves 8 public-use data files for type 2 diabetes research:
- Demographics, diabetes questionnaire, HbA1c, glucose, body measures,
  blood pressure, and dietary recalls (day 1 & 2).

Downloaded files are saved to ~/data/research/nhanes_2021_2023/raw/
with SHA-256 checksums and provenance metadata in MANIFEST.json.

Usage:
    python scripts/download_nhanes_2021_2023.py

References:
- NHANES 2021-2023: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- NCHS Data User Agreement: https://www.cdc.gov/nchs/data_access/restrictions.htm
"""

import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

# Files to download from NHANES 2021-2023 cycle
NHANES_FILES = [
    {
        "component": "Demographics",
        "file": "DEMO_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt",
        "cdc_release_date": "2024-09",
    },
    {
        "component": "Diabetes",
        "file": "DIQ_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.xpt",
        "cdc_release_date": "2024-09",
    },
    {
        "component": "HbA1c",
        "file": "GHB_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.xpt",
        "cdc_release_date": "2024-10",
    },
    {
        "component": "Glucose",
        "file": "GLU_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GLU_L.xpt",
        "cdc_release_date": "2024-10",
    },
    {
        "component": "Body Measures",
        "file": "BMX_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt",
        "cdc_release_date": "2024-09",
    },
    {
        "component": "Blood Pressure",
        "file": "BPXO_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.xpt",
        "cdc_release_date": "2024-09",
    },
    {
        "component": "Dietary Day 1",
        "file": "DR1TOT_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DR1TOT_L.xpt",
        "cdc_release_date": "2024-09",
    },
    {
        "component": "Dietary Day 2",
        "file": "DR2TOT_L",
        "url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DR2TOT_L.xpt",
        "cdc_release_date": "2024-09",
    },
]

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
TIMEOUT_SECONDS = 300


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, dest_path: Path) -> dict[str, Any]:
    """
    Download file from URL with retry logic.

    Returns:
        Metadata dict with retrieval_timestamp, sha256, file_size_bytes, url.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Downloading {url} (attempt {attempt}/{MAX_RETRIES})...")
            response = requests.get(
                url,
                timeout=TIMEOUT_SECONDS,
                stream=True,
                # DO NOT disable TLS verification
            )
            response.raise_for_status()

            # Write to disk
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Compute checksum
            sha256 = compute_sha256(dest_path)
            file_size = dest_path.stat().st_size
            retrieval_time = datetime.now(UTC).isoformat()

            print(f"  [OK] Downloaded {dest_path.name} ({file_size:,} bytes, SHA-256: {sha256[:16]}...)")

            return {
                "retrieval_timestamp": retrieval_time,
                "sha256": sha256,
                "file_size_bytes": file_size,
                "url": url,
            }

        except (requests.RequestException, OSError) as e:
            print(f"  [FAILED] Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"  [FAILED] Failed to download {url} after {MAX_RETRIES} attempts")
                raise


def main() -> None:
    """Download all NHANES 2021-2023 XPT files and generate manifest."""
    # Target directory (outside repo)
    output_dir = Path.home() / "data" / "research" / "nhanes_2021_2023" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("NHANES 2021-2023 Downloader")
    print(f"Output directory: {output_dir}")
    print(f"Files to download: {len(NHANES_FILES)}\n")

    manifest: dict[str, Any] = {
        "dataset": "NHANES August 2021 - August 2023",
        "cycle": "2021-2023",
        "source_url": "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023",
        "license": "NCHS Data User Agreement",
        "license_url": "https://www.cdc.gov/nchs/data_access/restrictions.htm",
        "download_date": datetime.now(UTC).isoformat(),
        "files": {},
    }

    success_count = 0
    for file_info in NHANES_FILES:
        file_name = f"{file_info['file']}.xpt"
        dest_path = output_dir / file_name

        print(f"[{success_count + 1}/{len(NHANES_FILES)}] {file_info['component']} ({file_name})")

        try:
            metadata = download_file(file_info["url"], dest_path)
            manifest["files"][file_name] = {
                "component": file_info["component"],
                "cdc_release_date": file_info["cdc_release_date"],
                **metadata,
            }
            success_count += 1
        except Exception as e:
            print(f"  [FAILED] Fatal error: {e}")
            sys.exit(1)

        print()

    # Write manifest
    manifest_path = output_dir.parent / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Download complete: {success_count}/{len(NHANES_FILES)} files")
    print(f"[OK] Manifest saved: {manifest_path}")
    print("\nNext step: python scripts/build_nhanes_2021_2023_cohort.py")


if __name__ == "__main__":
    main()
