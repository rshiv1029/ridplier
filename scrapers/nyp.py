import json
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import is_title_eligible, evaluate_new_grad

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
    max_postings = 60

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

                    is_friendly, reason = evaluate_new_grad(title)
                    ext_path = item.get("externalPath", "")
                    full_url = f"https://nyp.wd1.myworkdayjobs.com/en-US/nypcareers{ext_path}"
                    req_id = ext_path.split("_")[-1] if "_" in ext_path else ext_path
                    location = item.get("locationsText", "NYC Metro")

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
                        raw_data=item,
                    )
                    postings.append(job)
                offset += 20
        except Exception as e:
            print(f"[NYP Scraper] Error fetching jobs at offset {offset}: {e}")
            break

    return postings
