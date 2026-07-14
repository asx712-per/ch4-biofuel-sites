from typing import Dict, Any
from src.finance.market import MarketPriceService

class ROICalculator:
    def __init__(self, capex_total: float = 3000000.0, capex_years: int = 10, opex_monthly: float = 15000.0):
        """
        Initializes the ROI calculator with industry standard CapEx and OpEx.
        :param capex_total: Total capital expenditure for a mobile unit (e.g., $3,000,000)
        :param capex_years: Amortization period (e.g., 10 years)
        :param opex_monthly: Base monthly operational expenses (power, maintenance)
        """
        self.capex_total = capex_total
        self.capex_monthly = capex_total / (capex_years * 12)
        self.opex_monthly = opex_monthly
        
        self.market = MarketPriceService()
        
        # Global Warming Potential of Methane (1 ton CH4 = ~28 tons CO2e)
        self.methane_gwp = 28.0

    def calculate_monthly_roi(self, volume_tons: float, transport_cost: float, currency: str = "USD") -> Dict[str, Any]:
        """
        Calculates the monthly financial projections based on captured volume and transport costs.
        """
        # Get dynamic prices
        eth_price, carb_price, symbol = self.market.get_prices(currency=currency)
        
        # REVENUES
        # 1. Direct Ethanol Sales
        ethanol_revenue = volume_tons * eth_price
        
        # 2. Carbon Credit Revenue (Offsetting methane emissions)
        # Assuming 1 ton ethanol roughly requires capturing 1 ton of methane (simplified mass balance)
        co2e_avoided_tons = volume_tons * self.methane_gwp
        carbon_revenue = co2e_avoided_tons * carb_price
        
        total_revenue = ethanol_revenue + carbon_revenue
        
        # EXPENSES
        # Convert base expenses to requested currency (MarketService tracks exchange rates)
        rate = self.market.exchange_rates.get(currency.upper(), 1.0)
        capex_local = self.capex_monthly * rate
        opex_local = self.opex_monthly * rate
        
        total_expenses = capex_local + opex_local + transport_cost
        
        # NET PROFIT & ROI
        net_profit = total_revenue - total_expenses
        
        # Monthly ROI = (Net Profit / Total Expenses) * 100
        roi_percentage = (net_profit / total_expenses) * 100 if total_expenses > 0 else 0.0
        
        return {
            "currency_symbol": symbol,
            "revenues": {
                "ethanol_sales": ethanol_revenue,
                "carbon_credits": carbon_revenue,
                "total_revenue": total_revenue
            },
            "expenses": {
                "capex_amortized": capex_local,
                "opex_base": opex_local,
                "transport_logistics": transport_cost,
                "total_expenses": total_expenses
            },
            "net_profit": net_profit,
            "roi_percentage": roi_percentage,
            "co2e_avoided_tons": co2e_avoided_tons
        }
