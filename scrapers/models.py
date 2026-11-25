from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
import hashlib

@dataclass
class JobPosting:
    id: str
    hospital: str
    title: str
    location: str
    url: str
    posted_date: str
    is_new_grad_friendly: bool
    match_reason: str
    hub: str  # "MD", "NYC", "VA"
    probability: str = "moderate"  # "high", "moderate", "lower"
    specialty: str = "General / Inpatient"
    is_top_specialty: bool = False
    is_outside_nyc: bool = False
    borough_tag: Optional[str] = None
    salary_range: Optional[str] = None
    salary_min_annual: Optional[int] = None
    shift: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def make_id(cls, hospital: str, unique_key: str) -> str:
        raw = f"{hospital}:{unique_key}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("raw_data", None)
        return d
