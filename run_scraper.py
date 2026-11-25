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
from scrapers.hopkins import fetch_hopkins_jobs
from scrapers.mount_sinai import fetch_mount_sinai_jobs
from scrapers.medstar import fetch_medstar_jobs
from scrapers.inova import fetch_inova_jobs
from scrapers.nyu_langone import fetch_nyu_langone_jobs
from scrapers.pagny import fetch_nychhc_jobs
from scrapers.mskcc import fetch_mskcc_jobs
from scrapers.hss import fetch_hss_jobs
from scrapers.montefiore import fetch_montefiore_jobs
from scrapers.maimonides import fetch_maimonides_jobs
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

    hopkins_jobs = fetch_hopkins_jobs()
    print(f"  -> Suburban & Sibley / Johns Hopkins (MD/DC): {len(hopkins_jobs)} eligible listings found.")

    medstar_jobs = fetch_medstar_jobs()
    print(f"  -> MedStar Health (MD & DC): {len(medstar_jobs)} eligible listings found.")

    inova_jobs = fetch_inova_jobs()
    print(f"  -> Inova Health System (Northern Virginia): {len(inova_jobs)} eligible listings found.")

    nyp_jobs = fetch_nyp_jobs()
    print(f"  -> NewYork-Presbyterian (NYC): {len(nyp_jobs)} eligible listings found.")

    mount_sinai_jobs = fetch_mount_sinai_jobs()
    print(f"  -> Mount Sinai Health System (NYC): {len(mount_sinai_jobs)} eligible listings found.")

    nyu_jobs = fetch_nyu_langone_jobs()
    print(f"  -> NYU Langone Health (NYC): {len(nyu_jobs)} eligible listings found.")

    nychhc_jobs = fetch_nychhc_jobs()
    print(f"  -> NYC Health + Hospitals / PAGNY (NYC): {len(nychhc_jobs)} eligible listings found.")

    mskcc_jobs = fetch_mskcc_jobs()
    print(f"  -> Memorial Sloan Kettering / MSKCC (NYC): {len(mskcc_jobs)} eligible listings found.")

    hss_jobs = fetch_hss_jobs()
    print(f"  -> Hospital for Special Surgery / HSS (NYC): {len(hss_jobs)} eligible listings found.")

    montefiore_jobs = fetch_montefiore_jobs()
    print(f"  -> Montefiore Health System (NYC - Bronx): {len(montefiore_jobs)} eligible listings found.")

    maimonides_jobs = fetch_maimonides_jobs()
    print(f"  -> Maimonides Medical Center (NYC - Brooklyn): {len(maimonides_jobs)} eligible listings found.")

    all_jobs = (
        holy_cross_jobs
        + adventist_jobs
        + hopkins_jobs
        + medstar_jobs
        + inova_jobs
        + nyp_jobs
        + mount_sinai_jobs
        + nyu_jobs
        + nychhc_jobs
        + mskcc_jobs
        + hss_jobs
        + montefiore_jobs
        + maimonides_jobs
    )
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
