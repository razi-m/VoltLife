from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, CheckConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Battery(Base):
    __tablename__ = "batteries"

    id = Column(Integer, primary_key=True, index=True)
    aadhaar_id = Column(String(21), unique=True, index=True, nullable=True)
    external_ref = Column(String(50), nullable=False, index=True)
    oem = Column(String(50), nullable=False)
    model = Column(String(80), nullable=True)
    chemistry = Column(String(20), nullable=False)
    form_factor = Column(String(20), default="pack")
    rated_capacity_kwh = Column(Numeric(6, 2), nullable=False)
    nominal_voltage = Column(Numeric(5, 1), nullable=True)
    manufacture_date = Column(Date, nullable=True)
    source_city = Column(String(60), nullable=True)
    source_state = Column(String(40), nullable=True)
    lat = Column(Numeric(9, 6), nullable=True)
    lng = Column(Numeric(9, 6), nullable=True)
    status = Column(String(20), default="ingested")  # ingested | assessed | assigned | deployed | recycled
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    telemetry = relationship("TelemetrySummary", back_populates="battery", uselist=False, cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="battery", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="battery", cascade="all, delete-orphan")
    lifecycle_events = relationship("LifecycleEvent", back_populates="battery", cascade="all, delete-orphan")


class TelemetrySummary(Base):
    __tablename__ = "telemetry_summaries"

    battery_id = Column(Integer, ForeignKey("batteries.id", ondelete="CASCADE"), primary_key=True)
    cycle_count = Column(Integer, nullable=False)
    capacity_now_kwh = Column(Numeric(6, 2), nullable=True)
    capacity_fade_pct = Column(Numeric(5, 2), nullable=True)
    fade_rate_pct_per_100cyc = Column(Numeric(6, 3), nullable=True)
    avg_temp_c = Column(Numeric(5, 2), nullable=True)
    max_temp_c = Column(Numeric(5, 2), nullable=True)
    thermal_stress_hours = Column(Numeric(8, 1), nullable=True)
    internal_resistance_mohm = Column(Numeric(7, 2), nullable=True)
    ir_growth_pct = Column(Numeric(6, 2), nullable=True)
    voltage_stability = Column(Numeric(4, 3), nullable=True)
    coulombic_efficiency = Column(Numeric(5, 4), nullable=True)
    features_json = Column(JSON, nullable=True)

    # Relationships
    battery = relationship("Battery", back_populates="telemetry")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(Integer, ForeignKey("batteries.id", ondelete="CASCADE"), nullable=False, index=True)
    soh_pct = Column(Numeric(5, 2), nullable=False)
    rul_years = Column(Numeric(4, 1), nullable=False)
    rul_low_years = Column(Numeric(4, 1), nullable=True)
    rul_high_years = Column(Numeric(4, 1), nullable=True)
    grade = Column(String(1), CheckConstraint("grade IN ('S','A','B','C','D')"), nullable=False)
    confidence = Column(String(6), nullable=False)  # high | medium | low
    model_version = Column(String(20), nullable=False)
    explanation_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    battery = relationship("Battery", back_populates="assessments")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    site_type = Column(String(30), nullable=False)
    state = Column(String(40), nullable=True)
    lat = Column(Numeric(9, 6), nullable=False)
    lng = Column(Numeric(9, 6), nullable=False)
    demand_kwh = Column(Numeric(10, 2), nullable=False)
    min_soh_pct = Column(Numeric(5, 2), nullable=False)
    min_grade = Column(String(1), nullable=False)
    priority = Column(Numeric(3, 2), default=1.0)
    is_simulated = Column(Boolean, default=True)

    # Relationships
    deployments = relationship("Deployment", back_populates="site")


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(Integer, ForeignKey("batteries.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    score = Column(Numeric(6, 3), nullable=False)
    reasoning_json = Column(JSON, nullable=False)
    distance_km = Column(Numeric(8, 1), nullable=True)
    energy_unlocked_mwh = Column(Numeric(10, 3), nullable=False)
    carbon_saved_kg = Column(Numeric(12, 1), nullable=False)
    status = Column(String(20), default="recommended")  # recommended | approved | dispatched
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    battery = relationship("Battery", back_populates="deployments")
    site = relationship("Site", back_populates="deployments")


class LifecycleEvent(Base):
    __tablename__ = "lifecycle_events"

    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(Integer, ForeignKey("batteries.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    payload_json = Column(JSON, nullable=True)
    event_hash = Column(String(64), nullable=True)  # Sha256 hash for ledger verification
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    battery = relationship("Battery", back_populates="lifecycle_events")
