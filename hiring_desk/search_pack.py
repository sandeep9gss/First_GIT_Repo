from __future__ import annotations

from typing import Iterable


def _quote_terms(terms: Iterable[str]) -> str:
    cleaned = [f'"{t.strip()}"' for t in terms if t and t.strip()]
    return " OR ".join(cleaned)


def build_search_pack(job_title: str, must_have: list[str], good_to_have: list[str]) -> dict[str, str]:
    must = _quote_terms(must_have)
    good = _quote_terms(good_to_have)
    role = job_title.strip()

    boolean_query = f"({must}) AND ({good}) AND ({role})" if good else f"({must}) AND ({role})"
    linkedin_xray = f'site:linkedin.com/in ({must}) ({role})'
    google_xray = f'site:*.{role.lower().replace(" ", "")}.com ({must})'
    naukri = f"{must} {good}".strip()
    github = f"site:github.com ({must}) ({role})"

    return {
        "boolean": boolean_query,
        "naukri": naukri,
        "linkedin_xray": linkedin_xray,
        "google_xray": google_xray,
        "github": github,
    }
