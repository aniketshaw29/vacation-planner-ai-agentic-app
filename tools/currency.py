INR_PER_USD = 84

def to_inr(usd: float) -> int:
    return round(usd * INR_PER_USD)

def inr(usd: float) -> str:
    """Return a ₹-formatted string with Indian number formatting."""
    n = to_inr(usd)
    return f"₹{n:,}"
