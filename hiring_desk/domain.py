from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Role(str, Enum):
    RECRUITER = "recruiter"
    ADMIN = "admin"


class ApplicationStatus(str, Enum):
    SENT = "sent"
    L1 = "l1"
    L2 = "l2"
    SELECTED = "selected"
    REJECTED = "rejected"


@dataclass
class Requirement:
    req_id: str
    title: str
    client_name: str
    must_have_skills: List[str]
    good_to_have_skills: List[str]
    sla_hours: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    recruiter_email: Optional[str] = None
    ai_jd_version_id: Optional[str] = None


@dataclass
class Candidate:
    candidate_id: str
    name: str
    email: str
    total_experience_years: float
    skills: List[str]
    present_ctc: float
    expected_ctc: float
    resume_url: Optional[str] = None
    last_used_date: Optional[datetime] = None
    submission_history: List[str] = field(default_factory=list)


@dataclass
class AIResult:
    score: int
    top_3_skills: List[str]
    must_have_match: bool
    model_version: str


@dataclass
class Application:
    application_id: str
    req_id: str
    candidate_id: str
    recruiter_email: str
    comments: str
    submission_channel: str  # fresh | talent_pool
    ai_result: AIResult
    jd_version_id: Optional[str]
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    submission_order_index: int = 0
    first_submitted: bool = False
    status: ApplicationStatus = ApplicationStatus.SENT
    status_timestamps: Dict[str, datetime] = field(default_factory=dict)
    client_sent_log: Dict[str, datetime] = field(default_factory=dict)
    rejection_reason: Optional[str] = None
