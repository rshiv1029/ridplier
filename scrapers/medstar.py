import json
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import (
    is_title_eligible,
    evaluate_new_grad,
    detect_specialty,
    extract_salary_range,
    detect_shift,
    extract_posting_requirements,
)

MEDSTAR_API = "https://careers.medstarhealth.org/api/jobs?keywords=physician%20assistant&page={page}&limit=100&sortBy=posted_date&descending=true"

def fetch_medstar_jobs() -> List[JobPosting]:
    """
    Fetch active PA postings from MedStar Health across Maryland (including MedStar Montgomery in Olney)
    and the Washington DC metro area via the public Jibe REST API.
    """
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    postings = []
    seen_ids = set()
    fetched_raw = 0

    for page in range(1, 11):
        url = MEDSTAR_API.format(page=page)
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
                    title = d.get("title", "")

                    # Strictly require title eligibility (e.g. PA, APP; exclude Medical Assistant)
                    if not is_title_eligible(title):
                        continue

                    # Strictly require Full-Time (exclude Part-Time / Per Diem / PRN)
                    emp_type = str(d.get("employment_type", "")).upper()
                    if "FULL" not in emp_type:
                        continue

                    req_id = str(d.get("req_id", d.get("slug", "")))
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    location = d.get("full_location") or "Maryland / DC"
                    job_url = f"https://careers.medstarhealth.org/careers-home/jobs/{req_id}"
                    posted_date = str(d.get("posted_date", "Recently"))[:10]
                    desc_text = d.get("description", "")

                    # Format facility name if identifiable
                    facility_tag = "MedStar Health"
                    loc_lower = location.lower()
                    title_lower = title.lower()
                    if "montgomery" in loc_lower or "olney" in loc_lower or "montgomery" in title_lower:
                        facility_tag = "MedStar Montgomery (Olney, MD)"
                    elif "georgetown" in loc_lower or "georgetown" in title_lower:
                        facility_tag = "MedStar Georgetown University Hospital"
                    elif "washington hospital center" in loc_lower or "whc" in title_lower or "washington hospital center" in title_lower:
                        facility_tag = "MedStar Washington Hospital Center (DC)"
                    elif "promptcare" in loc_lower or "urgent care" in title_lower or "urgent care" in loc_lower:
                        facility_tag = "MedStar Health Urgent Care"

                    is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, desc_text)
                    salary_range, salary_min = extract_salary_range(
                        desc_text,
                        min_val=d.get("salary_min_value"),
                        max_val=d.get("salary_max_value"),
                    )
                    shift = detect_shift(title, desc_text, explicit_shift=str(d.get("shift") or ""))
                    requirements = extract_posting_requirements(title, desc_text)

                    job = JobPosting(
                        id=JobPosting.make_id("MedStar", req_id),
                        hospital=facility_tag,
                        title=title,
                        location=location,
                        url=job_url,
                        posted_date=posted_date,
                        is_new_grad_friendly=is_friendly,
                        match_reason=reason,
                        hub="MD",
                        probability=probability,
                        specialty=specialty,
                        is_top_specialty=is_top,
                        salary_range=salary_range,
                        salary_min_annual=salary_min,
                        shift=shift,
                        requirements=requirements,
                        raw_data=d,
                    )
                    postings.append(job)

                fetched_raw += len(items)
                if fetched_raw >= total_count or len(items) < 100:
                    break
        except Exception as e:
            print(f"[MedStar Scraper] Error on page {page}: {e}")
            break

    return postings
