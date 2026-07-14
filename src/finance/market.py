import random
from datetime import datetime, timedelta
from typing import Tuple

class MarketPriceService:
    def __init__(self):
        """
        Simulates live market prices for Bio-Ethanol and EU ETS Carbon Credits.
        Includes a 6-hour caching mechanism.
        """
        # Baseline prices in USD per ton
        self.baseline_ethanol_usd = 850.0  # Approx $850/ton for Bio-Ethanol
        self.baseline_carbon_usd = 70.0    # Approx $70/ton for EU ETS allowances
        
        self.current_ethanol_usd = self.baseline_ethanol_usd
        self.current_carbon_usd = self.baseline_carbon_usd
        
        self.last_updated_time = datetime.min
        self.refresh_interval = timedelta(hours=6)
        
        # Mock exchange rates (Base: 1 USD)
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "CNY": 7.23
        }

    def _fetch_live_prices(self):
        """Simulates fetching fluctuating market prices from an API."""
        eth_fluctuation = random.uniform(-0.15, 0.15)
        carb_fluctuation = random.uniform(-0.10, 0.10)
        
        self.current_ethanol_usd = self.baseline_ethanol_usd * (1 + eth_fluctuation)
        self.current_carbon_usd = self.baseline_carbon_usd * (1 + carb_fluctuation)

    def get_prices(self, currency: str = "USD") -> Tuple[float, float, str]:
        """
        Returns the current market prices for Ethanol and Carbon Credits in the requested currency.
        Returns: (ethanol_price, carbon_price, currency_symbol)
        """
        now = datetime.now()
        if now - self.last_updated_time >= self.refresh_interval:
            print(f"   [MARKET SERVICE] Cache expired. Fetching live commodity prices... (Last updated: {self.last_updated_time})")
            self._fetch_live_prices()
            self.last_updated_time = now
            
        currency = currency.upper()
        if currency not in self.exchange_rates:
            print(f"   [MARKET SERVICE] Currency {currency} not supported, defaulting to USD.")
            currency = "USD"
            
        rate = self.exchange_rates[currency]
        eth_converted = self.current_ethanol_usd * rate
        carb_converted = self.current_carbon_usd * rate
        
        symbols = {"USD": "$", "EUR": "€", "CNY": "¥"}
        
        return round(eth_converted, 2), round(carb_converted, 2), symbols[currency]
