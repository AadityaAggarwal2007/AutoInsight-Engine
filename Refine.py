def refine_business_kpis(df, roles):
    """
    Phase 3 – Step 1
    Business-aware KPI refinement (tiered dimensions)
    """

    refined = {
        "date": None,
        "revenue": None,
        "quantity": None,
        "profit": None,
        "dimensions": [],
        "warnings": []
    }

    # -----------------------------
    # 1️⃣ DATE REFINEMENT (PRIORITY)
    # -----------------------------
    # Prefer Order Date over Ship Date
    for col in roles["categorical"]:
        if "order date" in col.lower():
            refined["date"] = col
            break

    if not refined["date"] and roles["date"]:
        refined["date"] = roles["date"]["column"]
        refined["warnings"].append(
            f"Using {refined['date']} as primary date"
        )

    if not refined["date"]:
        refined["warnings"].append("No date column resolved")

    # -----------------------------
    # 2️⃣ REVENUE REFINEMENT
    # -----------------------------
    for item in roles["kpi_candidates"]["monetary"]:
        col = item["column"].lower()
        if any(x in col for x in ["sales", "revenue", "amount", "total"]):
            refined["revenue"] = item["column"]
            break

    if not refined["revenue"] and roles["kpi_candidates"]["monetary"]:
        refined["revenue"] = roles["kpi_candidates"]["monetary"][0]["column"]

    # -----------------------------
    # 3️⃣ QUANTITY REFINEMENT
    # -----------------------------
    for item in roles["kpi_candidates"]["quantity"]:
        col = item["column"].lower()
        if any(x in col for x in ["price", "rate", "discount"]):
            continue
        if any(x in col for x in ["qty", "quantity", "unit", "units", "count"]):
            refined["quantity"] = item["column"]
            break

    if not refined["quantity"] and roles["kpi_candidates"]["quantity"]:
        refined["quantity"] = roles["kpi_candidates"]["quantity"][0]["column"]

    # -----------------------------
    # 4️⃣ PROFIT DETECTION
    # -----------------------------
    for col in roles["numeric"]:
        if "profit" in col.lower():
            refined["profit"] = col
            break

    # -----------------------------
    # 5️⃣ DIMENSION HYGIENE (TIERED)
    # -----------------------------
    # Tier-1 keywords: prefer these for top-level insights
    priority_keywords = [
        "segment", "category", "sub", "region", "ship", "channel", "store"
    ]

    tier1_dims = []
    tier2_dims = []

    for col in roles["categorical"]:
        if col == refined["date"]:
            continue
        # drop explicit ids and date columns
        if "id" in col.lower() or "date" in col.lower():
            continue

        # cardinality ratio (how many unique values relative to rows)
        cardinality_ratio = df[col].nunique(dropna=True) / max(1, len(df))

        # If name matches priority keywords, force keep (Tier-1)
        if any(k in col.lower() for k in priority_keywords):
            tier1_dims.append(col)
            continue

        # Otherwise decide by cardinality: keep as Tier-2 if medium cardinality (< 0.3)
        if cardinality_ratio < 0.3:
            tier2_dims.append(col)

    # default dimensions = Tier-1 only (Tier-2 remains available if needed)
    clean_dims = tier1_dims

    refined["dimensions"] = clean_dims
    # expose tier2 for optional deeper analysis (not used by default)
    refined["_tier2_dimensions"] = tier2_dims

    return refined
