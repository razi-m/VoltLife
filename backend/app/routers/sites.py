from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.api import SiteListResponse
from app.services.deployment import get_derived_sites

router = APIRouter(prefix="/api/v1", tags=["sites"])

@router.get("/sites", response_model=SiteListResponse)
def list_sites(db: Session = Depends(get_db)):
    """
    Returns the demand registry sites list, with derived remaining capacities
    and active deployment counts computed in-database.
    """
    sites = get_derived_sites(db)
    
    items = []
    for site in sites:
        items.append({
            "id": site.id,
            "name": site.name,
            "site_type": site.site_type,
            "state": site.state,
            "lat": float(site.lat),
            "lng": float(site.lng),
            "demand_kwh": float(site.demand_kwh),
            "remaining_kwh": float(site.remaining_kwh),
            "min_grade": site.min_grade,
            "assigned_count": int(site.assigned_count)
        })
        
    return {"items": items}
