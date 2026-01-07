import pandas as pd
import matplotlib.pyplot as plt


def plot_revenue_trend(rev_time, date_col, revenue_col):
    """
    Line chart: Revenue over time
    """
    plt.figure(figsize=(10, 5))

    plt.plot(
        rev_time[date_col],
        rev_time[revenue_col],
        marker="o"
    )

    plt.title("Revenue Trend Over Time")
    plt.xlabel("Date")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_pareto(table, dim_col, revenue_col, top_n=5):
    """
    Pareto chart: Bars + cumulative percentage
    """
    data = table.head(top_n).copy()

    data["cum_pct"] = (
        data[revenue_col].cumsum()
        / data[revenue_col].sum()
        * 100
    )

    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Bars
    ax1.bar(data[dim_col], data[revenue_col])
    ax1.set_xlabel(dim_col)
    ax1.set_ylabel("Revenue")
    ax1.tick_params(axis="x", rotation=30)

    # Cumulative %
    ax2 = ax1.twinx()
    ax2.plot(data[dim_col], data["cum_pct"], marker="o")
    ax2.set_ylabel("Cumulative %")

    plt.title(f"Pareto Analysis: Top {top_n} {dim_col}")
    plt.tight_layout()
    plt.show()
