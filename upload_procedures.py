#!/usr/bin/env python3
"""
Script to upload current/custom test procedure data to the active Django database.
Usage:
    python upload_procedures.py [--file path/to/procedures.json]
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ndt_demo.settings")

import django
django.setup()

from home.models import InspectionProcedure


def upload_procedures(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Fixture file '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        procedures = json.load(f)

    if not isinstance(procedures, list):
        print(f"Error: Fixture file '{file_path}' must contain a JSON array/list of procedure objects.")
        sys.exit(1)

    print(f"Uploading test procedure data from: {file_path}")
    created_count = 0
    updated_count = 0

    for idx, item in enumerate(procedures, start=1):
        title = item.get("title", "").strip()
        standard_code = item.get("standard_code", "").strip()
        description = item.get("description", "").strip()
        default_statement = item.get("default_statement", "").strip()

        if not standard_code or not title:
            print(f"  [{idx}] Skipped invalid entry (missing title or standard_code): {item}")
            continue

        procedure, created = InspectionProcedure.objects.update_or_create(
            standard_code=standard_code,
            defaults={
                "title": title,
                "description": description,
                "default_statement": default_statement,
            }
        )

        status_str = "Created" if created else "Updated"
        if created:
            created_count += 1
        else:
            updated_count += 1

        print(f"  [{idx}] {status_str}: '{procedure.title}' ({procedure.standard_code})")

    print("\n----------------------------------------")
    print(f"Upload Complete!")
    print(f"  Total Processed : {len(procedures)}")
    print(f"  Created         : {created_count}")
    print(f"  Updated         : {updated_count}")
    print(f"  Total in DB     : {InspectionProcedure.objects.count()}")
    print("----------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="Upload test procedure data into the database.")
    default_fixture = BASE_DIR / "home" / "fixtures" / "test_procedures_data.json"
    parser.add_argument(
        "--file", "-f",
        default=str(default_fixture),
        help="Path to the JSON fixture file containing procedure data."
    )

    args = parser.parse_args()
    upload_procedures(args.file)


if __name__ == "__main__":
    main()
