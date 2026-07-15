from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from src.ranking.mock_data import generate_mock_sites
from src.ranking.scorer import SiteScorer
from src.logistics.routing import OfftakeRouter
from src.logistics.fleet import FleetManager
from src.finance.roi import ROICalculator
from src.dataio.satellite import Sentinel5PIngestor

app = FastAPI(title="Methane-to-Ethanol Platform API")

# Allow CORS for local frontend development and GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Services once so caches persist
config_path = os.path.join(os.path.dirname(__file__), "config", "weights.json")
scorer = SiteScorer(config_path=config_path)
router = OfftakeRouter(max_distance_km=2000.0)
fleet = FleetManager()
roi_calc = ROICalculator()
satellite_ingestor = Sentinel5PIngestor()

@app.get("/api/analyze")
def analyze_sites(
    currency: str = "EUR",
    min_lat: float = 48.0,
    max_lat: float = 54.0,
    min_lon: float = 6.0,
    max_lon: float = 14.0
):
    """
    Generates mock methane sites within a bounding box, ranks them, routes logistics, and calculates ROI.
    """
    # 1. Generate & Score within bounds using LIVE SATELLITE DATA
    hotspots = satellite_ingestor.get_ch4_hotspots(
        min_lat=min_lat, 
        max_lat=max_lat, 
        min_lon=min_lon, 
        max_lon=max_lon,
        max_sites=5
    )
    
    import random
    # If API fails, GEE is unauthenticated, or no hotspots found, generate mock hotspots
    if not hotspots:
        for _ in range(5):
            hotspots.append({
                "latitude": random.uniform(min_lat, max_lat),
                "longitude": random.uniform(min_lon, max_lon),
                "ch4_val": random.uniform(1800, 1950)
            })

    raw_sites = []
    archetypes = ["Agricultural Digester", "Municipal Landfill", "Wastewater Treatment Plant", "Abandoned Coal Mine"]
    
    for i, spot in enumerate(hotspots):
        site_type = random.choice(archetypes)
        site = {
            "site_id": f"GEE-S5P-{i+1:03d}",
            "site_type": site_type,
            "latitude": spot["latitude"],
            "longitude": spot["longitude"],
            # Give high feedstock volume because it was detected from space
            "feedstock_volume": min(1.0, (spot["ch4_val"] * 1000) + 0.5) if spot["ch4_val"] < 2000 else random.uniform(0.5, 1.0), 
            "zoning_regulatory": random.uniform(0.1, 1.0),
            "carbon_intensity_potential": random.uniform(0.4, 1.0), 
            "feedstock_stability": random.uniform(0.5, 0.9),
            "safety_environmental_buffer": random.uniform(0.1, 1.0),
            "utilities": random.uniform(0.2, 0.95),
            "methane_purity": random.uniform(0.3, 0.9),
            "offtake_logistics": random.uniform(0.4, 1.0),
            "market_proximity": random.uniform(0.3, 0.9),
            "local_ethanol_demand": random.uniform(0.5, 1.0),
            "tax_incentive_subsidy": random.uniform(0.0, 1.0),
            "land_acquisition_cost": random.uniform(0.1, 0.8),
            "byproduct_co2_offtake": random.uniform(0.1, 0.9),
            "topography_site_prep": random.uniform(0.3, 1.0),
            "workforce_availability": random.uniform(0.5, 1.0),
            "climate_risk": random.uniform(0.4, 0.95)
        }
        raw_sites.append(site)
        
    ranked_sites = scorer.score_sites(raw_sites)
    
    results = []
    fleet = FleetManager() # Fresh fleet for every scan
    
    # 2. Process Top 5 Sites
    for site in ranked_sites[:5]:
        site_data = {
            "id": site["site_id"],
            "type": site["site_type"],
            "score": site["final_score"],
            "latitude": site["latitude"],
            "longitude": site["longitude"],
            "logistics": None,
            "finance": None
        }
        
        # Fleet Dispatch
        dispatch = fleet.dispatch_unit(site['latitude'], site['longitude'])
        
        # Route to Market
        route = router.route_to_market(site['latitude'], site['longitude'], predicted_volume_tons=150.0, currency=currency)
        
        if dispatch and route["feasible"]:
            site_data["logistics"] = {
                "unit_id": dispatch["unit_id"],
                "relocation_distance_km": dispatch["relocation_distance_km"],
                "nearest_hub": route["nearest_hub"],
                "hub_distance_km": route["distance_km"],
                "transport_cost": route["estimated_transport_cost"],
                "transport_cost_rate": route["current_rate_applied"],
                "currency_symbol": route["currency_symbol"]
            }
            
            # ROI Projection
            financials = roi_calc.calculate_monthly_roi(
                volume_tons=route['volume_tons'], 
                transport_cost=route["estimated_transport_cost"],
                currency=currency
            )
            site_data["finance"] = financials
            
        else:
            site_data["logistics"] = {
                "feasible": False,
                "reason": route.get("reason", "All Mobile Refinement Units (MRUs) are currently deployed in other active regions.") if not dispatch else route.get("reason")
            }
            if not dispatch:
                site_data["logistics"]["reason"] = "All Mobile Refinement Units (MRUs) are currently deployed in other active regions."
            
        results.append(site_data)
        
    # Generate the Heatmap Tile URL
    heatmap_url = satellite_ingestor.get_ch4_heatmap_url(
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon
    )

    return {
        "status": "success", 
        "currency": currency, 
        "heatmap_url": heatmap_url, 
        "sites": results,
        "gee_authenticated": satellite_ingestor.is_authenticated,
        "hubs": router.get_all_hubs()
    }
