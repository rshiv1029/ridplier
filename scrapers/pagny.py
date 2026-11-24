"""
NYC Health + Hospitals / PAGNY Scraper
Scrapes open Physician Assistant roles across NYC Health + Hospitals facilities
via the Physician Affiliate Group of New York (PAGNY) portal.
Covers NYC public acute care hospitals:
- Jacobi Medical Center (Bronx)
- Lincoln Medical Center (Bronx)
- North Central Bronx Hospital (Bronx)
- Harlem Hospital Center (Manhattan)
- Metropolitan Hospital Center (Manhattan)
- Kings County Hospital Center (Brooklyn)
- South Brooklyn Health / Coney Island Hospital (Brooklyn)
- Elmhurst Hospital Center (Queens)
- Queens Hospital Center (Queens)
- Correctional Health Services (NYC)
All roles are strictly inside New York City (5 boroughs).
"""

import ssl
import urllib.request
from typing import List
from bs4 import BeautifulSoup

from scrapers.evaluator import (
    detect_specialty,
    evaluate_new_grad,
    is_title_eligible,
)
from scrapers.models import JobPosting

PAGNY_BASE_URL = "https://www.pagny.org/careers/search"

FACILITY_BOROUGH_MAP = {
    "jacobi": "Bronx",
    "lincoln": "Bronx",
    "north central bronx": "Bronx",
    "harlem": "Manhattan",
    "metropolitan": "Manhattan",
    "bellevue": "Manhattan",
    "kings county": "Brooklyn",
    "south brooklyn health": "Brooklyn",
    "coney island": "Brooklyn",
    "elmhurst": "Queens",
    "queens": "Queens",
    "correctional health": "NYC (Correctional Health)",
}


def fetch_pagny_jobs() -> List[JobPosting]:
    """Scrape PA positions from NYC Health + Hospitals via PAGNY."""
    print("[NYC H+H / PAGNY Scraper] Fetching listings from pagny.org...")
    postings: List[JobPosting] = []
    seen_urls = set()

    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # PAGNY currently spans ~14-15 search pages
    for page in range(1, 20):
        url = f"{PAGNY_BASE_URL}/p{page}" if page > 1 else PAGNY_BASE_URL
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".listing--job")
            if not cards:
                break

            for card in cards:
                dept_el = card.select_one(".job__dept")
                dept = dept_el.get_text(strip=True) if dept_el else ""

                title_el = card.select_one(".job__title a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                job_url = title_el.get("href", "")

                if not job_url or job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                # Filter strictly for Physician Assistant roles
                is_pa = (
                    "physician assistant" in dept.lower()
                    or "physician assistant" in title.lower()
                    or " pa " in f" {title.lower()} "
                )
                if not is_pa:
                    continue

                if not is_title_eligible(title):
                    continue

                partner_el = card.select_one(".job__partner")
                partner_text = partner_el.get_text(separator=" - ", strip=True) if partner_el else "NYC Health + Hospitals"

                posted_el = card.select_one(".job__posted")
                posted_date = (
                    posted_el.get_text(strip=True).replace("Posted", "").strip()
                    if posted_el
                    else "Recently"
                )

                # Determine borough from facility name
                borough = "NYC (5 Boroughs)"
                p_low = partner_text.lower()
                for key, b in FACILITY_BOROUGH_MAP.items():
                    if key in p_low:
                        borough = b
                        break

                req_slug = job_url.rstrip("/").split("/")[-1]

                # Evaluate new grad viability & specialty
                is_friendly, probability, reason = evaluate_new_grad(title, partner_text)
                if not is_friendly:
                    continue

                specialty, is_top = detect_specialty(title, partner_text)

                job = JobPosting(
                    id=JobPosting.make_id("NYCHHC", req_slug),
                    hospital=f"NYC Health + Hospitals ({partner_text})",
                    title=title,
                    location=f"New York City ({borough}), NY",
                    url=job_url,
                    posted_date=posted_date,
                    is_new_grad_friendly=is_friendly,
                    match_reason=reason,
                    hub="NYC",
                    probability=probability,
                    specialty=specialty,
                    is_top_specialty=is_top,
                    is_outside_nyc=False,
                    borough_tag=borough,
                    raw_data={"slug": req_slug, "partner": partner_text},
                )
                postings.append(job)

        except Exception as e:
            print(f"[NYC H+H / PAGNY Scraper] Finished or reached end on page {page}: {e}")
            break

    print(f"[NYC H+H / PAGNY Scraper] Successfully parsed {len(postings)} eligible new-grad roles.")
    return postings


fetch_nychhc_jobs = fetch_pagny_jobs


if __name__ == "__main__":
    jobs = fetch_pagny_jobs()
    for j in jobs[:10]:
        print(f"[{j.specialty}] 🗽 IN-CITY ({j.borough_tag}) {j.hospital}: {j.title}")
