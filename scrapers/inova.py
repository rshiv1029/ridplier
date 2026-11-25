import json
import ssl
import urllib.request
from typing import List
from .models import JobPosting
from .evaluator import is_title_eligible, evaluate_new_grad, detect_specialty

INOVA_API = "https://elar.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?finder=findReqs;siteNumber=CX_1,keyword=physician%20assistant,limit=100,offset={offset}&expand=requisitionList"

def fetch_inova_jobs() -> List[JobPosting]:
    """
    Fetch active PA postings from Inova Health System across Northern Virginia
    (Inova Fairfax, Inova Alexandria, Inova Loudoun, Inova Fair Oaks) via Oracle Cloud HCM.
    """
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    postings = []
    seen_ids = set()
    offset = 0
    page_size = 100
    max_total = 500

    try:
        while offset < max_total:
            req = urllib.request.Request(INOVA_API.format(offset=offset), headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                if not items:
                    break

                total_jobs = items[0].get("TotalJobsCount", 0)
                req_list = items[0].get("requisitionList", [])
                if not req_list:
                    break

                for q in req_list:
                    title = q.get("Title", "")

                    # Strictly require title eligibility (e.g. PA, APP; exclude Medical Assistant)
                    if not is_title_eligible(title):
                        continue

                    # Filter out Part-Time / PRN
                    schedule = str(q.get("JobSchedule", "")).upper()
                    if "PART" in schedule or "PRN" in schedule or "PER_DIEM" in schedule:
                        continue
                    if "PRN" in title.upper() or "PER DIEM" in title.upper():
                        continue

                    req_id = str(q.get("Id", ""))
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    loc = q.get("PrimaryLocation", "Northern Virginia")
                    # Format clean location (strip ', United States')
                    location = loc.replace(", United States", "").strip()

                    job_url = f"https://elar.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/{req_id}"
                    posted_date = str(q.get("PostedDate", "Recently"))[:10]

                    desc = q.get("ShortDescriptionStr", "")
                    quals = q.get("ExternalQualificationsStr", "")
                    resps = q.get("ExternalResponsibilitiesStr", "")
                    full_desc = f"{desc}\n{quals}\n{resps}"

                    # Identify specific Inova facility
                    hospital_name = "Inova Health System"
                    loc_lower = location.lower()
                    title_lower = title.lower()
                    if "fairfax" in loc_lower or "fairfax" in title_lower:
                        hospital_name = "Inova Fairfax Hospital (VA)"
                    elif "alexandria" in loc_lower or "alexandria" in title_lower:
                        hospital_name = "Inova Alexandria Hospital (VA)"
                    elif "loudoun" in loc_lower or "loudoun" in title_lower:
                        hospital_name = "Inova Loudoun Hospital (VA)"
                    elif "fair oaks" in loc_lower or "fair oaks" in title_lower:
                        hospital_name = "Inova Fair Oaks Hospital (VA)"

                    is_friendly, probability, reason = evaluate_new_grad(title, full_desc)
                    if not is_friendly:
                        continue

                    specialty, is_top = detect_specialty(title, full_desc)

                    job = JobPosting(
                        id=JobPosting.make_id("Inova", req_id),
                        hospital=hospital_name,
                        title=title,
                        location=location,
                        url=job_url,
                        posted_date=posted_date,
                        is_new_grad_friendly=is_friendly,
                        match_reason=reason,
                        hub="VA",
                        probability=probability,
                        specialty=specialty,
                        is_top_specialty=is_top,
                        raw_data=q,
                    )
                    postings.append(job)

                offset += len(req_list)
                if offset >= total_jobs or len(req_list) < page_size:
                    break
    except Exception as e:
        print(f"[Inova Scraper] Error fetching requisitions: {e}")

    return postings
