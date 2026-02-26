from hiring_desk.domain import ApplicationStatus
from hiring_desk.service import HiringDeskService


def test_requirement_id_and_submission_order_and_first_marker():
    svc = HiringDeskService()
    req = svc.create_requirement(
        title="Python Developer",
        client_name="Acme",
        must_have_skills=["Python", "FastAPI"],
        good_to_have_skills=["AWS"],
        sla_hours=24,
        recruiter_email="r1@thinkwise.com",
    )
    c1 = svc.add_candidate("A", "a@x.com", 5, ["Python", "FastAPI", "AWS"], 10, 15)
    c2 = svc.add_candidate("B", "b@x.com", 4, ["Python"], 8, 12)

    s1 = svc.submit_application(req.req_id, c1.candidate_id, "r1@thinkwise.com", "good", "fresh", "v1")
    s2 = svc.submit_application(req.req_id, c2.candidate_id, "r1@thinkwise.com", "ok", "talent_pool", "v1")

    assert req.req_id == "TWXYZ001"
    assert s1["application"].submission_order_index == 1
    assert s1["application"].first_submitted is True
    assert s2["application"].submission_order_index == 2
    assert s2["application"].first_submitted is False
    assert "Must-have skill mismatch warning" in s2["warnings"]


def test_tracker_deduplicates_by_client_and_preserves_order():
    svc = HiringDeskService()
    req = svc.create_requirement("Data Engineer", "Contoso", ["SQL"], ["Airflow"], 12)
    c1 = svc.add_candidate("C1", "c1@x.com", 6, ["SQL", "Airflow"], 20, 25)
    c2 = svc.add_candidate("C2", "c2@x.com", 5, ["SQL"], 18, 22)
    svc.submit_application(req.req_id, c1.candidate_id, "r@t.com", "x", "fresh", "v1")
    svc.submit_application(req.req_id, c2.candidate_id, "r@t.com", "y", "fresh", "v1")

    first = svc.generate_tracker(req.req_id, "Contoso", include_recruiter_name=True)
    second = svc.generate_tracker(req.req_id, "Contoso")

    assert len(first) == 2
    assert first[0]["sl_no"] == 1
    assert first[1]["sl_no"] == 2
    assert "recruiter_name" in first[0]
    assert second == []


def test_dashboards_and_health_and_feedback_velocity():
    svc = HiringDeskService()
    req = svc.create_requirement("SRE", "Beta", ["Linux"], ["K8s"], 8, recruiter_email="r2@thinkwise.com")
    c = svc.add_candidate("D", "d@x.com", 7, ["Linux", "K8s"], 21, 28)
    out = svc.submit_application(req.req_id, c.candidate_id, "r2@thinkwise.com", "fit", "fresh", "v2")
    app_id = out["application"].application_id
    svc.update_application_status(app_id, ApplicationStatus.L1)

    health = svc.requirement_health(req.req_id)
    recruiter = svc.recruiter_dashboard("r2@thinkwise.com")
    admin = svc.admin_dashboard()
    velocity = svc.feedback_velocity(req.req_id)
    search_pack = svc.smart_search_pack(req.req_id)

    assert health["submissions_count"] == 1
    assert recruiter["submissions_today"] == 1
    assert admin["fresh_vs_reused_submission_ratio"]["fresh"] == 1
    assert velocity["profiles_pending_feedback"] == 1
    assert "boolean" in search_pack
