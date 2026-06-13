import random
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.orm import Battery, Assessment, Deployment, Site
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["ai"])


class ChatMessage(BaseModel):
    message: str


# Pre-built contextual responses for the mock AI chat
CONTEXTUAL_RESPONSES = {
    "battery": [
        "Based on our fleet analysis, the average State of Health across all batteries is {avg_soh}%. "
        "The fleet contains {total} batteries with {by_grade_s} rated S-grade (excellent), {by_grade_a} A-grade, "
        "{by_grade_b} B-grade, {by_grade_c} C-grade, and {by_grade_d} D-grade (end-of-life).",
        "Battery health is primarily driven by cycle count, thermal exposure, and internal resistance growth. "
        "Our ML model analyzes 18 feature dimensions to produce a confidence-weighted grade from S to D.",
    ],
    "deployment": [
        "The deployment engine matches batteries to demand sites based on grade eligibility, geographic proximity, "
        "remaining capacity demand, and chemistry compatibility. Currently {active} batteries are actively deployed.",
        "Grade S and A batteries are prioritized for solar storage and EV charging stations. Grade B and C batteries "
        "are routed to rural microgrids, school backup systems, and telecom towers. Grade D batteries are sent "
        "directly to certified recyclers.",
    ],
    "impact": [
        "VoltLife has unlocked {mwh} MWh of second-life energy and saved {carbon} tonnes of CO₂. "
        "{diverted} batteries have been diverted from premature recycling, while {recycled} have been "
        "responsibly recycled through certified partners.",
        "Every battery diverted to second-life use saves approximately 65 kg of CO₂ compared to manufacturing "
        "a new unit. Our lifecycle approach ensures maximum value extraction before responsible end-of-life processing.",
    ],
    "aadhaar": [
        "Battery Aadhaar is a 21-character unique identity code assigned to every battery in the VoltLife system. "
        "It encodes the country of origin, manufacturer, chemistry, voltage class, capacity, manufacture date, "
        "and a unique serial. This creates an immutable identity for lifecycle tracking.",
        "The Aadhaar system is inspired by India's national identity program, adapted for battery lifecycle management. "
        "Each battery gets a QR-scannable passport that tracks its journey from intake to second-life deployment.",
    ],
    "default": [
        "I'm Volt AI, your intelligent assistant for battery lifecycle management. I can help you understand "
        "fleet health, deployment strategies, sustainability impact, and the Battery Aadhaar identity system. "
        "What would you like to know?",
        "VoltLife is India's first national-scale battery operating system. We intake retired EV and industrial "
        "batteries, assess their remaining health using AI, and deploy them to optimal second-life applications "
        "across the country — from solar storage to rural microgrids.",
    ],
}

SUGGESTIONS = [
    "What is the current fleet health?",
    "How does the deployment algorithm work?",
    "Show me the sustainability impact",
    "What is Battery Aadhaar?",
    "How many batteries are grade S?",
    "Explain the grading system",
]


def _classify_intent(message: str) -> str:
    msg = message.lower()
    if any(kw in msg for kw in ["battery", "health", "soh", "grade", "fleet", "capacity"]):
        return "battery"
    if any(kw in msg for kw in ["deploy", "site", "assign", "route", "recommend"]):
        return "deployment"
    if any(kw in msg for kw in ["impact", "carbon", "co2", "mwh", "sustainab", "environment"]):
        return "impact"
    if any(kw in msg for kw in ["aadhaar", "identity", "passport", "qr", "bpan"]):
        return "aadhaar"
    return "default"


@router.post("/ai/chat")
def chat(body: ChatMessage, db: Session = Depends(get_db)):
    """
    Mock AI chat endpoint that returns contextual responses about the VoltLife system.
    """
    intent = _classify_intent(body.message)
    templates = CONTEXTUAL_RESPONSES[intent]
    template = random.choice(templates)

    # Fetch live stats to fill template variables
    total = db.query(func.count(Battery.id)).scalar() or 0
    active = db.query(func.count(Deployment.id)).filter(
        Deployment.status.in_(["recommended", "approved", "dispatched"])
    ).scalar() or 0
    mwh = db.query(func.sum(Deployment.energy_unlocked_mwh)).scalar() or 0.0
    carbon_kg = db.query(func.sum(Deployment.carbon_saved_kg)).scalar() or 0.0
    diverted = db.query(func.count(Deployment.id)).join(Site).filter(
        Site.site_type != "recycler"
    ).scalar() or 0
    recycled = db.query(func.count(Battery.id)).filter(Battery.status == "recycled").scalar() or 0

    # Grade distribution
    latest_subq = db.query(
        Assessment.battery_id,
        Assessment.soh_pct,
        Assessment.grade,
        func.row_number().over(
            partition_by=Assessment.battery_id,
            order_by=Assessment.created_at.desc()
        ).label("rn")
    ).subquery()
    avg_soh = db.query(func.avg(latest_subq.c.soh_pct)).filter(latest_subq.c.rn == 1).scalar() or 0.0
    grade_counts = db.query(
        latest_subq.c.grade, func.count(latest_subq.c.battery_id)
    ).filter(latest_subq.c.rn == 1).group_by(latest_subq.c.grade).all()
    by_grade = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for g, c in grade_counts:
        if g in by_grade:
            by_grade[g] = c

    response_text = template.format(
        total=total,
        active=active,
        mwh=round(float(mwh), 1),
        carbon=round(float(carbon_kg) / 1000.0, 1),
        diverted=diverted,
        recycled=recycled,
        avg_soh=round(float(avg_soh), 1),
        by_grade_s=by_grade["S"],
        by_grade_a=by_grade["A"],
        by_grade_b=by_grade["B"],
        by_grade_c=by_grade["C"],
        by_grade_d=by_grade["D"],
    )

    return {
        "response": response_text,
        "intent": intent,
        "suggestions": random.sample(SUGGESTIONS, min(3, len(SUGGESTIONS))),
    }


@router.get("/ai/suggestions")
def get_suggestions():
    """
    Returns contextual prompt suggestions for the chat interface.
    """
    return {"suggestions": SUGGESTIONS}
