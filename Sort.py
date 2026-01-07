import pandas as pd
import re

# -----------------------------------
# Keywords to guess column meaning
# -----------------------------------
# These words help us guess what a column might represent
# based on its name (not 100% accurate, just a hint)
name_signals = {
    "date": ["date", "dt", "time", "month", "year", "day"],
    "monetary": ["revenue", "sales", "amount", "amt", "total", "price", "income"],
    "cost": ["cost", "expense", "exp"],
    "quantity": ["qty", "quantity", "unit", "units", "count"]
}

def name_signal_score(col_name, signal_type):
    """
    Checks if a column name contains any keyword
    related to the given signal type.
    Returns 1 if yes, else 0.
    """
    col = col_name.lower()
    for token in name_signals.get(signal_type, []):
        if token in col:
            return 1
    return 0


# -----------------------------------
# Main function to identify column roles
# -----------------------------------
def col_role(df, sample_limit=5000):

    # This dictionary will store all detected roles
    roles = {
        "date": None,
        "categorical": [],
        "numeric": [],
        "identifiers": [],
        "kpi_candidates": {
            "monetary": [],
            "quantity": [],
            "cost": []
        },
        "warnings": []
    }

    # To keep things fast, we work on a sample if data is very large
    sample = df.sample(sample_limit, random_state=42) if len(df) > sample_limit else df.copy()

    # -----------------------------------
    # Step 1: Separate numeric and categorical columns
    # -----------------------------------
    numeric_col = []
    categorical_col = []

    for col in sample.columns:

        # Try converting column values to numbers
        # Remove currency symbols if present
        numeric_try = pd.to_numeric(
            sample[col].astype(str).str.replace(r"[₹,$,]", "", regex=True),
            errors="coerce"
        )

        # If most values are numbers, treat column as numeric
        if numeric_try.notna().mean() >= 0.6:
            numeric_col.append(col)
        else:
            categorical_col.append(col)

    roles["numeric"] = numeric_col
    roles["categorical"] = categorical_col

    # -----------------------------------
    # Step 2: Detect ID columns (based on values)
    # -----------------------------------
    id_cols = []

    for col in roles["numeric"]:
        clean_col = pd.to_numeric(sample[col], errors="coerce")

        # ID columns usually have:
        # - mostly unique values
        # - mostly integers
        unique_ratio = clean_col.nunique(dropna=True) / len(clean_col)
        integer_ratio = (clean_col.dropna() % 1 == 0).mean()

        if unique_ratio >= 0.9 and integer_ratio >= 0.9:
            id_cols.append(col)

    # -----------------------------------
    # Step 3: Detect ID columns (based on name)
    # -----------------------------------
    # If column name contains "id", it is probably an identifier
    for col in roles["numeric"]:
        if "id" in col.lower():
            id_cols.append(col)

    roles["identifiers"] = list(set(id_cols))

    # Remove ID columns from numeric list
    roles["numeric"] = [c for c in roles["numeric"] if c not in roles["identifiers"]]

    # -----------------------------------
    # Step 4: Detect date column
    # -----------------------------------
    date_score = []

    for col in sample.columns:

        # Skip numeric and ID columns
        if col in roles["numeric"] or col in roles["identifiers"]:
            continue

        try:
            parsed = pd.to_datetime(sample[col], errors="coerce")
            parse_rate = parsed.notna().mean()

            # Column is considered date if most values parse correctly
            if parse_rate >= 0.9 and parsed.nunique() > 1:
                score = 0.7 * parse_rate
                score += 0.1 * name_signal_score(col, "date")

                # Dates often go in one direction (increasing or decreasing)
                if parsed.is_monotonic_increasing or parsed.is_monotonic_decreasing:
                    score += 0.2

                date_score.append((col, score))
        except:
            continue

    if date_score:
        date_score.sort(key=lambda x: x[1], reverse=True)
        roles["date"] = {
            "column": date_score[0][0],
            "confidence": round(date_score[0][1], 2)
        }
    else:
        roles["warnings"].append("No date column confidently detected")

    # -----------------------------------
    # Step 5: Basic stats for numeric columns
    # -----------------------------------
    numeric_stat = {}

    for col in roles["numeric"]:
        clean_col = pd.to_numeric(
            sample[col].astype(str).str.replace(r"[₹,$,]", "", regex=True),
            errors="coerce"
        )

        numeric_stat[col] = {
            "mean": clean_col.mean(),
            "integer_ratio": (clean_col.dropna() % 1 == 0).mean(),
            "neg_ratio": (clean_col < 0).mean()
        }

    # Sort columns by size of values (big numbers often mean money)
    magnitude_rank = sorted(
        numeric_stat.items(),
        key=lambda x: abs(x[1]["mean"]) if x[1]["mean"] is not None else 0,
        reverse=True
    )

    # -----------------------------------
    # Step 6: Score KPI candidates
    # -----------------------------------
    for col, stats in numeric_stat.items():

        monetary_score = 0
        quantity_score = 0
        cost_score = 0

        # Largest numeric column might be revenue or total
        if magnitude_rank and col == magnitude_rank[0][0]:
            monetary_score += 0.4

        if "total" in col.lower():
            monetary_score += 0.3

        monetary_score += 0.3 * name_signal_score(col, "monetary")
        quantity_score += 0.3 * name_signal_score(col, "quantity")
        cost_score += 0.3 * name_signal_score(col, "cost")

        # Quantities are usually integers (price is excluded)
        if "price" not in col.lower() and "rate" not in col.lower():
            quantity_score += 0.4 * stats["integer_ratio"]

        # Costs often have negative values
        cost_score += 0.3 * stats["neg_ratio"]

        if monetary_score > 0:
            roles["kpi_candidates"]["monetary"].append(
                {"column": col, "score": round(monetary_score, 2)}
            )

        if quantity_score > 0:
            roles["kpi_candidates"]["quantity"].append(
                {"column": col, "score": round(quantity_score, 2)}
            )

        if cost_score > 0:
            roles["kpi_candidates"]["cost"].append(
                {"column": col, "score": round(cost_score, 2)}
            )

    # -----------------------------------
    # Step 7: Detect Total = Quantity × Price
    # -----------------------------------
    for total_col in roles["numeric"]:
        for qty_col in roles["numeric"]:
            for price_col in roles["numeric"]:

                # All three columns must be different
                if len({total_col, qty_col, price_col}) < 3:
                    continue

                try:
                    lhs = sample[qty_col] * sample[price_col]
                    rhs = sample[total_col]

                    # Check if calculation matches for most rows
                    match_rate = (abs(lhs - rhs) / rhs).dropna().lt(0.01).mean()

                    if match_rate >= 0.8:
                        roles["kpi_candidates"]["monetary"].append(
                            {"column": total_col, "score": 1.0}
                        )
                        roles["kpi_candidates"]["quantity"].append(
                            {"column": qty_col, "score": 1.0}
                        )
                except:
                    continue

    # -----------------------------------
    # Step 8: Remove duplicate KPI entries
    # -----------------------------------
    def dedupe_kpis(kpi_list):
        best = {}
        for item in kpi_list:
            col = item["column"]
            if col not in best or item["score"] > best[col]["score"]:
                best[col] = item
        return list(best.values())

    for k in roles["kpi_candidates"]:
        roles["kpi_candidates"][k] = dedupe_kpis(roles["kpi_candidates"][k])

    # -----------------------------------
    # Step 9: Final cleanup
    # -----------------------------------
    # ID columns should never be KPIs
    for k in roles["kpi_candidates"]:
        roles["kpi_candidates"][k] = [
            x for x in roles["kpi_candidates"][k]
            if x["column"] not in roles["identifiers"]
        ]

    for k in roles["kpi_candidates"]:
        roles["kpi_candidates"][k].sort(key=lambda x: x["score"], reverse=True)

    if not roles["kpi_candidates"]["monetary"]:
        roles["warnings"].append("No strong monetary KPI candidate detected")

    return roles
