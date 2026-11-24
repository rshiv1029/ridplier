"""
NYU Langone Health Scraper
Scrapes open Physician Assistant roles from NYU Langone Health's Radancy / m-cloud API.
Covers NYU Langone Manhattan (Tisch/Kimmel/Orthopedic), Brooklyn, Bellevue partner rotations,
and Long Island (Mineola - clearly tagged with Outside NYC warning).
"""

import json
import re
import ssl
import urllib.parse
import urllib.request
from typing import List

from scrapers.evaluator import (
    classify_nyc_location,
    detect_specialty,
    evaluate_new_grad,
    is_title_eligible,
)
from scrapers.models import JobPosting

NYU_API_URL = "https://jobsapi-internal.m-cloud.io/api/job"
ORG_ID = "1637"


def scrape_nyu_langone() -> List[JobPosting]:
    """Scrape PA positions from NYU Langone Health."""
    print("[NYU Langone Scraper] Fetching listings from Radancy m-cloud API...")
    postings: List[JobPosting] = []
    seen_ids = set()

    ctx = ssl._create_unverified_context()
    offset = 1
    limit = 100

    while True:
        params = {
            "Organization": ORG_ID,
            "SearchText": "physician assistant",
            "Limit": str(limit),
            "offset": str(offset),
            "callback": "cb",
        }
        url = f"{NYU_API_URL}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://jobs.nyulangone.org/",
                "Origin": "https://jobs.nyulangone.org",
                "Accept": "*/*",
            },
        )

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                raw_text = resp.read().decode("utf-8")
                # Parse JSONP callback
                start_idx = raw_text.find("(")
                end_idx = raw_text.rfind(")")
                if start_idx == -1 or end_idx == -1:
                    print("[NYU Langone Scraper] Invalid JSONP response format.")
                    break
                data = json.loads(raw_text[start_idx + 1 : end_idx])

            items = data.get("queryResult", [])
            total_hits = data.get("totalHits", 0)

            if not items:
                break

            for it in items:
                req_id = str(it.get("ref") or it.get("id"))
                if req_id in seen_ids:
                    continue
                seen_ids.add(req_id)

                title = it.get("title", "").strip()
                if not is_title_eligible(title):
                    continue

                # Strictly full-time filter
                sched = (it.get("schedule") or it.get("employment_type") or "").lower()
                if any(x in sched for x in ["part-time", "part time", "per diem", "prn", "temporary", "casual"]):
                    continue

                city = it.get("primary_city") or ""
                state = it.get("primary_state") or ""
                location = f"{city}, {state}".strip(", ")
                if not location:
                    location = it.get("primary_address") or "New York, NY"

                job_url = it.get("url") or f"https://jobs.nyulangone.org/job/{req_id}"
                if job_url.startswith("http://"):
                    job_url = "https://" + job_url[7:]

                desc_text = it.get("description", "")
                posted_date = str(it.get("open_date") or "Recently")[:10]

                # Specific facility branding
                facility = "NYU Langone Health"
                t_low = title.lower()
                loc_low = location.lower()
                if "bellevue" in t_low or "bellevue" in desc_text.lower():
                    facility = "NYU Langone / NYC H+H Bellevue"
                elif "brooklyn" in t_low or "brooklyn" in loc_low:
                    facility = "NYU Langone Hospital - Brooklyn"
                elif "long island" in t_low or "mineola" in loc_low or "long island" in loc_low:
                    facility = "NYU Langone Hospital - Long Island (Suburbs)"
                elif "orthopedic" in t_low:
                    facility = "NYU Langone Orthopedic Hospital"

                is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                if not is_friendly:
                    continue

                specialty, is_top = detect_specialty(title, desc_text)
                is_outside, borough = classify_nyc_location(location, title)

                job = JobPosting(
                    id=JobPosting.make_id("NYULangone", req_id),
                    hospital=facility,
                    title=title,
                    location=location,
                    url=job_url,
                    posted_date=posted_date,
                    is_new_grad_friendly=is_friendly,
                    match_reason=reason,
                    hub="NYC",
                    probability=probability,
                    specialty=specialty,
                    is_top_specialty=is_top,
                    is_outside_nyc=is_outside,
                    borough_tag=borough,
                    raw_data={"id": req_id, "category": it.get("primary_category")},
                )
                postings.append(job)

            offset += len(items)
            if offset >= total_hits or len(items) < limit:
                break

        except Exception as e:
            print(f"[NYU Langone Scraper] Error fetching items at offset {offset}: {e}")
            break

    print(f"[NYU Langone Scraper] Successfully parsed {len(postings)} eligible new-grad roles.")
    return postings


fetch_nyu_langone_jobs = scrape_nyu_langone


if __name__ == "__main__":
    jobs = scrape_nyu_langone()
    for j in jobs[:10]:
        print(f"[{j.evaluation.specialty if hasattr(j, 'evaluation') else j.specialty}] "
              f"{'⚠️ OUTSIDE NYC' if j.is_outside_nyc else '🗽 IN-CITY'} "
              f"({j.borough_tag}) {j.hospital}: {j.title} | {j.location}")
