import os
from app.core.logging import logger

def calculate_delivery(origin: str, destination: str, quantity: int, capacity_per_pack_kwh: float) -> dict:
  """
  Mock Porter adapter that deterministically calculates delivery cost, vehicle selection,
  and ETA based on origin/destination distance and total battery payload weight.
  """
  api_key = os.getenv("PORTER_API_KEY")
  if api_key:
      logger.info(f"Simulating Porter API call using configured PORTER_API_KEY...")
  else:
      logger.info("Using offline mock Porter adapter...")

  # 1. Deterministic distance heuristic (Pune/Mumbai/Bangalore/Delhi/Hyderabad/Chennai)
  org = origin.strip().lower()
  dest = destination.strip().lower()
  
  if org == dest:
      distance_km = 20.0
  else:
      # Deterministic hash of origin and destination names to simulate distance
      h = sum(ord(c) for c in org) * 13 + sum(ord(c) for c in dest) * 17
      distance_km = (h % 380) + 40.0  # 40km to 420km
      
  # 2. Weight heuristic (8 kg per kWh of capacity)
  total_capacity = quantity * capacity_per_pack_kwh
  total_weight_kg = total_capacity * 8.0
  
  # Apply 10% safety/packaging buffer to prevent overloaded cargo
  buffered_weight_kg = total_weight_kg * 1.10
  
  # 3. Vehicle selection based on weight (standard limits: Ape = 250kg, Ace = 850kg, Bolero = 2000kg)
  if buffered_weight_kg <= 250:
      vehicle = "Three Wheeler (Piaggio Ape)"
      base_rate = 30.0
      per_km_rate = 0.5
  elif buffered_weight_kg <= 850:
      vehicle = "Tata Ace (Chota Hathi)"
      base_rate = 75.0
      per_km_rate = 1.0
  elif buffered_weight_kg <= 2000:
      vehicle = "Mahindra Bolero Pickup"
      base_rate = 150.0
      per_km_rate = 1.8
  else:
      vehicle = "Tata 407 (Light Truck)"
      base_rate = 300.0
      per_km_rate = 3.0
      
  # 4. Cost calculation
  transport_cost = base_rate + (distance_km * per_km_rate)
  
  # 5. Delivery days (ETA)
  if distance_km <= 50:
      days = 1
  elif distance_km <= 150:
      days = 2
  elif distance_km <= 300:
      days = 3
  else:
      days = 4
      
  logger.info(f"Logistics calculated: Origin={origin}, Dest={destination}, Weight={total_weight_kg:.1f}kg, Vehicle={vehicle}, Cost=${transport_cost:.2f}, Days={days}")
  
  return {
      "porter_vehicle_type": vehicle,
      "transport_cost": round(transport_cost, 2),
      "delivery_days": days
  }
