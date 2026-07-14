import random
from typing import List, Dict, Any

def generate_mock_sites(num_sites: int = 5, min_lat: float = 48.0, max_lat: float = 54.0, min_lon: float = 6.0, max_lon: float = 14.0) -> List[Dict[str, Any]]:
    """
    Generates a list of synthetic methane emission sites with random raw 
    scores (0.0 to 1.0) for all 16 modifiers. 1.0 represents the ideal case.
    """
    sites = []
    
    # We'll use a few named archetypes for realism
    archetypes = [
        "Agricultural Digester",
        "Municipal Landfill",
        "Wastewater Treatment Plant",
        "Leaky Pipeline Valve",
        "Abandoned Coal Mine"
    ]
    
    for i in range(num_sites):
        site_type = random.choice(archetypes)
        site = {
            "site_id": f"SITE-{i+1:03d}",
            "site_type": site_type,
            "latitude": random.uniform(min_lat, max_lat),
            "longitude": random.uniform(min_lon, max_lon),
            
            # Raw variables between 0.0 and 1.0 (1.0 = best possible condition)
            "zoning_regulatory": random.uniform(0.1, 1.0),
            "carbon_intensity_potential": random.uniform(0.4, 1.0), 
            "feedstock_stability": random.uniform(0.2, 0.9),
            "feedstock_volume": random.uniform(0.3, 1.0),
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
        
        # Add some domain logic logic: Landfills are stable but have low purity
        if site_type == "Municipal Landfill":
            site["feedstock_stability"] = random.uniform(0.8, 1.0)
            site["methane_purity"] = random.uniform(0.1, 0.4)
            
        # Ag digesters have high CI potential (very negative CI) but maybe far from infrastructure
        elif site_type == "Agricultural Digester":
            site["carbon_intensity_potential"] = random.uniform(0.8, 1.0)
            site["offtake_logistics"] = random.uniform(0.1, 0.5)
            
        sites.append(site)
        
    return sites

if __name__ == "__main__":
    # Test generation
    import pprint
    mock = generate_mock_sites(1)
    pprint.pprint(mock)
