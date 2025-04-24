class BudgetEstimatorAgent:
    def estimate_budget(self, state):
        flights = state.get("flights", {}).get("estimated_cost", 0)
        hotels = state.get("hotels", {}).get("estimated_cost", 0)
        food_cost_per_day = {"Low": 50, "Medium": 100, "High": 200}.get(state.get("budget"), 100)
        days = (state.get("end_date") - state.get("start_date")).days + 1
        
        total = flights + hotels + (food_cost_per_day * days)
        state["budget_estimate"] = {
            "flights": flights,
            "hotels": hotels,
            "food": food_cost_per_day * days,
            "total": total
        }
        return state