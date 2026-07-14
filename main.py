from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from src.ranking.mock_data import generate_mock_sites
from src.ranking.scorer import SiteScorer
from src.logistics.routing import OfftakeRouter
from src.logistics.fleet import FleetManager
from src.finance.roi import ROICalculator

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
router = OfftakeRouter(max_distance_km=300.0)
fleet = FleetManager()
roi_calc = ROICalculator()

@app.get("/api/analyze")
def analyze_sites(currency: str = "EUR"):
    """
    Generates mock methane sites, ranks them, routes logistics, and calculates ROI.
    """
    # 1. Generate & Score
    raw_sites = generate_mock_sites(num_sites=10)
    ranked_sites = scorer.score_sites(raw_sites)
    
    results = []
    
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
                "reason": route.get("reason", "No mobile units available.")
            }
            
        results.append(site_data)
        
    return {"status": "success", "currency": currency, "sites": results}
