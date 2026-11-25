import re
import json
import urllib.request
import urllib.parse
from typing import List
from .models import JobPosting
from .evaluator import is_title_eligible, evaluate_new_grad, detect_specialty, extract_salary_range, detect_shift

TRINITY_URL = "https://jobs.trinity-health.org/search-results?keywords=physician%20assistant"

def fetch_holy_cross_jobs() -> List[JobPosting]:
    """Fetch active PA postings from Holy Cross Health / Trinity Health in MD (Germantown & Silver Spring)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    postings = []
    seen_ids = set()

    # Paginate through top 50 results (5 pages) to catch all Maryland Holy Cross listings
    for offset in range(0, 50, 10):
        url = f"https://jobs.trinity-health.org/search-results?keywords=physician%20assistant&from={offset}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8")
                ph = re.search(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", html, re.DOTALL)
                if not ph:
                    continue

                data = json.loads(ph.group(1))
                items = data.get("eagerLoadRefineSearch", {}).get("data", {}).get("jobs", [])
                if not items:
                    break

                for item in items:
                    title = item.get("title", "")
                    state = item.get("state", "")
                    city = item.get("city", "")
                    seq_no = item.get("jobSeqNo", "")

                    if seq_no in seen_ids:
                        continue

                    # Filter specifically for Maryland (Montgomery County / Holy Cross)
                    is_md = state.lower() == "maryland" or "HOLYCROSS" in seq_no.upper()
                    if not is_md:
                        continue

                    # Strictly require Full-Time roles (exclude Part-Time / Per Diem)
                    job_type = item.get("type", "").lower()
                    if job_type and "full" not in job_type:
                        continue

                    if not is_title_eligible(title):
                        continue

                    seen_ids.add(seq_no)
                    is_friendly, probability, reason = evaluate_new_grad(title)
                    if not is_friendly:
                        continue

                    desc_text = item.get("description", "")
                    specialty, is_top = detect_specialty(title, desc_text)
                    salary_range, salary_min = extract_salary_range(desc_text)
                    shift = detect_shift(title, desc_text)

                    # Build direct job link
                    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-")
                    job_url = f"https://jobs.trinity-health.org/job/{seq_no}/{slug}"
                    location = f"{city}, MD" if city else "Montgomery County, MD"

                    job = JobPosting(
                        id=JobPosting.make_id("HolyCross", seq_no),
                        hospital="Holy Cross Health (Trinity)",
                        title=title,
                        location=location,
                        url=job_url,
                        posted_date=item.get("postedDate", "Recently")[:10],
                        is_new_grad_friendly=is_friendly,
                        match_reason=reason,
                        hub="MD",
                        probability=probability,
                        specialty=specialty,
                        is_top_specialty=is_top,
                        salary_range=salary_range,
                        salary_min_annual=salary_min,
                        shift=shift,
                        raw_data=item,
                    )
                    postings.append(job)
        except Exception as e:
            print(f"[Holy Cross Scraper] Error at offset {offset}: {e}")
            break

    return postings
