from typing import Dict, Any, Tuple
from geopy.distance import geodesic
from datetime import datetime, timedelta
import random

class FuelPriceService:
    def __init__(self, baseline_cost_usd: float = 0.15):
        """
        Manages dynamic fuel pricing, updating every 6 hours automatically.
        Includes currency conversion logic.
        """
        self.baseline_cost_usd = baseline_cost_usd
        self.current_price_usd = baseline_cost_usd
        self.last_updated_time = datetime.min
        self.refresh_interval = timedelta(hours=6)
        
        # Mock exchange rates (Base: 1 USD)
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "CNY": 7.23
        }
        
    def _fetch_live_price_usd(self) -> float:
        """Simulates an API call to get live fuel/transportation pricing in USD."""
        fluctuation = random.uniform(-0.20, 0.20)
        new_price = self.baseline_cost_usd * (1 + fluctuation)
        return new_price

    def get_price_per_km_ton(self, currency: str = "USD") -> Tuple[float, str]:
        """
        Returns the current price in the requested currency along with the symbol.
        Automatically fetches a new price if the cache is older than 6 hours.
        """
        now = datetime.now()
        if now - self.last_updated_time >= self.refresh_interval:
            print(f"   [FUEL SERVICE] Cache expired. Fetching live fuel prices... (Last updated: {self.last_updated_time})")
            self.current_price_usd = self._fetch_live_price_usd()
            self.last_updated_time = now
            print(f"   [FUEL SERVICE] New base transport cost rate applied: ${self.current_price_usd:.4f} USD / km / ton")
            
        currency = currency.upper()
        if currency not in self.exchange_rates:
            print(f"   [FUEL SERVICE] Currency {currency} not supported, defaulting to USD.")
            currency = "USD"
            
        rate = self.current_price_usd * self.exchange_rates[currency]
        
        symbols = {"USD": "$", "EUR": "€", "CNY": "¥"}
        return round(rate, 4), symbols[currency]

class OfftakeRouter:
    def __init__(self, max_distance_km: float = 300.0, baseline_cost_usd: float = 0.15):
        """
        Initializes the router with a maximum distance cutoff and a dynamic fuel price service.
        """
        self.max_distance_km = max_distance_km
        self.fuel_service = FuelPriceService(baseline_cost_usd=baseline_cost_usd)
        
        # Mock blending hubs in Europe (e.g., Rotterdam, Hamburg, Antwerp)
        self.blending_hubs = {
            "Rotterdam Port": (51.9225, 4.47917),
            "Hamburg Port": (53.5511, 9.9937),
            "Antwerp Hub": (51.2194, 4.4025),
            "Marseille Hub": (43.2965, 5.3698)
        }

    def route_to_market(self, site_lat: float, site_lon: float, predicted_volume_tons: float = 100.0, currency: str = "USD") -> Dict[str, Any]:
        """
        Finds the nearest blending hub and calculates the distance, cost in the requested currency, 
        and checks the maximum distance cutoff.
        """
        site_coords = (site_lat, site_lon)
        
        best_hub = None
        min_distance = float('inf')
        
        for hub_name, hub_coords in self.blending_hubs.items():
            dist = geodesic(site_coords, hub_coords).kilometers
            if dist < min_distance:
                min_distance = dist
                best_hub = hub_name
                
        # Check against the maximum distance cutoff
        if min_distance > self.max_distance_km:
            return {
                "feasible": False,
                "reason": f"Nearest hub ({best_hub}) is {min_distance:.1f} km away. Exceeds cutoff of {self.max_distance_km} km due to significant transit losses.",
                "distance_km": min_distance,
                "nearest_hub": best_hub
            }
            
        # Get the latest dynamic cost in the requested currency
        current_rate, symbol = self.fuel_service.get_price_per_km_ton(currency)
        estimated_cost = min_distance * current_rate * predicted_volume_tons
        
        return {
            "feasible": True,
            "nearest_hub": best_hub,
            "distance_km": min_distance,
            "estimated_transport_cost": estimated_cost,
            "currency_symbol": symbol,
            "currency_code": currency,
            "current_rate_applied": current_rate,
            "volume_tons": predicted_volume_tons
        }
