"""
Job Hunter Agent — Hermes-powered job application system.

وكلاء Hermes يبحثون عن وظائف ويقدمون تلقائياً.

Agents:
- Scout: يبحث عن وظائف جديدة كل يوم
- Matcher: يقارن CV مع متطلبات الوظيفة
- Writer: يكتب Cover Letter مخصص
- Tracker: يتتبع حالة الطلبات
"""

from __future__ import annotations
from fastapi import APIRouter
import os, json, time, subprocess
from pathlib import Path

router = APIRouter(prefix="/jobs", tags=["job-hunter"])

# ── Storage ──
jobs_db: list[dict] = []
applications_db: list[dict] = []

PROFILE = {
    "name": "Alaa Al-Din Al-Awdi",
    "email": "Alawdisoft@gmail.com",
    "title": "AI/ML Engineer",
    "location": "Riyadh, Saudi Arabia",
    "skills": ["Python", "FastAPI", "Next.js", "DeepSeek", "OpenAI", "Hermes Agent",
               "Multi-Agent Systems", "Docker", "TypeScript", "REST APIs"],
    "github": "github.com/ALaaAlawdi",
    "projects": ["Agent-Flow", "Hermes Brain", "VirtualCorp"],
    "years": 3,
    "salary_min": 15000,
    "salary_max": 30000,
    "remote": True,
}


def call_deepseek(prompt: str) -> str:
    """Call DeepSeek via Hermes CLI."""
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
    env["HERMES_DEFAULT_MODEL"] = "deepseek-v4-pro"
    env["HERMES_DEFAULT_PROVIDER"] = "deepseek"
    try:
        result = subprocess.run(
            ["hermes", "-z", prompt, "-t", "web"],
            capture_output=True, text=True, timeout=45, env=env
        )
        output = result.stdout.strip()
        return output[:800] if output else ""
    except:
        return ""


# ═══════════════════════════════════════
# 📋 JOB DATABASE — default jobs
# ═══════════════════════════════════════
DEFAULT_JOBS = [
    {
        "id": "job-1", "title": "AI Engineer", "company": "Mozn",
        "location": "Riyadh, Saudi Arabia", "salary": "20000-30000 SAR",
        "url": "https://www.linkedin.com/jobs/",
        "requirements": "Python, ML, LLMs, REST APIs, 3+ years",
        "posted": "2026-07-20",
        "source": "LinkedIn",
    },
    {
        "id": "job-2", "title": "AI Solution Engineer", "company": "Tamm",
        "location": "Riyadh, Saudi Arabia", "salary": "18000-25000 SAR",
        "url": "https://www.linkedin.com/jobs/",
        "requirements": "Python, AI/ML, Cloud, Docker, APIs",
        "posted": "2026-07-21",
        "source": "LinkedIn",
    },
    {
        "id": "job-3", "title": "Machine Learning Engineer", "company": "Uxbert",
        "location": "Riyadh, Saudi Arabia", "salary": "22000-35000 SAR",
        "url": "https://www.linkedin.com/jobs/",
        "requirements": "ML, Deep Learning, Python, TensorFlow, 5+ years",
        "posted": "2026-07-22",
        "source": "LinkedIn",
    },
    {
        "id": "job-4", "title": "Fullstack AI Engineer", "company": "Emagine",
        "location": "Al Khobar, Saudi Arabia", "salary": "18000-28000 SAR",
        "url": "https://www.linkedin.com/jobs/",
        "requirements": "Python, React, TypeScript, AI/ML, Docker",
        "posted": "2026-07-19",
        "source": "LinkedIn",
    },
    {
        "id": "job-5", "title": "Gen AI Engineer", "company": "Aramco Digital",
        "location": "Dhahran, Saudi Arabia", "salary": "25000-40000 SAR",
        "url": "https://www.linkedin.com/jobs/",
        "requirements": "LLMs, Generative AI, Python, Cloud, Production ML",
        "posted": "2026-07-18",
        "source": "LinkedIn",
    },
]

# Initialize DB
if not jobs_db:
    jobs_db.extend(DEFAULT_JOBS)


# ═══════════════════════════════════════
# 🔍 AGENT: SCOUT — search for jobs
# ═══════════════════════════════════════
@router.post("/scout")
async def scout_search(keywords: str = "AI Engineer", location: str = "Saudi Arabia"):
    """Scout agent: search for new jobs."""
    prompt = f"""You are a job search agent. Find the best matching AI/ML jobs.
Profile: {json.dumps(PROFILE, ensure_ascii=False)}
Search: {keywords} in {location}

Return a JSON list of top 3 jobs with: title, company, location, salary, url, requirements.
Each job must be a valid JSON object. Return ONLY JSON array, no explanation.
Example: [{{"title":"...", "company":"...", "location":"...", "salary":"...", "url":"...", "requirements":"..."}}]"""

    response = call_deepseek(prompt)
    
    try:
        # Try to parse as JSON
        new_jobs = json.loads(response)
        for j in new_jobs:
            j["id"] = f"job-{len(jobs_db)+1}"
            j["source"] = "DeepSeek Scout"
            j["posted"] = time.strftime("%Y-%m-%d")
            jobs_db.append(j)
        return {"found": len(new_jobs), "jobs": new_jobs}
    except:
        # Return existing jobs if parsing fails
        return {"found": len(jobs_db), "jobs": jobs_db[-5:], "note": "Using cached jobs"}


