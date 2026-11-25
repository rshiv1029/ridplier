"""
Shared Workday CXS REST API helper used across Workday-hosted hospital networks.
Handles paginated search, concurrent detail fetching, Full-Time checks, NP-only exclusion,
salary/shift/requirement extraction, and NYC borough vs suburb classification.
"""

import json
import re
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

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


def fetch_workday_jobs(
    host: str,
    tenant: str,
    site: str,
    hospital_name: str,
    id_prefix: str,
    hub: str = "NYC",
    search_terms: Optional[List[str]] = None,
    max_per_term: int = 160,
    default_location: str = "New York, NY",
    location_filter: Optional[Callable[[str, str, Dict], Optional[str]]] = None,
) -> List[JobPosting]:
    """
    Fetch eligible Full-Time PA/APP postings from a Workday CXS portal.
    location_filter(title, location_str, info_dict) -> normalized location string, or None to exclude out-of-region jobs.
    """
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    base_cxs = f"https://{host}/wday/cxs/{tenant}/{site}"
    terms = search_terms or ["physician assistant"]

    seen_paths = set()
    raw_items: List[Dict] = []

    for kw in terms:
        offset = 0
        total_expected = None
        while offset < max_per_term:
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": kw}
            req = urllib.request.Request(f"{base_cxs}/jobs", data=json.dumps(payload).encode("utf-8"), headers=headers)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                items = data.get("jobPostings", [])
                if total_expected is None:
                    total_expected = data.get("total", 0)
                if not items:
                    break
                added_on_page = 0
                for it in items:
                    title = it.get("title", "")
                    ext_path = it.get("externalPath", "")
                    if not ext_path or ext_path in seen_paths:
                        continue
                    seen_paths.add(ext_path)
                    added_on_page += 1
                    if is_title_eligible(title):
                        raw_items.append(it)
                offset += len(items)
                if added_on_page == 0 or (total_expected is not None and offset >= total_expected) or len(items) < 20:
                    break
            except Exception as e:
                print(f"[{hospital_name} Scraper] Error at offset {offset} (kw={kw}): {e}")
                break

    def _fetch_detail(ext_path: str) -> Dict:
        try:
            d_req = urllib.request.Request(f"{base_cxs}{ext_path}", headers=headers)
            with urllib.request.urlopen(d_req, context=ctx, timeout=12) as d_resp:
                return json.loads(d_resp.read().decode("utf-8")).get("jobPostingInfo", {})
        except Exception:
            return {}

    with ThreadPoolExecutor(max_workers=6) as pool:
        details = list(pool.map(lambda it: _fetch_detail(it["externalPath"]), raw_items))

    postings: List[JobPosting] = []
    seen_ids = set()

    for it, info in zip(raw_items, details):
        title = (info.get("title") or it.get("title") or "").strip()
        ext_path = it.get("externalPath", "")
        req_id = ext_path.split("_")[-1] if "_" in ext_path else ext_path
        if not req_id or req_id in seen_ids:
            continue

        # Strictly exclude Part-Time / Per Diem / Casual
        time_type = str(info.get("timeType") or "").lower()
        if any(x in time_type for x in ["part time", "part-time", "per diem", "prn", "casual", "temporary"]):
            continue

        desc_text = info.get("jobDescription", "")
        desc_clean = re.sub(r"<[^>]+>", " ", desc_text).lower()

        # If title is generic APP, reject roles that require NP exclusively without PA
        t_low = title.lower()
        is_explicit_pa_title = bool(re.search(r"\b(physician\s+assistant|physician\s+asst|pa-c|pa)\b", t_low))
        if not is_explicit_pa_title:
            mentions_np = "nurse practitioner" in desc_clean or "aprn" in desc_clean
            mentions_pa = "physician assistant" in desc_clean or "pa-c" in desc_clean
            if mentions_np and not mentions_pa:
                continue

        loc_str = info.get("location") or it.get("locationsText") or default_location
        if loc_str.lower() == "2 locations" and info.get("additionalLocations"):
            loc_str = f"{loc_str} ({', '.join(info['additionalLocations'][:2])})"

        if location_filter is not None:
            filtered_loc = location_filter(title, loc_str, info)
            if filtered_loc is None:
                continue
            loc_str = filtered_loc

        is_friendly, probability, reason = evaluate_new_grad(title, desc_text)
        if not is_friendly:
            continue

        seen_ids.add(req_id)
        specialty, is_top = detect_specialty(title, desc_text)
        if hub == "NYC":
            is_outside, borough = classify_nyc_location(loc_str, f"{title} {hospital_name}")
        else:
            is_outside, borough = False, None
        salary_range, salary_min = extract_salary_range(desc_text)
        shift = detect_shift(title, desc_text)
        requirements = extract_posting_requirements(title, desc_text)

        full_url = f"https://{host}/en-US/{site}{ext_path}"
        posted_date = info.get("postedOn") or it.get("postedOn") or "Recently"

        postings.append(
            JobPosting(
                id=JobPosting.make_id(id_prefix, req_id),
                hospital=hospital_name,
                title=title,
                location=loc_str,
                url=full_url,
                posted_date=posted_date,
                is_new_grad_friendly=is_friendly,
                match_reason=reason,
                hub=hub,
                probability=probability,
                specialty=specialty,
                is_top_specialty=is_top,
                is_outside_nyc=is_outside,
                borough_tag=borough,
                salary_range=salary_range,
                salary_min_annual=salary_min,
                shift=shift,
                requirements=requirements,
                raw_data=it,
            )
        )

    return postings
