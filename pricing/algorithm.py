"""Pricing algorithms for dynamic pricing demo.

This module provides:
- a simple demand estimator using price elasticity and competitor adjustment
- a grid-search optimizer that recommends a price to maximize expected profit
- a small mock for competitor price (no network calls) to keep the demo self-contained

The models are intentionally simple and conservative for demonstration and unit tests.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class Product:
    id: str
    name: str
    cost: float
    base_price: float
    base_demand: float
    elasticity: float  # price elasticity (>0)
    inventory: int


class PricingEngine:
    def __init__(self, products_data: List[Dict]):
        # load products into Product instances
        self.products: Dict[str, Product] = {}
        for p in products_data:
            prod = Product(
                id=p["id"],
                name=p.get("name", ""),
                cost=float(p["cost"]),
                base_price=float(p.get("base_price", p["cost"] * 1.5)),
                base_demand=float(p.get("base_demand", 100)),
                elasticity=float(p.get("elasticity", 1.5)),
                inventory=int(p.get("inventory", 100)),
            )
            self.products[prod.id] = prod

    def _mock_competitor_price(self, product: Product) -> float:
        """Return a mock competitor price for the product.

        This is deterministic (non-network) and roughly near base_price to
        allow the optimizer to consider competitive pressure.
        """
        # simple heuristic: competitor price = base_price * (1 + small offset)
        offset = 0.05 * (hash(product.id) % 5 - 2) / 2.0  # pseudo-random small offset
        return max(product.cost * 1.01, product.base_price * (1 + offset))

    def estimate_demand(self, product: Product, price: float, competitor_price: Optional[float] = None) -> float:
        """Estimate expected demand at a given price.

        - Base demand is scaled by price via a log-linear elasticity model.
        - If competitor price is lower, demand reduces further; if higher, demand increases slightly.
        - Demand is never negative.
        """
        if price <= 0:
            return 0.0

        p_ref = product.base_price
        # elasticity model: demand ∝ (p_ref / price) ** elasticity
        demand = product.base_demand * (p_ref / price) ** product.elasticity

        # competitor effect
        if competitor_price is None:
            competitor_price = self._mock_competitor_price(product)

        # if competitor is cheaper, reduce share proportional to difference
        comp_diff = (competitor_price - price) / max(competitor_price, price, 1e-6)
        # alpha controls sensitivity to competitor price; small by default
        alpha = 0.25
        demand *= max(0.0, 1.0 + alpha * comp_diff)

        return max(0.0, demand)

    def expected_profit(self, product: Product, price: float, competitor_price: Optional[float] = None) -> Tuple[float, float]:
        """Return tuple (expected_profit, expected_sales) under inventory cap.

        expected_profit = (price - cost) * expected_sales
        expected_sales = min(estimated_demand, inventory)
        """
        est = self.estimate_demand(product, price, competitor_price)
        sales = min(est, product.inventory)
        profit = (price - product.cost) * sales
        return profit, sales

    def recommend_price(self, product_id: str, price_grid_steps: int = 200) -> Dict:
        """Recommend a price for a product to maximize expected profit.

        Strategy:
        - Build a price grid between cost+epsilon and max_search_price
        - Evaluate expected profit on the grid and pick the price that maximizes profit
        - Return recommendation details
        """
        product = self.products[product_id]
        comp_price = self._mock_competitor_price(product)

        low = max(product.cost * 1.01, product.base_price * 0.5)
        high = max(product.base_price * 1.6, comp_price * 1.4, product.cost * 3)
        best_price = low
        best_profit = -1e12
        best_sales = 0.0

        for i in range(price_grid_steps + 1):
            price = low + (high - low) * i / price_grid_steps
            profit, sales = self.expected_profit(product, price, comp_price)
            if profit > best_profit:
                best_profit = profit
                best_price = round(price, 2)
                best_sales = sales

        # also compute revenue at recommended price and margin
        revenue = best_price * best_sales
        margin = (best_price - product.cost) / (best_price + 1e-9)

        return {
            "recommended_price": best_price,
            "expected_profit": round(best_profit, 2),
            "expected_sales": round(best_sales, 2),
            "expected_revenue": round(revenue, 2),
            "margin": round(margin, 3),
            "competitor_price": round(comp_price, 2),
        }

    def simulate_change(self, product_id: str, new_price: float) -> Dict:
        """Simulate what would happen at a chosen price: returns expected sales, profit, revenue."""
        product = self.products[product_id]
        comp_price = self._mock_competitor_price(product)
        profit, sales = self.expected_profit(product, new_price, comp_price)
        return {
            "price": round(new_price, 2),
            "expected_sales": round(sales, 2),
            "expected_profit": round(profit, 2),
            "expected_revenue": round(new_price * sales, 2),
        }
