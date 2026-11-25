"""Adventist HealthCare PA Scraper (Rockville & Silver Spring, MD)."""

from typing import List
from .models import JobPosting
from .workday_common import fetch_workday_jobs


def fetch_adventist_jobs() -> List[JobPosting]:
    """Fetch active Full-Time PA postings from Adventist HealthCare (Shady Grove in Rockville & White Oak in Silver Spring)."""
    return fetch_workday_jobs(
        host="adventisthealthcare.wd1.myworkdayjobs.com",
        tenant="adventisthealthcare",
        site="AdventistHealthCareCareers",
        hospital_name="Adventist HealthCare (Shady Grove / White Oak)",
        id_prefix="Adventist",
        hub="MD",
        search_terms=["physician assistant"],
        max_per_term=140,
        default_location="Rockville / Silver Spring, MD",
    )
