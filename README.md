# Minimal E‑commerce Dynamic Pricing Demo

This repository demonstrates a simple dynamic pricing approach for an e-commerce setting with a minimalist web UI.

## What you get
- A Python module `pricing/algorithm.py` implementing a small demand estimator and grid-search optimizer balancing demand, competition, and inventory.
- A minimal Flask app (`app.py`) that shows recommended prices for sample products.
- A tiny minimalist frontend (`templates/index.html`, `static/style.css`).
- Sample data in `products.json` and a couple of tests under `tests/`.

## Quick start (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Run tests

```powershell
pytest -v
```

## Notes
- The competitor-pricing function is a deterministic mock (no network calls) so the demo is self-contained.
- The pricing model is intentionally simple. For production, replace with real demand forecasting (time series or ML), competitor scraping (with care), A/B testing, constraints, and safety rules.

## How it works

### Pricing Algorithm
The `PricingEngine` in `pricing/algorithm.py` implements:

1. **Demand Estimation**: Uses price elasticity model where demand responds to price changes
   - Formula: `demand = base_demand * (base_price / price) ** elasticity`
   - Adjusts for competitor pricing (if competitor is cheaper, demand decreases)

2. **Profit Optimization**: Grid search over possible prices to maximize:
   - `expected_profit = (price - cost) * min(estimated_demand, inventory)`
   - Considers inventory constraints (can't sell more than available stock)

3. **Competitor Awareness**: Mock competitor prices to simulate market competition
   - In production, replace with real competitor data scraping or API integration

4. **Inventory Management**: Caps sales at available inventory level
   - Prevents overselling
   - Encourages higher prices when inventory is low

### API Endpoints
- `GET /` - Main page showing all products with pricing recommendations
- `GET /api/recommendations` - JSON API returning pricing data for all products
