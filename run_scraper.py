#!/usr/bin/env python3
"""
Ridplier: Automated PA Job Scraper, Evaluator, and Notifier.
Scrapes direct hospital career portals (MD & NYC), evaluates new-grad viability,
sends T-Mobile SMS notifications for fresh drops, and updates the static dashboard.
"""
import json
import os
import sys
from pathlib import Path

from scrapers.holy_cross import fetch_holy_cross_jobs
from scrapers.nyp import fetch_nyp_jobs
from scrapers.adventist import fetch_adventist_jobs
from notifier import notify_new_jobs
from build_site import generate_dashboard

HERE = Path(__file__).parent
SEEN_FILE = HERE / "seen.json"
DOCS_DIR = HERE / "docs"

def load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_seen(seen: set):
    SEEN_FILE.write_text(json.dumps(sorted(list(seen)), indent=2), encoding="utf-8")

def main():
    print("=" * 60)
    print("🩺 Starting Ridplier Job Discovery Run")
    print("=" * 60)

    seen_ids = load_seen()
    print(f"[State] Loaded {len(seen_ids)} previously seen job IDs.")

    # 1. Fetch from hospital systems
    print("\n[1/3] Scraping hospital portals...")
    holy_cross_jobs = fetch_holy_cross_jobs()
    print(f"  -> Holy Cross Health (MD): {len(holy_cross_jobs)} eligible listings found.")

    adventist_jobs = fetch_adventist_jobs()
    print(f"  -> Adventist HealthCare (MD - Rockville & Silver Spring): {len(adventist_jobs)} eligible listings found.")

    nyp_jobs = fetch_nyp_jobs()
    print(f"  -> NewYork-Presbyterian (NYC): {len(nyp_jobs)} eligible listings found.")

    all_jobs = holy_cross_jobs + adventist_jobs + nyp_jobs
    print(f"[Total] Collected {len(all_jobs)} active PA postings across all target hubs.")

    # 2. Identify new jobs
    print("\n[2/3] Checking for newly posted jobs...")
    new_jobs = [j for j in all_jobs if j.id not in seen_ids]
    print(f"[Matches] Found {len(new_jobs)} brand new listings.")

    # 3. Notify via SMS
    print("\n[3/3] Dispatching notifications...")
    notify_new_jobs(new_jobs)

    # 4. Update seen state and regenerate static dashboard
    for j in all_jobs:
        seen_ids.add(j.id)
    save_seen(seen_ids)

    generate_dashboard(all_jobs, DOCS_DIR)

    print("\n" + "=" * 60)
    print("✅ Ridplier Run Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
