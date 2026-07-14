import json
from pathlib import Path
from typing import List, Dict, Any

class SiteScorer:
    def __init__(self, config_path: str = "config/weights.json"):
        """
        Initializes the SiteScorer by loading dynamic weights from a configuration file.
        """
        self.config_path = Path(config_path)
        self.weights = self._load_weights()

    def _load_weights(self) -> Dict[str, float]:
        """Loads weights from a JSON file, or uses defaults if not found."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Fallback default weights (European baseline) if file is missing
        print(f"Warning: {self.config_path} not found. Using default weights.")
        return {
            "zoning_regulatory": 10.0,
            "carbon_intensity_potential": 9.0,
            "feedstock_stability": 9.0,
            "feedstock_volume": 8.0,
            "safety_environmental_buffer": 8.0,
            "utilities": 8.0,
            "methane_purity": 7.0,
            "offtake_logistics": 7.0,
            "market_proximity": 6.0,
            "local_ethanol_demand": 6.0,
            "tax_incentive_subsidy": 6.0,
            "land_acquisition_cost": 5.0,
            "byproduct_co2_offtake": 5.0,
            "topography_site_prep": 4.0,
            "workforce_availability": 4.0,
            "climate_risk": 3.0
        }

    def score_sites(self, sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates a final weighted score for each site and returns the sites sorted
        by feasibility (highest score first).
        
        sites: List of dictionaries, where each dict contains raw scores (0.0 to 1.0)
               for the 16 modifiers.
        """
        scored_sites = []
        for site in sites:
            total_score = 0.0
            max_possible_score = sum(self.weights.values())
            
            # Compute weighted sum
            for feature, weight in self.weights.items():
                # We assume the site dictionary has raw values for each feature between 0 and 1
                raw_value = site.get(feature, 0.0) 
                total_score += raw_value * weight
                
            # Normalize to 100 for easy readability
            final_percentage = (total_score / max_possible_score) * 100.0
            
            # Create a new dict to avoid modifying the original data
            site_result = site.copy()
            site_result["final_score"] = final_percentage
            scored_sites.append(site_result)
            
        # Sort by final score descending
        scored_sites.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_sites
