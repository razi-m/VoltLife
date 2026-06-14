from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

# Association table for Battery <-> InventoryLot (Many-to-Many or One-to-Many but represented cleanly)
# A battery can belong to one inventory lot at a time, but using an association table is clean and extensible.
BatteryInventoryLotAssociation = Table(
    "battery_inventory_lot_associations",
    Base.metadata,
    Column("battery_id", Integer, ForeignKey("batteries.id", ondelete="CASCADE"), primary_key=True),
    Column("inventory_lot_id", Integer, ForeignKey("inventory_lots.id", ondelete="CASCADE"), primary_key=True)
)

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    gstin = Column(String(15), nullable=False)
    address = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("SupplierUser", back_populates="supplier", cascade="all, delete-orphan")
    verifications = relationship("SupplierVerification", back_populates="supplier", cascade="all, delete-orphan")
    lots = relationship("InventoryLot", back_populates="supplier", cascade="all, delete-orphan")
    subscriptions = relationship("SaaS_Subscription", back_populates="supplier", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="supplier")


class SupplierUser(Base):
    __tablename__ = "supplier_users"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="member")  # admin | member
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("Supplier", back_populates="users")


class SupplierVerification(Base):
    __tablename__ = "supplier_verifications"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    verifier_notes = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")  # pending | approved | rejected
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    supplier = relationship("Supplier", back_populates="verifications")


class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    grade = Column(String(10), nullable=False)  # e.g. "GRADE A", "GRADE B", etc.
    chemistry = Column(String(20), nullable=False)
    total_capacity_kwh = Column(Numeric(10, 2), nullable=False)
    available_quantity = Column(Integer, nullable=False)
    avg_soh = Column(Numeric(5, 2), nullable=False)
    avg_rul_years = Column(Numeric(4, 1), nullable=False)
    status = Column(String(20), default="draft")  # draft | listed | sold_out
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="lots")
    pricing_tiers = relationship("PricingTier", back_populates="inventory_lot", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="inventory_lot", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="inventory_lot")
    orders = relationship("Order", back_populates="inventory_lot")
    
    # Associated individual batteries (reusing existing Battery model)
    batteries = relationship(
        "Battery",
        secondary=BatteryInventoryLotAssociation,
        backref="inventory_lot"
    )


class PricingTier(Base):
    __tablename__ = "pricing_tiers"

    id = Column(Integer, primary_key=True, index=True)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id", ondelete="CASCADE"), nullable=False)
    min_quantity = Column(Integer, nullable=False, default=1)
    price_per_kwh = Column(Numeric(10, 2), nullable=False)

    inventory_lot = relationship("InventoryLot", back_populates="pricing_tiers")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    moq = Column(Integer, nullable=False, default=1)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory_lot = relationship("InventoryLot", back_populates="listings")


class BuyerAccount(Base):
    __tablename__ = "buyer_accounts"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    requirements = relationship("Requirement", back_populates="buyer", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="buyer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="buyer", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="buyer", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    use_case_text = Column(String(1000), nullable=False)
    parsed_grade = Column(String(10), nullable=True)
    parsed_capacity_kwh = Column(Numeric(10, 2), nullable=True)
    parsed_quantity = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("BuyerAccount", back_populates="requirements")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    battery_cost = Column(Numeric(12, 2), nullable=False)
    transport_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    delivery_days = Column(Integer, nullable=False)
    porter_vehicle_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")  # pending | accepted | rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("BuyerAccount", back_populates="quotes")
    inventory_lot = relationship("InventoryLot", back_populates="quotes")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(20), default="pending")  # pending | paid | failed
    tracking_status = Column(String(30), default="confirmed")  # confirmed | porter_booked | seller_notified | buyer_notified | shipment_started | in_transit | delivered
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("BuyerAccount", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    inventory_lot = relationship("InventoryLot", back_populates="orders")
    tracking_events = relationship("ShipmentTrackingEvent", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("PaymentEvent", back_populates="order", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="order", cascade="all, delete-orphan")


class ShipmentTrackingEvent(Base):
    __tablename__ = "shipment_tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(40), nullable=False)  # confirmed | porter_booked | seller_notified | buyer_notified | shipment_started | in_transit | delivered
    notes = Column(String(255), nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="tracking_events")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    stripe_session_id = Column(String(100), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)  # success | failed | pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payments")


class SaaS_Subscription(Base):
    __tablename__ = "saas_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id = Column(String(100), nullable=True)
    plan_name = Column(String(30), nullable=False)  # Monthly | Annual | Enterprise
    status = Column(String(20), nullable=False)  # active | cancelled | expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    supplier = relationship("Supplier", back_populates="subscriptions")



class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    issue_text = Column(String(1000), nullable=False)
    status = Column(String(20), default="open")  # open | resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("BuyerAccount", back_populates="support_tickets")
    order = relationship("Order", back_populates="support_tickets")
