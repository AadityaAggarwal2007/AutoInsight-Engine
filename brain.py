import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from Sort import col_role
from Refine import refine_business_kpis
from category import revenue_growth_engine
from insight import (
    generate_insights,
    generate_executive_summary,
    generate_next_steps
)
from Charts import plot_revenue_trend, plot_pareto

#Display
pd.options.display.float_format = '{:,.2f}'.format

#Load file
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

#load data
    df = load_data()

#Column
    roles = col_role(df)

    print("\n--- DATE DETECTION ---")
    print(roles["date"])

    print("\n--- IDENTIFIERS ---")
    print(roles["identifiers"])

    print("\n--- NUMERIC COLUMNS ---")
    print(roles["numeric"])

    print("\n--- CATEGORICAL COLUMNS ---")
    print(roles["categorical"])

    # -----------------------------
    # Phase 3 – Step 1: Business KPIs
    # -----------------------------
    business_kpis = refine_business_kpis(df, roles)

    print("\n--- BUSINESS KPIs ---")
    for k, v in business_kpis.items():
        if not k.startswith("_"):
            print(f"{k} : {v}")

    # -----------------------------
    # Phase 3 – Step 2: Growth Engine
    # -----------------------------
    results = revenue_growth_engine(df, business_kpis)

    print("\n--- TOTAL REVENUE ---")
    print(results["total_revenue"])

    print("\n--- TIME GRAIN ---")
    print(results["time_grain"])

    print("\n--- REVENUE OVER TIME (HEAD) ---")
    print(results["revenue_over_time"].head())

    print("\n--- GROWTH OVER TIME (HEAD) ---")
    print(results["growth_over_time"].head())

    # -----------------------------
    # Phase 3 – Step 3: Insights
    # -----------------------------
    insights = generate_insights(results, business_kpis)

    print("\n--- KEY INSIGHTS ---")
    for i, text in enumerate(insights, 1):
        print(f"{i}. {text}")

    print("\n--- EXECUTIVE SUMMARY ---")
    print(generate_executive_summary(insights))

    print("\n--- WHAT TO LOOK AT NEXT ---")
    for i, step in enumerate(generate_next_steps(insights), 1):
        print(f"{i}. {step}")

    # -----------------------------
    # INTERACTIVE CHART MENU
    # -----------------------------
    dims = list(results["by_dimension"].keys())
    viewed_any_chart = False

    while True:
        print("\n📊 What do you want to view?\n")
        print("1. Revenue Trend")

        for i, dim in enumerate(dims, start=2):
            print(f"{i}. Pareto – {dim}")

        print("0. Exit")

        choice = input("\nEnter choice number: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            fig, ax = plt.subplots(figsize=(12, 5))
            plot_revenue_trend(
                results["revenue_over_time"],
                business_kpis["date"],
                business_kpis["revenue"],
                ax,
                insights
            )
            plt.show()
            viewed_any_chart = True

        elif choice.isdigit() and 2 <= int(choice) <= len(dims) + 1:
            dim = dims[int(choice) - 2]
            fig, ax = plt.subplots(figsize=(12, 5))
            plot_pareto(
                results["by_dimension"][dim],
                dim,
                business_kpis["revenue"],
                ax
            )
            plt.show()
            viewed_any_chart = True

        else:
            print("❌ Invalid choice. Try again.")

    # -----------------------------
    # PDF EXPORT (FULL DASHBOARD)
    # -----------------------------
    save = input("\nDownload full dashboard as PDF?\n1. Yes\n2. No\nChoice: ").strip()

    if save == "1":
        with PdfPages("analytics_dashboard.pdf") as pdf:

            # Revenue trend
            fig, ax = plt.subplots(figsize=(14, 5))
            plot_revenue_trend(
                results["revenue_over_time"],
                business_kpis["date"],
                business_kpis["revenue"],
                ax,
                insights
            )
            pdf.savefig(fig)
            plt.close(fig)

            # Pareto charts
            for dim in dims:
                fig, ax = plt.subplots(figsize=(14, 5))
                plot_pareto(
                    results["by_dimension"][dim],
                    dim,
                    business_kpis["revenue"],
                    ax
                )
                pdf.savefig(fig)
                plt.close(fig)

        print("\n📄 analytics_dashboard.pdf saved successfully")

    print("\n👋 Session complete. Goodbye.")
