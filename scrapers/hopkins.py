import json
import re
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import is_title_eligible, evaluate_new_grad, detect_specialty, extract_salary_range, detect_shift, extract_posting_requirements

HOPKINS_SEARCH_URLS = [
    # Suburban Hospital (Bethesda, MD)
    "https://jobs.hopkinsmedicine.org/jobs/us-md-bethesda/",
    "https://jobs.hopkinsmedicine.org/jobs/advanced-practice-providers/us-md-bethesda/",
    "https://jobs.hopkinsmedicine.org/jobs/physician-assistant/us-md-bethesda/",
    # Sibley Memorial Hospital (DC / MD Border)
    "https://jobs.hopkinsmedicine.org/jobs/us-dc-washington/",
    "https://jobs.hopkinsmedicine.org/jobs/advanced-practice-providers/us-dc-washington/",
    "https://jobs.hopkinsmedicine.org/jobs/physician-assistant/us-dc-washington/",
]

def fetch_hopkins_jobs() -> List[JobPosting]:
    """
    Fetch active PA postings for Suburban Hospital / Johns Hopkins Medicine in Montgomery County (Bethesda, MD).
    Parses structured JSON-LD JobPosting schema from official career pages.
    """
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # 1. Collect unique job detail URLs in Bethesda / Suburban Hospital
    detail_urls = set()
    for s_url in HOPKINS_SEARCH_URLS:
        try:
            req = urllib.request.Request(s_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'href="(/job/[^"]+)"', html)
                for path in matches:
                    detail_urls.add(f"https://jobs.hopkinsmedicine.org{path}")
        except Exception as e:
            print(f"[Hopkins Scraper] Error collecting from {s_url}: {e}")

    postings = []
    seen_ids = set()

    # 2. Parse JobPosting JSON-LD for each requisition
    for url in detail_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
                
                for b in blocks:
                    try:
                        data = json.loads(b.strip())
                    except Exception:
                        continue

                    if data.get("@type") != "JobPosting":
                        continue

                    title = data.get("title", "")
                    
                    # Strictly require title eligibility (e.g. PA, APP; exclude Medical Assistant, Lead, etc.)
                    if not is_title_eligible(title):
                        continue

                    # Strictly require Full-Time (exclude Part-Time / PRN)
                    emp_type = str(data.get("employmentType", "")).upper()
                    if "FULL" not in emp_type:
                        continue

                    # Extract location details
                    loc_data = data.get("jobLocation", {}).get("address", {})
                    street = loc_data.get("streetAddress", "Suburban Hospital")
                    city = loc_data.get("addressLocality", "Bethesda")
                    state = loc_data.get("addressRegion", "MD")
                    location = f"{city}, {state}" if city else "Bethesda, MD"
                    
                    # Format hospital name and facility
                    full_context = f"{street} {city} {url}".lower()
                    if "sibley" in full_context:
                        hospital_name = "Sibley Memorial Hospital (Johns Hopkins)"
                        location = "Washington, DC (MD Border)"
                    elif "suburban" in full_context:
                        hospital_name = "Suburban Hospital (Johns Hopkins)"
                        location = "Bethesda, MD"
                    else:
                        hospital_name = f"Johns Hopkins Medicine ({street})"
                        location = f"{city}, {state}" if city else "Maryland"

                    # Extract requisition ID from URL path (e.g. /job/101276/...)
                    req_id_match = re.search(r'/job/(\d+)/', url)
                    req_id = req_id_match.group(1) if req_id_match else url
                    if req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    desc_text = data.get("description", "")
                    date_posted = data.get("datePosted", "Recently")

                    # Evaluate new grad viability and clinical specialty
                    is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, desc_text)
                    salary_range, salary_min = extract_salary_range(desc_text)
                    shift = detect_shift(title, desc_text)
                    requirements = extract_posting_requirements(title, desc_text)

                    job = JobPosting(
                        id=JobPosting.make_id("Hopkins", req_id),
                        hospital=hospital_name,
                        title=title,
                        location=location,
                        url=url,
                        posted_date=date_posted,
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
                        raw_data=data,
                    )
                    postings.append(job)
        except Exception as e:
            print(f"[Hopkins Scraper] Error fetching detail {url}: {e}")

    return postings
