import numpy as np
import matplotlib.pyplot as plt
import os
from src.ranking.mock_data import generate_mock_sites
from src.ranking.scorer import SiteScorer
from src.logistics.routing import OfftakeRouter
from src.logistics.fleet import FleetManager
from src.finance.roi import ROICalculator

def main():
    print("\n--- Phase 1: Methane Site Feasibility Scorer ---")
    
    # 1. Generate Mock Sites
    print("Generating mock site data...")
    raw_sites = generate_mock_sites(num_sites=5)
    
    # 2. Score Sites
    print("Scoring sites based on EU weighting profile...")
    scorer = SiteScorer(config_path=os.path.join(os.path.dirname(__file__), "config", "weights.json"))
    ranked_sites = scorer.score_sites(raw_sites)
    
    # 3. Print Phase 1 Results
    print("\nTop Recommended Sites for Ethanol Refinement:")
    for i, site in enumerate(ranked_sites):
        print(f"Rank {i+1}: {site['site_id']} ({site['site_type']}) - Score: {site['final_score']:.2f}%")
        print(f"   Location: {site['latitude']:.4f}N, {site['longitude']:.4f}E")

    print("\n=======================================================")
    print("--- Phase 2: Supply Chain & Logistics Integration ---")
    
    router = OfftakeRouter(max_distance_km=300.0) # Set cutoff distance
    fleet = FleetManager()
    roi_calc = ROICalculator() # Phase 3: ROI Calculator
    
    for i, site in enumerate(ranked_sites[:3]): # Just evaluate top 3 sites
        print(f"\nEvaluating Rank {i+1} Site: {site['site_id']}")
        
        # Dispatch Mobile Unit
        dispatch = fleet.dispatch_unit(site['latitude'], site['longitude'])
        if dispatch:
            print(f"   [FLEET] Dispatched Mobile Unit {dispatch['unit_id']} from {dispatch['origin_coords']} (Relocation Dist: {dispatch['relocation_distance_km']:.1f} km)")
        else:
            print("   [FLEET] No mobile units available for dispatch!")
            
        # Route to Market
        target_currency = "EUR" # Can be easily changed to USD or CNY
        route = router.route_to_market(site['latitude'], site['longitude'], predicted_volume_tons=150.0, currency=target_currency)
        if route["feasible"]:
            print(f"   [OFFTAKE] Route to {route['nearest_hub']} is {route['distance_km']:.1f} km.")
            print(f"   [OFFTAKE] Estimated Transport Cost: {route['currency_symbol']}{route['estimated_transport_cost']:.2f} {route['currency_code']} per month.")
            
            # --- Phase 3: Financial Projections ---
            print("\n   --- Phase 3: Financial Projections ---")
            financials = roi_calc.calculate_monthly_roi(
                volume_tons=route['volume_tons'], 
                transport_cost=route['estimated_transport_cost'],
                currency=target_currency
            )
            
            sym = financials["currency_symbol"]
            print(f"   [REVENUE] Ethanol Sales: {sym}{financials['revenues']['ethanol_sales']:.2f}")
            print(f"   [REVENUE] Carbon Credits ({financials['co2e_avoided_tons']}t CO2e): {sym}{financials['revenues']['carbon_credits']:.2f}")
            print(f"   [REVENUE] Total: {sym}{financials['revenues']['total_revenue']:.2f}")
            
            print(f"   [EXPENSE] CapEx (Amortized): {sym}{financials['expenses']['capex_amortized']:.2f}")
            print(f"   [EXPENSE] OpEx (Base): {sym}{financials['expenses']['opex_base']:.2f}")
            print(f"   [EXPENSE] Transport: {sym}{financials['expenses']['transport_logistics']:.2f}")
            print(f"   [EXPENSE] Total: {sym}{financials['expenses']['total_expenses']:.2f}")
            
            print(f"   [ROI] Net Monthly Profit: {sym}{financials['net_profit']:.2f}")
            print(f"   [ROI] Monthly ROI: {financials['roi_percentage']:.2f}%")
            
        else:
            print(f"   [OFFTAKE] WARNING: {route['reason']} Skipping financial projection.")

if __name__ == "__main__":
    main()

