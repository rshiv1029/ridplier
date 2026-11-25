"""NewYork-Presbyterian (NYP) PA Scraper (NYC Manhattan, Brooklyn, Queens, Westchester)."""

from typing import List
from .models import JobPosting
from .workday_common import fetch_workday_jobs


def fetch_nyp_jobs() -> List[JobPosting]:
    """Fetch active Full-Time PA postings from NewYork-Presbyterian (NYP)."""
    return fetch_workday_jobs(
        host="nyp.wd1.myworkdayjobs.com",
        tenant="nyp",
        site="nypcareers",
        hospital_name="NewYork-Presbyterian (NYP)",
        id_prefix="NYP",
        search_terms=["physician assistant"],
        max_per_term=120,
        default_location="NYC Metro",
    )
