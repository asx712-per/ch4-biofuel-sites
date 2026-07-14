from typing import List, Dict, Any, Optional
from geopy.distance import geodesic

class FleetManager:
    def __init__(self):
        """
        Manages a fleet of mobile methane-to-ethanol refinement units.
        """
        # Mock initial fleet state (stationed around Europe)
        self.fleet = [
            {"unit_id": "MRU-01", "status": "AVAILABLE", "lat": 48.8566, "lon": 2.3522}, # Paris
            {"unit_id": "MRU-02", "status": "MAINTENANCE", "lat": 52.5200, "lon": 13.4050}, # Berlin
            {"unit_id": "MRU-03", "status": "AVAILABLE", "lat": 41.9028, "lon": 12.4964}, # Rome
        ]

    def dispatch_unit(self, site_lat: float, site_lon: float) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest available Mobile Refinement Unit (MRU) and dispatches it.
        """
        available_units = [u for u in self.fleet if u["status"] == "AVAILABLE"]
        
        if not available_units:
            return None
            
        site_coords = (site_lat, site_lon)
        best_unit = None
        min_distance = float('inf')
        
        for unit in available_units:
            unit_coords = (unit["lat"], unit["lon"])
            dist = geodesic(site_coords, unit_coords).kilometers
            if dist < min_distance:
                min_distance = dist
                best_unit = unit
                
        if best_unit:
            # Mark as dispatched (in a real system this would update a DB)
            best_unit["status"] = "DISPATCHED"
            return {
                "unit_id": best_unit["unit_id"],
                "relocation_distance_km": min_distance,
                "origin_coords": (best_unit["lat"], best_unit["lon"])
            }
            
        return None
