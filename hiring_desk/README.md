# Thinkwise Hiring Desk (SRS v1.4) – Core Domain Prototype

This module implements a runnable, in-memory backend domain layer aligned to the SRS provided for **Thinkwise Hiring Desk**.

## What is covered

- Requirement creation with `TWXYZ001` style IDs
- Must-have / good-to-have skills + SLA fields
- Candidate talent pool storage
- Submission flow with:
  - submission timestamp
  - submission order index
  - first-submitted marker
  - AI score + top skills + must-have confirmation
  - soft warnings for low score and skill mismatch
- Requirement health indicator (`🟢 / 🟡 / 🔴`)
- Client tracker generation with duplicate-send prevention and order preservation
- Recruiter dashboard and admin dashboard metrics
- Talent pool match suggestions
- Smart Search Pack generation (Boolean + X-Ray variants)
- Feedback velocity monitor buckets

## Quick run

```bash
python -m pytest hiring_desk/tests -q
```

## Notes

- This is an in-memory prototype for rapid iteration.
- It is ready to be wrapped with a REST API (FastAPI/Django/etc.) and persistent storage.
