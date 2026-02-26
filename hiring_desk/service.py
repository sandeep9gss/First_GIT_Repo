from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Dict, List, Optional

from .domain import AIResult, Application, ApplicationStatus, Candidate, Requirement
from .search_pack import build_search_pack


class HiringDeskService:
    def __init__(self) -> None:
        self.requirements: Dict[str, Requirement] = {}
        self.candidates: Dict[str, Candidate] = {}
        self.applications: Dict[str, Application] = {}
        self.req_submission_index: Dict[str, int] = defaultdict(int)
        self._req_counter = 0
        self._candidate_counter = 0
        self._application_counter = 0

    def _new_req_id(self) -> str:
        self._req_counter += 1
        return f"TWXYZ{self._req_counter:03d}"

    def create_requirement(
        self,
        title: str,
        client_name: str,
        must_have_skills: list[str],
        good_to_have_skills: list[str],
        sla_hours: int,
        recruiter_email: Optional[str] = None,
        ai_jd_version_id: Optional[str] = None,
    ) -> Requirement:
        req = Requirement(
            req_id=self._new_req_id(),
            title=title,
            client_name=client_name,
            must_have_skills=must_have_skills,
            good_to_have_skills=good_to_have_skills,
            sla_hours=sla_hours,
            recruiter_email=recruiter_email,
            ai_jd_version_id=ai_jd_version_id,
        )
        self.requirements[req.req_id] = req
        return req

    def add_candidate(
        self,
        name: str,
        email: str,
        total_experience_years: float,
        skills: list[str],
        present_ctc: float,
        expected_ctc: float,
        resume_url: Optional[str] = None,
    ) -> Candidate:
        self._candidate_counter += 1
        cid = f"C{self._candidate_counter:04d}"
        c = Candidate(
            candidate_id=cid,
            name=name,
            email=email,
            total_experience_years=total_experience_years,
            skills=skills,
            present_ctc=present_ctc,
            expected_ctc=expected_ctc,
            resume_url=resume_url,
        )
        self.candidates[cid] = c
        return c

    def _compute_ai(self, req: Requirement, candidate: Candidate, ai_model_version: str) -> AIResult:
        must_hits = len(set(s.lower() for s in req.must_have_skills) & set(s.lower() for s in candidate.skills))
        good_hits = len(set(s.lower() for s in req.good_to_have_skills) & set(s.lower() for s in candidate.skills))
        must_score = (must_hits / max(len(req.must_have_skills), 1)) * 70
        good_score = (good_hits / max(len(req.good_to_have_skills), 1)) * 30 if req.good_to_have_skills else 0
        score = round(min(100, must_score + good_score))
        top = sorted(candidate.skills)[:3]
        return AIResult(
            score=score,
            top_3_skills=top,
            must_have_match=must_hits == len(req.must_have_skills),
            model_version=ai_model_version,
        )

    def suggest_talent_pool_matches(self, req_id: str, top_n: int = 10) -> list[dict]:
        req = self.requirements[req_id]
        suggestions: list[dict] = []
        for c in self.candidates.values():
            ai = self._compute_ai(req, c, ai_model_version="sim-v1")
            suggestions.append(
                {
                    "candidate_id": c.candidate_id,
                    "candidate_name": c.name,
                    "ai_match_score": ai.score,
                    "last_submission_history": c.submission_history[-3:],
                }
            )
        return sorted(suggestions, key=lambda x: x["ai_match_score"], reverse=True)[:top_n]

    def submit_application(
        self,
        req_id: str,
        candidate_id: str,
        recruiter_email: str,
        comments: str,
        submission_channel: str,
        ai_model_version: str,
        jd_version_id: Optional[str] = None,
    ) -> dict:
        req = self.requirements[req_id]
        candidate = self.candidates[candidate_id]
        self._application_counter += 1
        app_id = f"A{self._application_counter:05d}"
        ai = self._compute_ai(req, candidate, ai_model_version=ai_model_version)

        self.req_submission_index[req_id] += 1
        order = self.req_submission_index[req_id]
        warnings: List[str] = []
        if ai.score < 50:
            warnings.append("Low AI score warning")
        if not ai.must_have_match:
            warnings.append("Must-have skill mismatch warning")

        app = Application(
            application_id=app_id,
            req_id=req_id,
            candidate_id=candidate_id,
            recruiter_email=recruiter_email,
            comments=comments,
            submission_channel=submission_channel,
            ai_result=ai,
            jd_version_id=jd_version_id,
            submission_order_index=order,
            first_submitted=order == 1,
            status_timestamps={ApplicationStatus.SENT.value: datetime.utcnow()},
        )
        self.applications[app_id] = app
        candidate.last_used_date = datetime.utcnow()
        candidate.submission_history.append(app_id)
        return {"application": app, "warnings": warnings}

    def update_application_status(self, application_id: str, status: ApplicationStatus, rejection_reason: Optional[str] = None) -> Application:
        app = self.applications[application_id]
        app.status = status
        app.status_timestamps[status.value] = datetime.utcnow()
        if rejection_reason:
            app.rejection_reason = rejection_reason
        return app

    def requirement_health(self, req_id: str) -> dict:
        req = self.requirements[req_id]
        req_apps = [a for a in self.applications.values() if a.req_id == req_id]
        days_open = (datetime.utcnow() - req.created_at).days
        avg_score = round(mean([a.ai_result.score for a in req_apps]), 2) if req_apps else 0.0
        first_submission_hours = None
        if req_apps:
            first = min(req_apps, key=lambda a: a.submitted_at)
            first_submission_hours = round((first.submitted_at - req.created_at).total_seconds() / 3600, 2)

        pending_feedback = len([a for a in req_apps if a.status in {ApplicationStatus.SENT, ApplicationStatus.L1, ApplicationStatus.L2}])
        if first_submission_hours is None or first_submission_hours > req.sla_hours:
            badge = "🔴 At Risk"
        elif avg_score < 55 or pending_feedback > 10:
            badge = "🟡 Slow"
        else:
            badge = "🟢 Healthy"

        return {
            "req_id": req_id,
            "days_open": days_open,
            "submissions_count": len(req_apps),
            "avg_ai_score": avg_score,
            "time_to_first_submission_hours": first_submission_hours,
            "pending_feedback_count": pending_feedback,
            "badge": badge,
        }

    def generate_tracker(self, req_id: str, client_name: str, include_recruiter_name: bool = False) -> list[dict]:
        req_apps = sorted(
            [a for a in self.applications.values() if a.req_id == req_id],
            key=lambda a: a.submission_order_index,
        )
        rows = []
        sl_no = 1
        for app in req_apps:
            if client_name in app.client_sent_log:
                continue
            c = self.candidates[app.candidate_id]
            row = {
                "sl_no": sl_no,
                "candidate_name": c.name,
                "experience": c.total_experience_years,
                "skillset_or_role": ", ".join(c.skills[:5]),
                "ai_score": app.ai_result.score,
                "top_3_skills": ", ".join(app.ai_result.top_3_skills),
                "present_ctc": c.present_ctc,
                "expected_ctc": c.expected_ctc,
                "recruiter_comments": app.comments,
                "status": app.status.value,
                "submission_date": app.submitted_at.date().isoformat(),
                "profile_age_days": (datetime.utcnow() - app.submitted_at).days,
            }
            if include_recruiter_name:
                row["recruiter_name"] = app.recruiter_email
            rows.append(row)
            app.client_sent_log[client_name] = datetime.utcnow()
            sl_no += 1
        return rows

    def smart_search_pack(self, req_id: str) -> dict:
        req = self.requirements[req_id]
        return build_search_pack(req.title, req.must_have_skills, req.good_to_have_skills)

    def feedback_velocity(self, req_id: str) -> dict:
        req_apps = [a for a in self.applications.values() if a.req_id == req_id]
        pending = [a for a in req_apps if a.status in {ApplicationStatus.SENT, ApplicationStatus.L1, ApplicationStatus.L2}]
        ages = [int((datetime.utcnow() - a.submitted_at).days) for a in pending]
        bucket_0_3 = len([d for d in ages if d <= 3])
        bucket_4_7 = len([d for d in ages if 4 <= d <= 7])
        bucket_7_plus = len([d for d in ages if d > 7])
        avg_response = round(mean(ages), 2) if ages else 0.0
        return {
            "profiles_pending_feedback": len(pending),
            "avg_client_response_time_days": avg_response,
            "aging_buckets": {"0-3": bucket_0_3, "4-7": bucket_4_7, "7+": bucket_7_plus},
        }

    def recruiter_dashboard(self, recruiter_email: str) -> dict:
        my_reqs = [r for r in self.requirements.values() if r.recruiter_email == recruiter_email]
        my_apps_today = [
            a for a in self.applications.values() if a.recruiter_email == recruiter_email and a.submitted_at.date() == datetime.utcnow().date()
        ]
        team_today = [a for a in self.applications.values() if a.submitted_at.date() == datetime.utcnow().date()]
        team_avg = round(len(team_today) / max(len(set(a.recruiter_email for a in team_today)), 1), 2)
        return {
            "my_active_requirements": [r.req_id for r in my_reqs],
            "sla_countdown_hours": {
                r.req_id: max(0, r.sla_hours - round((datetime.utcnow() - r.created_at).total_seconds() / 3600, 2)) for r in my_reqs
            },
            "submissions_today": len(my_apps_today),
            "team_avg_submissions_today": team_avg,
        }

    def admin_dashboard(self) -> dict:
        per_recruiter: dict[str, list[Application]] = defaultdict(list)
        for app in self.applications.values():
            per_recruiter[app.recruiter_email].append(app)
        recruiter_stats = {
            recruiter: {
                "profiles_submitted": len(apps),
                "avg_ai_score": round(mean(a.ai_result.score for a in apps), 2) if apps else 0.0,
                "l1_l2_conversion": round(
                    len([a for a in apps if a.status in {ApplicationStatus.L1, ApplicationStatus.L2, ApplicationStatus.SELECTED}])
                    / max(len(apps), 1)
                    * 100,
                    2,
                ),
            }
            for recruiter, apps in per_recruiter.items()
        }
        fresh = len([a for a in self.applications.values() if a.submission_channel == "fresh"])
        reused = len([a for a in self.applications.values() if a.submission_channel == "talent_pool"])
        return {
            "recruiter_stats": recruiter_stats,
            "fresh_vs_reused_submission_ratio": {"fresh": fresh, "reused": reused},
        }