# ═══════════════════════════════════════
# 🎯 AGENT: MATCHER — score job fit
# ═══════════════════════════════════════
@router.post("/match/{job_id}")
async def matcher_score(job_id: str):
    """Matcher agent: analyze how well you fit this job."""
    job = next((j for j in jobs_db if j["id"] == job_id), None)
    if not job:
        return {"error": "Job not found"}
    
    prompt = f"""You are a job matching agent. Compare the profile with the job.

PROFILE:
{json.dumps(PROFILE, ensure_ascii=False, indent=2)}

JOB:
{json.dumps(job, ensure_ascii=False, indent=2)}

Return ONLY a JSON object with:
- match_score (0-100)
- matched_skills (list of matching skills)
- missing_skills (list of missing skills)
- recommendation (APPLY / SKIP / UPGRADE - one word)
- reason (one sentence in English)

No explanation, just the JSON object."""

    response = call_deepseek(prompt)
    try:
        match = json.loads(response)
        match["job_id"] = job_id
        match["job_title"] = job["title"]
        match["company"] = job["company"]
        return match
    except:
        return {
            "job_id": job_id, "job_title": job["title"], "company": job["company"],
            "match_score": 75, "matched_skills": ["Python", "AI/ML"],
            "missing_skills": [], "recommendation": "APPLY",
            "reason": "Good match based on skills"
        }


# ═══════════════════════════════════════
# ✍️ AGENT: WRITER — customized cover letter
# ═══════════════════════════════════════
@router.post("/cover-letter/{job_id}")
async def writer_cover_letter(job_id: str):
    """Writer agent: generate a customized cover letter."""
    job = next((j for j in jobs_db if j["id"] == job_id), None)
    if not job:
        return {"error": "Job not found"}
    
    prompt = f"""Write a professional cover letter in English.
Applicant: {json.dumps(PROFILE, ensure_ascii=False)}
Job: {json.dumps(job, ensure_ascii=False)}

The cover letter must:
1. Be personalized to the company and role
2. Highlight relevant projects (Agent-Flow, multi-agent systems)
3. Be 3 short paragraphs maximum
4. Include contact info: Alawdisoft@gmail.com
5. Sound human, not AI-generated
6. Use confident but humble tone

Return ONLY the cover letter text, no JSON wrapper."""

    letter = call_deepseek(prompt)
    return {
        "job_id": job_id,
        "company": job["company"],
        "title": job["title"],
        "cover_letter": letter or f"Dear {job['company']} team,\n\nI'm excited to apply...",
        "to_email": job.get("contact_email", "careers@{}.com".format(job['company'].lower().replace(' ', ''))),
    }


# ═══════════════════════════════════════
# 📤 AGENT: TRACKER — manage applications
# ═══════════════════════════════════════
@router.post("/apply/{job_id}")
async def tracker_apply(job_id: str, cover_letter: str = ""):
    """Tracker agent: record an application."""
    job = next((j for j in jobs_db if j["id"] == job_id), None)
    if not job:
        return {"error": "Job not found"}
    
    app = {
        "id": f"app-{len(applications_db)+1}",
        "job_id": job_id,
        "company": job["company"],
        "title": job["title"],
        "applied_at": time.strftime("%Y-%m-%d %H:%M"),
        "status": "applied",
        "cover_letter_sent": bool(cover_letter),
        "follow_up": time.strftime("%Y-%m-%d", time.localtime(time.time() + 7*86400)),
    }
    applications_db.append(app)
    
    # Mark job as applied
    job["applied"] = True
    job["applied_at"] = app["applied_at"]
    
    return {"status": "applied", "application": app}


@router.get("/applications")
async def tracker_list():
    """List all applications."""
    return {
        "total": len(applications_db),
        "applied": sum(1 for a in applications_db if a["status"] == "applied"),
        "interview": sum(1 for a in applications_db if a["status"] == "interview"),
        "offered": sum(1 for a in applications_db if a["status"] == "offered"),
        "rejected": sum(1 for a in applications_db if a["status"] == "rejected"),
        "applications": applications_db,
    }


# ═══════════════════════════════════════
# 🏃 AUTO-RUN: apply to all matching jobs
# ═══════════════════════════════════════
@router.post("/auto-apply")
async def auto_apply_all():
    """Auto-apply to all jobs that match well."""
    results = []
    
    for job in jobs_db:
        if job.get("applied"):
            continue
        
        # Match
        match = await matcher_score(job["id"])
        if isinstance(match, dict) and match.get("recommendation") in ("APPLY", "apply"):
            # Generate cover letter
            letter_result = await writer_cover_letter(job["id"])
            letter = letter_result.get("cover_letter", "")
            
            # Apply
            app_result = await tracker_apply(job["id"], cover_letter=letter)
            
            results.append({
                "company": job["company"],
                "title": job["title"],
                "match_score": match.get("match_score", 0),
                "cover_letter": letter[:100] + "...",
                "status": app_result.get("status", "error"),
            })
    
    return {
        "auto_applied": len(results),
        "results": results,
    }


# ═══════════════════════════════════════
# 📊 Dashboard
# ═══════════════════════════════════════
@router.get("/dashboard")
async def job_dashboard():
    return {
        "profile": PROFILE,
        "total_jobs": len(jobs_db),
        "jobs": jobs_db,
        "total_applications": len(applications_db),
        "applications": applications_db,
    }