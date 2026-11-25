"""Maimonides Medical Center PA Scraper (Brooklyn, NY via Jibe REST API)."""

import json
import re
import ssl
import urllib.request
from typing import List
from .evaluator import (
    classify_nyc_location,
    detect_shift,
    detect_specialty,
    evaluate_new_grad,
    extract_posting_requirements,
    extract_salary_range,
    is_title_eligible,
)
from .models import JobPosting

MAIMO_API = "https://careers.maimo.org/api/jobs?keywords={kw}&page={page}&limit=100&sortBy=posted_date&descending=true"


def fetch_maimonides_jobs() -> List[JobPosting]:
    """Fetch eligible Full-Time PA postings from Maimonides Medical Center (Brooklyn, NY)."""
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    postings: List[JobPosting] = []
    seen_ids = set()

    for kw in ("physician%20asst", "physician%20assistant"):
        for page in range(1, 5):
            url = MAIMO_API.format(kw=kw, page=page)
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                items = data.get("jobs", [])
                total_count = data.get("totalCount", 0)
                if not items:
                    break

                for item in items:
                    d = item.get("data", {})
                    title = d.get("title", "").strip()
                    if not is_title_eligible(title):
                        continue

                    desc_text = d.get("description", "")
                    desc_low = re.sub(r"<[^>]+>", " ", desc_text).lower()
                    emp_type = str(d.get("employment_type") or "").upper()
                    if emp_type:
                        if "FULL" not in emp_type:
                            continue
                    else:
                        if any(x in desc_low for x in ["per diem", "part-time", "part time", "prn", "casual"]):
                            continue
                        if "full-time" not in desc_low and "full time" not in desc_low:
                            continue

                    req_id = str(d.get("req_id") or d.get("slug") or "")
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    location = d.get("full_location") or "Brooklyn, NY"
                    job_url = f"https://careers.maimo.org/jobs/{req_id}"
                    posted_date = str(d.get("posted_date", "Recently"))[:10]

                    is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, desc_text)
                    is_outside, borough = classify_nyc_location(location, f"{title} Maimonides")
                    salary_range, salary_min = extract_salary_range(
                        desc_text,
                        min_val=d.get("salary_min_value"),
                        max_val=d.get("salary_max_value"),
                    )
                    shift = detect_shift(title, desc_text, explicit_shift=str(d.get("shift") or ""))
                    requirements = extract_posting_requirements(title, desc_text)

                    postings.append(
                        JobPosting(
                            id=JobPosting.make_id("Maimonides", req_id),
                            hospital="Maimonides Medical Center",
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
                            salary_range=salary_range,
                            salary_min_annual=salary_min,
                            shift=shift,
                            requirements=requirements,
                            raw_data=d,
                        )
                    )

                if len(items) < 100 or page * 100 >= total_count:
                    break
            except Exception as e:
                print(f"[Maimonides Scraper] Error on page {page} (kw={kw}): {e}")
                break

    return postings
