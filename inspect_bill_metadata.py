#!/usr/bin/env python3

"""
Utility script to sample OpenParliament bill metadata.

Fetches a handful of bills, prints the raw fields returned by the API,
and shows the derived metadata that the ingestion pipeline can attach
to each chunk/vector.
"""

import json
from typing import Dict, Any

from fetch_bills import (
    fetch_bills_list,
    fetch_bill_details,
    extract_bill_metadata,
)


def summarize_bill(bill_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch detail payload for a bill and return a metadata summary.
    """

    details = fetch_bill_details(bill_summary.get('url'))
    if not details:
        return {
            'bill_number': bill_summary.get('number'),
            'error': 'Failed to fetch detailed metadata',
        }

    derived_metadata = extract_bill_metadata(details)

    return {
        'bill_number': bill_summary.get('number'),
        'title_en': (details.get('name') or {}).get('en'),
        'short_title_en': (details.get('short_title') or {}).get('en'),
        'introduced': details.get('introduced'),
        'available_fields': sorted(details.keys()),
        'metadata_summary': derived_metadata,
    }


def main(session: str = "45-1", limit: int = 2) -> None:
    bills = fetch_bills_list(session=session, limit=limit)

    if not bills:
        print("No bills returned; check session or network connectivity.")
        return

    print(f"\nInspecting metadata for {min(limit, len(bills))} bills:\n")

    for bill in bills[:limit]:
        summary = summarize_bill(bill)
        print(json.dumps(summary, indent=2, sort_keys=True))
        print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    main()
