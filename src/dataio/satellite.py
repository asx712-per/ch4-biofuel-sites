import os
import ee
from google.oauth2 import service_account

class Sentinel5PIngestor:
    def __init__(self, key_path: str = None):
        if key_path is None:
            key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "gee_key.json")
            
        print("[SATELLITE] Authenticating with Google Earth Engine...")
        try:
            credentials = service_account.Credentials.from_service_account_file(key_path)
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
            ee.Initialize(scoped_credentials)
            self.is_authenticated = True
            print("[SATELLITE] Authentication Successful.")
        except Exception as e:
            print(f"[SATELLITE] Authentication Failed: {e}")
            self.is_authenticated = False

    def get_ch4_hotspots(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float, max_sites: int = 5):
        """
        Queries the Sentinel-5P Tropomi dataset for CH4 anomalies within a bounding box.
        Returns a list of dicts with latitude and longitude.
        """
        if not self.is_authenticated:
            print("[SATELLITE] Not authenticated. Returning empty list.")
            return []
            
        print(f"[SATELLITE] Querying Sentinel-5P CH4 Data for bounds: ({min_lat:.2f}, {min_lon:.2f}) to ({max_lat:.2f}, {max_lon:.2f})")
        
        try:
            # 1. Define the geometry
            roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            
            # 2. Get the CH4 collection for the last 30 days
            # We use 2023 dates for reliability if current data is processing
            collection = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4") \
                .filterBounds(roi) \
                .filterDate('2023-01-01', '2023-12-31') \
                .select('CH4_column_volume_mixing_ratio_dry_air')
                
            # 3. Create a mean composite
            mean_ch4 = collection.mean().clip(roi)
            
            # 4. We want to find "hotspots" (pixels above a certain threshold)
            # Since Earth Engine runs on Google servers, we use getRegion to pull data points locally
            # In a true production app, we would use GEE spatial reducers to find local maxima,
            # but for this MVP, we pull a coarse grid of points and sort them.
            
            # Create a coarse grid of points (e.g., 0.5 degree steps) to sample
            lat_step = (max_lat - min_lat) / 10
            lon_step = (max_lon - min_lon) / 10
            
            points = []
            for i in range(10):
                for j in range(10):
                    lat = min_lat + (i * lat_step) + (lat_step / 2)
                    lon = min_lon + (j * lon_step) + (lon_step / 2)
                    points.append(ee.Feature(ee.Geometry.Point([lon, lat])))
                    
            fc = ee.FeatureCollection(points)
            
            # Extract the CH4 values at these points
            sampled = mean_ch4.sampleRegions(
                collection=fc,
                scale=7000, # Sentinel-5P resolution is roughly 7km
                geometries=True
            )
            
            features = sampled.getInfo()['features']
            
            # 5. Process the results locally to find the highest CH4 values
            results = []
            for f in features:
                coords = f['geometry']['coordinates']
                val = f['properties'].get('CH4_column_volume_mixing_ratio_dry_air', 0)
                if val > 0:
                    results.append({
                        "longitude": coords[0],
                        "latitude": coords[1],
                        "ch4_val": val
                    })
                    
            # Sort by CH4 value descending (Hotspots first)
            results.sort(key=lambda x: x['ch4_val'], reverse=True)
            
            hotspots = results[:max_sites]
            print(f"[SATELLITE] Found {len(hotspots)} distinct CH4 hotspots.")
            return hotspots
            
        except Exception as e:
            print(f"[SATELLITE] Error querying GEE: {e}")
            return []

    def get_ch4_heatmap_url(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> str:
        """
        Generates a MapID and Token from Google Earth Engine for a tile layer.
        Returns the url format string that Leaflet can use.
        """
        if not self.is_authenticated:
            return ""
            
        try:
            roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            collection = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4") \
                .filterBounds(roi) \
                .filterDate('2023-01-01', '2023-12-31') \
                .select('CH4_column_volume_mixing_ratio_dry_air')
                
            mean_ch4 = collection.mean().clip(roi)
            
            # Typical S5P CH4 values are between 1750 and 1950 ppb
            # But the raw data is often in mol/m^2 or mixing ratio. S5P L3 is usually around 1800-1950 ppb.
            # We'll use 1800 to 1900 to ensure good contrast.
            vis_params = {
                'min': 1800,
                'max': 1950,
                'palette': ['0000FF', '00FF00', 'FFFF00', 'FF0000'], # Blue -> Green -> Yellow -> Red
                'opacity': 0.6
            }
            
            map_id_dict = ee.Image(mean_ch4).getMapId(vis_params)
            return map_id_dict['tile_fetcher'].url_format
        except Exception as e:
            print(f"[SATELLITE] Error generating heatmap URL: {e}")
            return ""
