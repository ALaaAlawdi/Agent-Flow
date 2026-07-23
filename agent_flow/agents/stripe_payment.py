"""Stripe Payment + Usage Tracking — API endpoints."""

from fastapi import APIRouter, HTTPException
import time, os

router = APIRouter(prefix="/billing", tags=["billing"])

# In-memory usage tracking (replace with DB in production)
usage_tracker: dict[str, dict] = {}
plans = {
    "free": {"agents": 1, "calls": 100, "name": "Free"},
    "starter": {"agents": 3, "calls": 1000, "name": "Starter"},
    "pro": {"agents": 10, "calls": 10000, "name": "Pro"},
    "enterprise": {"agents": 999, "calls": 999999, "name": "Enterprise"},
}


@router.get("/status/{user_id}")
async def billing_status(user_id: str):
    """Get user billing status."""
    u = usage_tracker.get(user_id, {"plan": "free", "calls_used": 0, "since": time.time()})
    plan = plans.get(u["plan"], plans["free"])
    return {
        "user_id": user_id,
        "plan": plan["name"],
        "calls_used": u["calls_used"],
        "calls_limit": plan["calls"],
        "agents_allowed": plan["agents"],
        "remaining": max(0, plan["calls"] - u["calls_used"]),
        "usage_pct": round(u["calls_used"] / max(1, plan["calls"]) * 100, 1),
    }


@router.get("/track/{user_id}")
async def track_usage(user_id: str):
    """Track a usage call and check limits."""
    if user_id not in usage_tracker:
        usage_tracker[user_id] = {"plan": "free", "calls_used": 0, "since": time.time()}
    
    u = usage_tracker[user_id]
    plan = plans.get(u["plan"], plans["free"])
    
    if u["calls_used"] >= plan["calls"]:
        raise HTTPException(status_code=429, detail=f"Limit reached: {plan['calls']} calls. Upgrade plan.")
    
    u["calls_used"] += 1
    return {"status": "ok", "calls_used": u["calls_used"], "remaining": plan["calls"] - u["calls_used"]}


@router.post("/upgrade")
async def upgrade_plan(user_id: str, plan: str):
    """Upgrade user plan (mock — real would use Stripe webhook)."""
    if plan not in plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")
    usage_tracker[user_id] = {"plan": plan, "calls_used": 0, "since": time.time()}
    return {
        "status": "upgraded",
        "plan": plans[plan]["name"],
        "calls_limit": plans[plan]["calls"],
        "agents_allowed": plans[plan]["agents"],
        "message": f"✅ Upgraded to {plans[plan]['name']}!",
    }


@router.post("/stripe-webhook")
async def stripe_webhook(payload: dict = {}):
    """Handle Stripe webhook (mock endpoint)."""
    user_id = payload.get("customer_id", "demo-user")
    plan = payload.get("plan", "starter")
    usage_tracker[user_id] = {"plan": plan, "calls_used": 0, "since": time.time()}
    return {
        "status": "ok",
        "user_id": user_id,
        "plan": plans.get(plan, plans["free"])["name"],
    }


@router.get("/dashboard")
async def billing_dashboard():
    """Get overall billing dashboard."""
    total_users = len(usage_tracker)
    total_calls = sum(u["calls_used"] for u in usage_tracker.values())
    by_plan = {}
    for u in usage_tracker.values():
        p = u["plan"]
        by_plan[p] = by_plan.get(p, 0) + 1
    return {
        "total_users": total_users,
        "total_calls": total_calls,
        "by_plan": by_plan,
        "plans": {k: {"name": v["name"], "calls": v["calls"], "agents": v["agents"]} for k, v in plans.items()},
    }