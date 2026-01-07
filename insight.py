import pandas as pd
import numpy as np

# --------------------------------------------------
# PHASE 3 – STEP 3
# This part tries to "read" the data
# and tell us what is actually happening
# --------------------------------------------------

def generate_insights(growth_results, business_kpis):
    """
    This function looks at revenue numbers
    and converts them into simple business insights
    that humans can understand.
    """

    # This list will store all insights we find
    insights = []

    # Getting important column names
    revenue_col = business_kpis["revenue"]
    date_col = business_kpis["date"]

    # Getting total revenue value
    total_revenue = growth_results["total_revenue"]

    # Revenue over time table
    rev_time = growth_results["revenue_over_time"].copy()

    # Growth percentage column (remove missing values)
    growth = rev_time["growth_pct"].dropna()

    # --------------------------------------------------
    # 1️⃣ TREND CHECK
    # --------------------------------------------------
    # Check last two periods to see basic trend
    if len(growth) >= 2:
        last_two = growth.tail(2)

        # If both periods are negative → bad sign
        if (last_two < 0).all():
            insights.append({
                "type": "trend",
                "severity": 5,
                "text": "Revenue declined for two consecutive periods."
            })

        # If both periods are positive → good sign
        elif (last_two > 0).all():
            insights.append({
                "type": "trend",
                "severity": 4,
                "text": "Revenue grew for two consecutive periods."
            })

    # --------------------------------------------------
    # Check for long decline streak
    # --------------------------------------------------
    streak = 0
    max_streak = 0

    for g in growth:
        if g < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    if max_streak >= 3:
        insights.append({
            "type": "trend",
            "severity": 5,
            "text": f"Revenue experienced a prolonged decline lasting {max_streak} periods."
        })

    # --------------------------------------------------
    # 2️⃣ VOLATILITY CHECK
    # --------------------------------------------------
    # Very high ups and downs = risky
    if len(growth) >= 3 and growth.std() > 50:
        insights.append({
            "type": "volatility",
            "severity": 4,
            "text": "Growth volatility is high; short-term spikes should be interpreted cautiously."
        })

    # --------------------------------------------------
    # 3️⃣ REBOUND CHECK
    # --------------------------------------------------
    # Big fall followed by big rise
    if len(growth) >= 3:
        prev, curr = growth.iloc[-2], growth.iloc[-1]

        if prev < -20 and curr > 50:
            insights.append({
                "type": "trend",
                "severity": 4,
                "text": "Revenue rebounded sharply after a low baseline period."
            })

    # --------------------------------------------------
    # 4️⃣ DIMENSION LEADERS
    # --------------------------------------------------
    # Find who is making the most money
    for dim, table in growth_results["by_dimension"].items():

        if table.empty:
            continue

        top = table.iloc[0]
        share = (top[revenue_col] / total_revenue) * 100

        if share >= 35:
            insights.append({
                "type": "leader",
                "severity": 4,
                "text": f"{top[dim]} is the leading {dim.lower()}, contributing approximately {share:.1f}% of total revenue."
            })

    # --------------------------------------------------
    # 5️⃣ TOP-3 CONCENTRATION
    # --------------------------------------------------
    # Too much revenue from just 3 items = risky
    for dim, table in growth_results["by_dimension"].items():

        if len(table) < 3:
            continue

        top3_share = table.head(3)[revenue_col].sum() / total_revenue * 100

        if top3_share >= 70:
            insights.append({
                "type": "concentration",
                "severity": 4,
                "text": f"Revenue is highly concentrated — top 3 {dim.lower()} account for nearly {top3_share:.1f}% of total revenue."
            })

    # --------------------------------------------------
    # 6️⃣ 60% PARETO CHECK
    # --------------------------------------------------
    # How many items make 60% of revenue
    for dim, table in growth_results["by_dimension"].items():

        if table.empty:
            continue

        table = table.copy()
        table["cum_share"] = table[revenue_col].cumsum() / total_revenue * 100

        top_n = (table["cum_share"] <= 60).sum() + 1

        insights.append({
            "type": "pareto",
            "severity": 3,
            "text": f"Top {top_n} {dim.lower()} contribute approximately 60% of total revenue."
        })

    # --------------------------------------------------
    # 7️⃣ SINGLE DEPENDENCY RISK
    # --------------------------------------------------
    # One thing controlling too much revenue
    for dim, table in growth_results["by_dimension"].items():

        if table.empty:
            continue

        top = table.iloc[0]
        share = top[revenue_col] / total_revenue * 100

        if share >= 30:
            insights.append({
                "type": "risk",
                "severity": 5,
                "text": f"{top[dim]} alone contributes over {share:.1f}% of revenue, indicating potential concentration risk."
            })

    # --------------------------------------------------
    # 8️⃣ MIX BALANCE CHECK
    # --------------------------------------------------
    for dim, table in growth_results["by_dimension"].items():

        if len(table) < 3:
            continue

        shares = table[revenue_col] / total_revenue * 100

        if shares.max() - shares.min() < 15:
            insights.append({
                "type": "distribution",
                "severity": 2,
                "text": f"Revenue distribution across {dim.lower()} is relatively balanced."
            })
        elif shares.max() >= 50:
            insights.append({
                "type": "risk",
                "severity": 4,
                "text": f"Revenue is heavily skewed toward a single {dim.lower()}."
            })

    # --------------------------------------------------
    # 9️⃣ FALLBACK (if nothing found)
    # --------------------------------------------------
    if not insights:
        insights.append({
            "type": "general",
            "severity": 1,
            "text": "Revenue performance appears stable with no significant anomalies detected."
        })

    # Before returning, clean the insights
    return curate_insights(insights)


# --------------------------------------------------
# PHASE 3.5 – INSIGHT CLEANUP
# --------------------------------------------------

def curate_insights(raw_insights, max_insights=6):
    """
    Too many insights = confusion.
    This function:
    - keeps important ones
    - removes duplicates
    - limits total count
    """

    seen_types = set()
    curated = []

    # Sort insights by importance (severity)
    for ins in sorted(raw_insights, key=lambda x: x["severity"], reverse=True):

        if ins["type"] in seen_types:
            continue

        curated.append(ins["text"])
        seen_types.add(ins["type"])

        if len(curated) >= max_insights:
            break

    return curated


def generate_executive_summary(curated_insights):
    """
    Converts insights into a short paragraph
    that a manager can read quickly.
    """

    if not curated_insights:
        return "Revenue performance appears stable with no major risks or anomalies detected."

    summary = "Overall, "

    # Take first few important insights
    key_points = curated_insights[:4]

    summary += " ".join(
        insight.rstrip(".") + "."
        for insight in key_points
    )

    return summary


def generate_next_steps(curated_insights):
    """
    Suggests what to analyze next
    based on the insights found.
    """

    suggestions = []

    text_blob = " ".join(curated_insights).lower()

    if "decline" in text_blob:
        suggestions.append(
            "Investigate drivers behind recent revenue decline, particularly by category and region."
        )

    if "concentrated" in text_blob or "skewed" in text_blob:
        suggestions.append(
            "Assess dependency risk by evaluating performance of secondary segments or channels."
        )

    if "technology" in text_blob or "product" in text_blob:
        suggestions.append(
            "Analyze top products for margin, discounting, and repeat purchase behavior."
        )

    if "volatility" in text_blob:
        suggestions.append(
            "Review seasonality patterns and baseline effects to normalize growth interpretation."
        )

    # If nothing special is detected
    if not suggestions:
        suggestions.append(
            "Explore performance across time and key dimensions to identify hidden trends."
        )

    # Return only top 3 suggestions
    return suggestions[:3]
