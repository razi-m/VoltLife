import os
import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.orm import Site
from app.core.logging import logger

def seed_sites(db: Session):
    """
    Seeds the sites table with demand registry data from sites.json.
    Wipes existing sites first to ensure idempotency.
    """
    # Load sites.json
    # Determine the directory where this file resides
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sites_json_path = os.path.join(current_dir, "sites.json")
    
    if not os.path.exists(sites_json_path):
        logger.error(f"sites.json not found at {sites_json_path}")
        return
        
    with open(sites_json_path, "r") as f:
        sites_data = json.load(f)
        
    logger.info(f"Loaded {len(sites_data)} sites from sites.json. Seeding database...")
    
    # Wipe old sites
    db.query(Site).delete()
    db.commit()
    
    # Insert new sites
    for s_dict in sites_data:
        site = Site(
            name=s_dict["name"],
            site_type=s_dict["site_type"],
            state=s_dict.get("state"),
            lat=s_dict["lat"],
            lng=s_dict["lng"],
            demand_kwh=s_dict["demand_kwh"],
            min_soh_pct=s_dict["min_soh_pct"],
            min_grade=s_dict["min_grade"],
            priority=s_dict.get("priority", 1.0),
            is_simulated=s_dict.get("is_simulated", True)
        )
        db.add(site)
        
    db.commit()
    logger.info("Successfully seeded sites table.")

if __name__ == "__main__":
    # If run directly, initialize DB (SQLite fallback support) and run seeding
    init_db()
    db = SessionLocal()
    try:
        seed_sites(db)
    finally:
        db.close()
