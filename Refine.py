def refine_business_kpis(df, roles):
    """
    This function takes raw detected columns
    and tries to decide which ones actually
    make sense for business analysis.
    """

    # This dictionary will store the final KPIs
    refined = {
        "date": None,        # main date column
        "revenue": None,     # revenue column
        "quantity": None,    # quantity / units column
        "profit": None,      # profit column (if any)
        "dimensions": [],    # category columns
        "warnings": []       # warnings if something is missing
    }

    # --------------------------------------------------
    # 1️⃣ DATE SELECTION (MOST IMPORTANT)
    # --------------------------------------------------
    # If we see "Order Date", we prefer that
    # because it usually makes more sense
    for col in roles["categorical"]:
        if "order date" in col.lower():
            refined["date"] = col
            break

    # If Order Date not found, use detected date column
    if not refined["date"] and roles["date"]:
        refined["date"] = roles["date"]["column"]
        refined["warnings"].append(
            f"Using {refined['date']} as primary date"
        )

    # If still nothing, add warning
    if not refined["date"]:
        refined["warnings"].append("No date column resolved")

    # --------------------------------------------------
    # 2️⃣ REVENUE SELECTION
    # --------------------------------------------------
    # Try to pick a column that clearly sounds like revenue
    for item in roles["kpi_candidates"]["monetary"]:
        col = item["column"].lower()

        if any(x in col for x in ["sales", "revenue", "amount", "total"]):
            refined["revenue"] = item["column"]
            break

    # If nothing matched by name, pick the best candidate
    if not refined["revenue"] and roles["kpi_candidates"]["monetary"]:
        refined["revenue"] = roles["kpi_candidates"]["monetary"][0]["column"]

    # --------------------------------------------------
    # 3️⃣ QUANTITY SELECTION
    # --------------------------------------------------
    # Quantity should NOT be price or discount
    for item in roles["kpi_candidates"]["quantity"]:
        col = item["column"].lower()

        # Skip wrong quantity-like columns
        if any(x in col for x in ["price", "rate", "discount"]):
            continue

        if any(x in col for x in ["qty", "quantity", "unit", "units", "count"]):
            refined["quantity"] = item["column"]
            break

    # Fallback: pick top quantity candidate
    if not refined["quantity"] and roles["kpi_candidates"]["quantity"]:
        refined["quantity"] = roles["kpi_candidates"]["quantity"][0]["column"]

    # --------------------------------------------------
    # 4️⃣ PROFIT COLUMN CHECK
    # --------------------------------------------------
    # Profit is optional, so we just check if it exists
    for col in roles["numeric"]:
        if "profit" in col.lower():
            refined["profit"] = col
            break

    # --------------------------------------------------
    # 5️⃣ DIMENSION CLEANUP (VERY IMPORTANT)
    # --------------------------------------------------
    # We don’t want too many categories
    # So we divide them into Tier-1 and Tier-2

    # Tier-1 keywords are most useful for business
    priority_keywords = [
        "segment", "category", "sub", "region",
        "ship", "channel", "store"
    ]

    tier1_dims = []  # important dimensions
    tier2_dims = []  # optional deep-dive dimensions

    for col in roles["categorical"]:

        # Skip date column
        if col == refined["date"]:
            continue

        # Skip ID-like or date-like columns
        if "id" in col.lower() or "date" in col.lower():
            continue

        # Check how many unique values exist
        # Too many unique values = messy analysis
        cardinality_ratio = df[col].nunique(dropna=True) / max(1, len(df))

        # If column name matches priority keywords → Tier-1
        if any(k in col.lower() for k in priority_keywords):
            tier1_dims.append(col)
            continue

        # Otherwise keep only medium-cardinality columns
        if cardinality_ratio < 0.3:
            tier2_dims.append(col)

    # By default, we only use Tier-1 dimensions
    refined["dimensions"] = tier1_dims

    # Tier-2 is kept hidden for deeper analysis
    refined["_tier2_dimensions"] = tier2_dims

    return refined
