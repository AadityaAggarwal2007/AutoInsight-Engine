import pandas as pd

def revenue_growth_engine(df, business_kpis):
    """
    This function helps us understand revenue.
    It calculates total revenue, growth over time,
    and shows which categories make the most money.
    """

    # -----------------------------------
    # This dictionary will store everything
    # we calculate step by step
    # -----------------------------------
    results = {
        "total_revenue": None,        # total money earned
        "time_grain": None,           # weekly or monthly
        "revenue_over_time": None,    # revenue trend
        "growth_over_time": None,     # growth percentage
        "by_dimension": {},           # revenue by category
        "top_contributors": {},       # top 3 contributors
        "warnings": []                # problems if any
    }

    # -----------------------------------
    # Getting column names from input
    # -----------------------------------
    date_col = business_kpis["date"]        # date column name
    revenue_col = business_kpis["revenue"]  # revenue column name
    dimensions = business_kpis["dimensions"]  # category columns

    # -----------------------------------
    # Safety check (very important!)
    # -----------------------------------
    if not date_col or not revenue_col:
        # If we don’t have date or revenue,
        # we cannot do any analysis
        results["warnings"].append("Missing date or revenue column")
        return results

    # -----------------------------------
    # Keep only required columns
    # -----------------------------------
    data = df[[date_col, revenue_col] + dimensions].copy()

    # Convert date column into datetime format
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")

    # Remove rows where date or revenue is missing
    data = data.dropna(subset=[date_col, revenue_col])

    # -----------------------------------
    # Calculate TOTAL revenue
    # -----------------------------------
    # Add all revenue values and round to 2 decimals
    results["total_revenue"] = round(data[revenue_col].sum(), 2)

    # -----------------------------------
    # Decide if we use Weekly or Monthly data
    # -----------------------------------
    # Find how many days the data covers
    span_days = (data[date_col].max() - data[date_col].min()).days

    if span_days > 120:
        # Long time range → Monthly view
        freq = "ME"   # month-end
        results["time_grain"] = "Monthly"
    else:
        # Short time range → Weekly view
        freq = "W"
        results["time_grain"] = "Weekly"

    # -----------------------------------
    # Revenue over time
    # -----------------------------------
    # Group revenue by week or month
    rev_time = (
        data
        .set_index(date_col)
        .resample(freq)[revenue_col]
        .sum()
        .reset_index()
    )

    # -----------------------------------
    # Growth calculation safety
    # -----------------------------------
    # If revenue is zero, growth % becomes crazy
    # so we treat zero revenue as missing
    rev_time.loc[rev_time[revenue_col] == 0, revenue_col] = pd.NA

    # Round revenue values
    rev_time[revenue_col] = rev_time[revenue_col].round(2)

    # Calculate percentage growth
    rev_time["growth_pct"] = rev_time[revenue_col].pct_change() * 100

    # Round growth values
    rev_time["growth_pct"] = rev_time["growth_pct"].round(2)

    # Save results
    results["revenue_over_time"] = rev_time
    results["growth_over_time"] = rev_time[[date_col, "growth_pct"]]

    # -----------------------------------
    # Revenue by each dimension
    # -----------------------------------
    for dim in dimensions:

        # Group revenue by category
        dim_rev = (
            data
            .groupby(dim)[revenue_col]
            .sum()
            .round(2)
            .sort_values(ascending=False)
            .reset_index()
        )

        # Store full data
        results["by_dimension"][dim] = dim_rev

        # Store top 3 contributors
        results["top_contributors"][dim] = dim_rev.head(3)

    # -----------------------------------
    # Finally return everything
    # -----------------------------------
    return results
