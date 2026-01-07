import pandas as pd

from Sort import col_role
from Refine import refine_business_kpis
from category import revenue_growth_engine
from insight import (
    generate_insights,
    generate_executive_summary,
    generate_next_steps
)
from Charts import plot_revenue_trend, plot_pareto

pd.options.display.float_format = '{:,.2f}'.format


def load_data():
    path = input("\nEnter file path (CSV or Excel): ").strip()

    try:
        if path.lower().endswith(".csv"):
            df = pd.read_csv(path)
        elif path.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")

        print("\n✅ File loaded successfully")
        return df

    except Exception as e:
        print(f"\n❌ Failed to load file: {e}")
        exit()


if __name__ == "__main__":

    df = load_data()

    roles = col_role(df)

    print("\n--- DATE DETECTION ---")
    print(roles["date"])

    print("\n--- IDENTIFIERS ---")
    print(roles["identifiers"])

    print("\n--- NUMERIC COLUMNS ---")
    print(roles["numeric"])

    print("\n--- CATEGORICAL COLUMNS ---")
    print(roles["categorical"])

    business_kpis = refine_business_kpis(df, roles)

    print("\n--- BUSINESS KPIs ---")
    for k, v in business_kpis.items():
        if not k.startswith("_"):
            print(f"{k} : {v}")

    results = revenue_growth_engine(df, business_kpis)

    print("\n--- TOTAL REVENUE ---")
    print(results["total_revenue"])

    print("\n--- TIME GRAIN ---")
    print(results["time_grain"])

    print("\n--- REVENUE OVER TIME (HEAD) ---")
    print(results["revenue_over_time"].head())

    print("\n--- GROWTH OVER TIME (HEAD) ---")
    print(results["growth_over_time"].head())

    print("\n--- TOP CONTRIBUTORS ---")
    for dim, table in results["top_contributors"].items():
        print(f"\n{dim}")
        print(table)

    insights = generate_insights(results, business_kpis)

    print("\n--- KEY INSIGHTS ---")
    for i, text in enumerate(insights, 1):
        print(f"{i}. {text}")

    print("\n📊 Generating Revenue Trend Chart...")
    plot_revenue_trend(
        results["revenue_over_time"],
        business_kpis["date"],
        business_kpis["revenue"]
    )

    print("\n📊 Generating Pareto Charts...")
    for dim, table in results["by_dimension"].items():
        print(f"→ Pareto: {dim}")
        plot_pareto(
            table,
            dim,
            business_kpis["revenue"]
        )


insights = generate_insights(results, business_kpis)

print("\n--- KEY INSIGHTS ---")
for i, text in enumerate(insights, 1):
    print(f"{i}. {text}")

print("\n--- EXECUTIVE SUMMARY ---")
print(generate_executive_summary(insights))

print("\n--- WHAT TO LOOK AT NEXT ---")
for i, step in enumerate(generate_next_steps(insights), 1):
    print(f"{i}. {step}")
