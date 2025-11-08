import json
import os
import sys

# Add parent directory to path to import pricing module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pricing.algorithm import PricingEngine


def load_products():
    products_path = os.path.join(os.path.dirname(__file__), '..', 'products.json')
    with open(products_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_recommendations_return_reasonable_values():
    """Test that pricing recommendations are sensible and respect constraints."""
    products = load_products()
    engine = PricingEngine(products)

    for p in products:
        rec = engine.recommend_price(p["id"]) 
        # recommended price should be at least above cost
        assert rec["recommended_price"] > float(p["cost"]) - 1e-6, \
            f"Price {rec['recommended_price']} should be > cost {p['cost']}"
        # expected sales should be non-negative and <= inventory
        assert rec["expected_sales"] >= 0, \
            f"Sales should be non-negative, got {rec['expected_sales']}"
        assert rec["expected_sales"] <= p["inventory"] + 1e-6, \
            f"Sales {rec['expected_sales']} should not exceed inventory {p['inventory']}"
        # profit should be reasonable
        assert rec["expected_profit"] >= 0, \
            f"Profit should be non-negative at optimal price"


def test_simulate_change_consistency():
    """Test that simulation matches recommendation at the recommended price."""
    products = load_products()
    engine = PricingEngine(products)
    p = products[0]
    rec = engine.recommend_price(p["id"]) 
    sim = engine.simulate_change(p["id"], rec["recommended_price"]) 
    # simulation at recommended price should match expected_sales/profit values
    assert abs(sim["expected_sales"] - rec["expected_sales"]) < 0.1, \
        f"Simulation sales {sim['expected_sales']} should match recommendation {rec['expected_sales']}"
    assert abs(sim["expected_profit"] - rec["expected_profit"]) < 0.1, \
        f"Simulation profit {sim['expected_profit']} should match recommendation {rec['expected_profit']}"


def test_demand_estimation():
    """Test that demand decreases as price increases (elasticity)."""
    products = load_products()
    engine = PricingEngine(products)
    product = engine.products["p1"]
    
    # Lower price should give higher demand
    demand_low = engine.estimate_demand(product, product.base_price * 0.8)
    demand_high = engine.estimate_demand(product, product.base_price * 1.2)
    
    assert demand_low > demand_high, \
        f"Lower price should yield higher demand: {demand_low} vs {demand_high}"


def test_inventory_constraint():
    """Test that expected sales never exceed inventory."""
    products = load_products()
    engine = PricingEngine(products)
    
    for p in products:
        product = engine.products[p["id"]]
        # Test at very low price (high demand scenario)
        low_price = product.cost * 1.1
        profit, sales = engine.expected_profit(product, low_price)
        
        assert sales <= product.inventory, \
            f"Sales {sales} should not exceed inventory {product.inventory}"


def test_competitor_effect():
    """Test that competitor pricing affects demand appropriately."""
    products = load_products()
    engine = PricingEngine(products)
    product = engine.products["p1"]
    
    price = product.base_price
    # When competitor is more expensive, we get more demand
    demand_comp_high = engine.estimate_demand(product, price, competitor_price=price * 1.5)
    # When competitor is cheaper, we get less demand
    demand_comp_low = engine.estimate_demand(product, price, competitor_price=price * 0.8)
    
    assert demand_comp_high > demand_comp_low, \
        f"Higher competitor price should increase our demand"
