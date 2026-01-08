import pandas as pd
import matplotlib.pyplot as plt


def plot_revenue_trend(rev_time, date_col, revenue_col, ax, insights=None):
    """
    This function draws a simple line chart
    to show how revenue changes over time.
    The chart is drawn on a provided axis (ax)
    so it can be part of a dashboard.
    """

    # -----------------------------------
    # Draw the line chart
    # X-axis = date
    # Y-axis = revenue
    # marker="o" adds small dots on points
    # -----------------------------------
    ax.plot(
        rev_time[date_col],
        rev_time[revenue_col],
        marker="o"
    )

    # -----------------------------------
    # Adding chart details so it looks nice
    # -----------------------------------
    ax.set_title("Revenue Trend Over Time")   # chart title
    ax.set_xlabel("Date")                     # x-axis label
    ax.set_ylabel("Revenue")                  # y-axis label

    # Rotate date labels so they don’t overlap
    ax.tick_params(axis="x", rotation=45)

    # Add grid lines for easy reading
    ax.grid(True)


def plot_pareto(table, dim_col, revenue_col, ax, top_n=5):
    """
    This function creates a Pareto chart.
    Pareto chart = bars + cumulative percentage line.
    The chart is drawn on a provided axis (ax)
    so it can be part of a dashboard.
    """

    # -----------------------------------
    # Take only top N rows (highest revenue)
    # -----------------------------------
    data = table.head(top_n).copy()

    # -----------------------------------
    # Calculate cumulative percentage
    # This shows how much revenue is covered
    # as we move from top contributor to next
    # -----------------------------------
    data["cum_pct"] = (
        data[revenue_col].cumsum()
        / data[revenue_col].sum()
        * 100
    )

    # -----------------------------------
    # BAR CHART (Revenue)
    # -----------------------------------
    ax.bar(data[dim_col], data[revenue_col])
    ax.set_xlabel(dim_col)     # category name
    ax.set_ylabel("Revenue")   # revenue axis

    # Rotate labels so names fit properly
    ax.tick_params(axis="x", rotation=30)

    # -----------------------------------
    # LINE CHART (Cumulative %)
    # Uses a second Y-axis
    # -----------------------------------
    ax2 = ax.twinx()
    ax2.plot(data[dim_col], data["cum_pct"], marker="o")
    ax2.set_ylabel("Cumulative %")

    # -----------------------------------
    # Final touches
    # -----------------------------------
    ax.set_title(f"Pareto Analysis: Top {top_n} {dim_col}")
