import math
import requests
from typing import Dict, Any, List

class GaussianPlumeModel:
    def __init__(self):
        """
        Initializes the dispersion model for generating plume polygons.
        Uses the free Open-Meteo API for real-time wind data.
        """
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def get_real_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetches current wind speed and direction for the given coordinates.
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true"
            }
            response = requests.get(self.api_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get("current_weather", {})
                wind_speed_kmh = data.get("windspeed", 10.0) # default 10 km/h
                wind_dir_deg = data.get("winddirection", 0) # default North
                return {
                    "wind_speed_kmh": wind_speed_kmh,
                    "wind_dir_deg": wind_dir_deg,
                    "status": "success"
                }
            else:
                return self._fallback_weather()
        except Exception as e:
            print(f"Weather API Error: {e}")
            return self._fallback_weather()

    def _fallback_weather(self) -> Dict[str, Any]:
        return {
            "wind_speed_kmh": 15.0,
            "wind_dir_deg": 45.0, # Northeast
            "status": "fallback"
        }

    def _calculate_destination(self, lat: float, lon: float, distance_km: float, bearing_deg: float) -> tuple:
        """
        Calculate destination lat/lon given a start point, distance, and bearing.
        """
        R = 6371.0 # Earth radius in km
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        brng = math.radians(bearing_deg)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance_km / R) +
                         math.cos(lat1) * math.sin(distance_km / R) * math.cos(brng))
        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(distance_km / R) * math.cos(lat1),
                                 math.cos(distance_km / R) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2)

    def generate_plume_polygon(self, lat: float, lon: float, volume_tons: float) -> Dict[str, Any]:
        """
        Generates a wedge/polygon representing the dispersion plume.
        The length of the plume depends on wind speed and emission volume.
        The spread (angle) represents the dispersion cone.
        Returns a GeoJSON-like list of coordinates [lat, lon].
        """
        weather = self.get_real_weather(lat, lon)
        speed = weather["wind_speed_kmh"]
        direction = weather["wind_dir_deg"]
        
        # Wind direction is where wind comes FROM. Plume goes TOWARDS the opposite direction.
        plume_bearing = (direction + 180) % 360

        # Calculate plume length (distance). Higher speed and volume = longer plume
        # Example heuristic: 10 km/h wind + 100 tons = ~5 km plume
        base_length_km = (volume_tons / 50.0) + (speed / 5.0)
        
        # Dispersion spread angle (e.g. 30 degrees)
        spread_angle = 30.0 
        
        # Calculate polygon points
        # Point 1: Source
        points = [[lat, lon]]
        
        # We will create an arc at the end of the plume
        # From (plume_bearing - spread_angle/2) to (plume_bearing + spread_angle/2)
        start_angle = plume_bearing - (spread_angle / 2)
        end_angle = plume_bearing + (spread_angle / 2)
        
        # Generate 5 points along the arc for smooth rendering
        steps = 5
        for i in range(steps + 1):
            current_angle = start_angle + (i * (spread_angle / steps))
            p_lat, p_lon = self._calculate_destination(lat, lon, base_length_km, current_angle)
            points.append([p_lat, p_lon])
            
        # Close the polygon back to source
        points.append([lat, lon])
        
        return {
            "polygon": points,
            "wind_speed_kmh": speed,
            "wind_direction_deg": direction,
            "plume_length_km": base_length_km
        }
