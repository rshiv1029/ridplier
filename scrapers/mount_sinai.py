import json
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import (
    is_title_eligible,
    evaluate_new_grad,
    detect_specialty,
    classify_nyc_location,
    extract_salary_range,
    detect_shift,
    extract_posting_requirements,
)

MOUNT_SINAI_API = "https://careers.mountsinai.org/api/jobs?keywords=physician%20assistant&page={page}&limit=100&sortBy=posted_date&descending=true"

def fetch_mount_sinai_jobs() -> List[JobPosting]:
    """
    Fetch active PA postings from Mount Sinai Health System across NYC
    (Manhattan, Brooklyn, Queens) via the public Jibe REST API.
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
        url = MOUNT_SINAI_API.format(page=page)
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
                    
                    # Strictly require title eligibility
                    if not is_title_eligible(title):
                        continue

                    # Strictly require Full-Time (exclude Part-Time / Per Diem)
                    emp_type = str(d.get("employment_type", "")).upper()
                    if "FULL" not in emp_type:
                        continue

                    req_id = str(d.get("req_id", d.get("slug", "")))
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    location = d.get("full_location") or "New York, NY"
                    job_url = f"https://careers.mountsinai.org/jobs/{req_id}"
                    posted_date = str(d.get("posted_date", "Recently"))[:10]
                    desc_text = d.get("description", "")

                    is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, desc_text)
                    is_outside, borough = classify_nyc_location(location, title)
                    salary_range, salary_min = extract_salary_range(
                        desc_text,
                        min_val=d.get("salary_min_value"),
                        max_val=d.get("salary_max_value"),
                    )
                    shift = detect_shift(title, desc_text, explicit_shift=str(d.get("shift") or ""))
                    requirements = extract_posting_requirements(title, desc_text)

                    job = JobPosting(
                        id=JobPosting.make_id("MountSinai", req_id),
                        hospital="Mount Sinai Health System",
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
                    postings.append(job)

                fetched_raw += len(items)
                if fetched_raw >= total_count or len(items) < 100:
                    break
        except Exception as e:
            print(f"[Mount Sinai Scraper] Error on page {page}: {e}")
            break

    return postings
