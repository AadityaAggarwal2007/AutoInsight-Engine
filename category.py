import pandas as pd

def revenue_growth_engine(df, business_kpis):
    """
    Phase 3 – Step 2
    Revenue & Growth Engine (Refined + Presentation)
    """

    results = {
        "total_revenue": None,
        "time_grain": None,
        "revenue_over_time": None,
        "growth_over_time": None,
        "by_dimension": {},
        "top_contributors": {},
        "warnings": []
    }

    date_col = business_kpis["date"]
    revenue_col = business_kpis["revenue"]
    dimensions = business_kpis["dimensions"]

    if not date_col or not revenue_col:
        results["warnings"].append("Missing date or revenue column")
        return results

    data = df[[date_col, revenue_col] + dimensions].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col, revenue_col])

    # -----------------------------
    # Total revenue (rounded 2 dp)
    # -----------------------------
    results["total_revenue"] = round(data[revenue_col].sum(), 2)

    # -----------------------------
    # Time grain detection
    # -----------------------------
    span_days = (data[date_col].max() - data[date_col].min()).days
    if span_days > 120:
        freq = "ME"   # month-end
        results["time_grain"] = "Monthly"
    else:
        freq = "W"
        results["time_grain"] = "Weekly"

    # -----------------------------
    # Revenue over time (rounded)
    # -----------------------------
    rev_time = (
        data
        .set_index(date_col)
        .resample(freq)[revenue_col]
        .sum()
        .reset_index()
    )

    # Growth sanity: treat zero-revenue periods as missing to avoid wild pct changes
    rev_time.loc[rev_time[revenue_col] == 0, revenue_col] = pd.NA

    # Round revenue and growth
    rev_time[revenue_col] = rev_time[revenue_col].round(2)
    rev_time["growth_pct"] = rev_time[revenue_col].pct_change() * 100
    rev_time["growth_pct"] = rev_time["growth_pct"].round(2)

    results["revenue_over_time"] = rev_time
    results["growth_over_time"] = rev_time[[date_col, "growth_pct"]]

    # -----------------------------
    # Revenue by dimension (rounded)
    # -----------------------------
    for dim in dimensions:
        dim_rev = (
            data
            .groupby(dim)[revenue_col]
            .sum()
            .round(2)
            .sort_values(ascending=False)
            .reset_index()
        )

        results["by_dimension"][dim] = dim_rev
        results["top_contributors"][dim] = dim_rev.head(3)

    return results
