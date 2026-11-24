import json
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import is_title_eligible, evaluate_new_grad

ADVENTIST_URL = "https://adventisthealthcare.wd1.myworkdayjobs.com/wday/cxs/adventisthealthcare/AdventistHealthCareCareers/jobs"

def fetch_adventist_jobs() -> List[JobPosting]:
    """Fetch active PA postings from Adventist HealthCare (Shady Grove in Rockville & White Oak in Silver Spring)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    ctx = ssl._create_unverified_context()
    postings = []
    offset = 0
    max_postings = 40

    while offset < max_postings:
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": offset,
            "searchText": "physician assistant",
        }
        req = urllib.request.Request(ADVENTIST_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
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
                    full_url = f"https://adventisthealthcare.wd1.myworkdayjobs.com/en-US/AdventistHealthCareCareers{ext_path}"
                    req_id = ext_path.split("_")[-1] if "_" in ext_path else ext_path
                    location = item.get("locationsText", "Rockville / Silver Spring, MD")

                    # Fetch exact job posting detail for true posting date and description
                    posted_date = "Recently"
                    desc_text = ""
                    try:
                        detail_url = f"https://adventisthealthcare.wd1.myworkdayjobs.com/wday/cxs/adventisthealthcare/AdventistHealthCareCareers{ext_path}"
                        d_req = urllib.request.Request(detail_url, headers=headers)
                        with urllib.request.urlopen(d_req, context=ctx, timeout=10) as d_resp:
                            info = json.loads(d_resp.read().decode("utf-8")).get("jobPostingInfo", {})
                            posted_on = info.get("postedOn")
                            start_date = info.get("startDate")
                            if posted_on:
                                posted_date = posted_on
                            elif start_date:
                                posted_date = f"Posted {start_date}"
                            desc_text = info.get("jobDescription", "")
                    except Exception as err:
                        print(f"[Adventist Scraper] Could not fetch detail for {req_id}: {err}")

                    is_friendly, reason = evaluate_new_grad(title, desc_text)

                    job = JobPosting(
                        id=JobPosting.make_id("Adventist", req_id),
                        hospital="Adventist HealthCare (Shady Grove / White Oak)",
                        title=title,
                        location=location,
                        url=full_url,
                        posted_date=posted_date,
                        is_new_grad_friendly=is_friendly,
                        match_reason=reason,
                        hub="MD",
                        raw_data=item,
                    )
                    postings.append(job)
                offset += 20
        except Exception as e:
            print(f"[Adventist Scraper] Error fetching jobs at offset {offset}: {e}")
            break

    return postings
