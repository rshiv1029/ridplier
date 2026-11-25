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
)

NYP_URL = "https://nyp.wd1.myworkdayjobs.com/wday/cxs/nyp/nypcareers/jobs"

def fetch_nyp_jobs() -> List[JobPosting]:
    """Fetch active PA postings from NewYork-Presbyterian (NYP)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    ctx = ssl._create_unverified_context()
    postings = []
    offset = 0
    max_postings = 120

    while offset < max_postings:
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": offset,
            "searchText": "physician assistant",
        }
        req = urllib.request.Request(NYP_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("jobPostings", [])
                if not items:
                    break
                for item in items:
                    title = item.get("title", "")
                    if not is_title_eligible(title):
                        continue

                    ext_path = item.get("externalPath", "")
                    full_url = f"https://nyp.wd1.myworkdayjobs.com/en-US/nypcareers{ext_path}"
                    req_id = ext_path.split("_")[-1] if "_" in ext_path else ext_path
                    location = item.get("locationsText", "NYC Metro")

                    # Fetch job description for deep evaluation
                    desc_text = ""
                    try:
                        detail_url = f"https://nyp.wd1.myworkdayjobs.com/wday/cxs/nyp/nypcareers{ext_path}"
                        d_req = urllib.request.Request(detail_url, headers=headers)
                        with urllib.request.urlopen(d_req, context=ctx, timeout=10) as d_resp:
                            info = json.loads(d_resp.read().decode("utf-8")).get("jobPostingInfo", {})
                            desc_text = info.get("jobDescription", "")
                    except Exception:
                        pass

                    is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, desc_text)
                    is_outside, borough = classify_nyc_location(location, title)
                    salary_range, salary_min = extract_salary_range(desc_text)
                    shift = detect_shift(title, desc_text)

                    job = JobPosting(
                        id=JobPosting.make_id("NYP", req_id),
                        hospital="NewYork-Presbyterian (NYP)",
                        title=title,
                        location=location,
                        url=full_url,
                        posted_date=item.get("postedOn", "Recently"),
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
                        raw_data=item,
                    )
                    postings.append(job)
                offset += 20
        except Exception as e:
            print(f"[NYP Scraper] Error fetching jobs at offset {offset}: {e}")
            break

    return postings
