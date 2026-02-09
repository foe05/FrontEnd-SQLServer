"""
Skeleton loader components for tables, charts, and metrics.

Provides shimmer-effect placeholders during data loading to improve
perceived performance and reduce layout shift.
"""
import streamlit as st
from typing import Optional


def show_table_skeleton(
    num_rows: int = 5,
    num_columns: int = 4,
    height: Optional[int] = None
) -> None:
    """
    Renders a skeleton placeholder for data tables with shimmer effect.

    Args:
        num_rows: Number of placeholder rows to display (default: 5)
        num_columns: Number of placeholder columns to display (default: 4)
        height: Optional fixed height in pixels (default: None for auto height)

    Usage:
        # Show skeleton while data is loading
        if data_loading:
            show_table_skeleton(num_rows=10, num_columns=5)
        else:
            st.dataframe(actual_data)
    """

    # CSS for shimmer animation
    shimmer_css = """
    <style>
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    .skeleton-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }

    .skeleton-table th,
    .skeleton-table td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }

    .skeleton-box {
        height: 16px;
        background: linear-gradient(
            90deg,
            #f0f0f0 0%,
            #e0e0e0 20%,
            #f0f0f0 40%,
            #f0f0f0 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 4px;
        display: inline-block;
        width: 100%;
    }

    .skeleton-box-header {
        height: 18px;
        background: linear-gradient(
            90deg,
            #d0d0d0 0%,
            #c0c0c0 20%,
            #d0d0d0 40%,
            #d0d0d0 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 4px;
        display: inline-block;
        width: 80%;
        font-weight: bold;
    }
    </style>
    """

    # Inject CSS
    st.markdown(shimmer_css, unsafe_allow_html=True)

    # Build table HTML
    table_style = ""
    if height:
        table_style = f'style="max-height: {height}px; overflow-y: auto; display: block;"'

    table_html = f'<div {table_style}><table class="skeleton-table">'

    # Header row
    table_html += '<thead><tr>'
    for col in range(num_columns):
        table_html += '<th><div class="skeleton-box-header"></div></th>'
    table_html += '</tr></thead>'

    # Data rows
    table_html += '<tbody>'
    for row in range(num_rows):
        table_html += '<tr>'
        for col in range(num_columns):
            # Vary width slightly for more realistic look
            width_pct = 85 if col % 2 == 0 else 95
            table_html += f'<td><div class="skeleton-box" style="width: {width_pct}%;"></div></td>'
        table_html += '</tr>'
    table_html += '</tbody>'

    table_html += '</table></div>'

    # Render skeleton table
    st.markdown(table_html, unsafe_allow_html=True)


def show_chart_skeleton(
    height: int = 400,
    chart_type: str = "line"
) -> None:
    """
    Renders a skeleton placeholder for charts with shimmer effect.

    Args:
        height: Height of the chart placeholder in pixels (default: 400)
        chart_type: Type of chart visualization - "line", "bar", "area" (default: "line")

    Usage:
        # Show skeleton while chart data is loading
        if data_loading:
            show_chart_skeleton(height=500, chart_type="bar")
        else:
            render_burndown_chart(project_id, bookings_df, target_hours)
    """

    # CSS for shimmer animation and chart skeleton
    chart_css = """
    <style>
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    .skeleton-chart-container {
        width: 100%;
        padding: 20px;
        background: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
    }

    .skeleton-chart-title {
        height: 24px;
        width: 40%;
        background: linear-gradient(
            90deg,
            #d0d0d0 0%,
            #c0c0c0 20%,
            #d0d0d0 40%,
            #d0d0d0 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 4px;
        margin-bottom: 20px;
    }

    .skeleton-chart-area {
        width: 100%;
        background: linear-gradient(
            90deg,
            #f0f0f0 0%,
            #e0e0e0 20%,
            #f0f0f0 40%,
            #f0f0f0 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }

    .skeleton-chart-legend {
        display: flex;
        gap: 20px;
        margin-top: 15px;
        justify-content: center;
    }

    .skeleton-legend-item {
        height: 12px;
        width: 80px;
        background: linear-gradient(
            90deg,
            #e0e0e0 0%,
            #d0d0d0 20%,
            #e0e0e0 40%,
            #e0e0e0 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 4px;
    }

    .skeleton-chart-axis-y {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 40px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 10px 5px;
    }

    .skeleton-chart-axis-x {
        position: absolute;
        bottom: 0;
        left: 40px;
        right: 0;
        height: 30px;
        display: flex;
        justify-content: space-between;
        padding: 5px 10px;
    }

    .skeleton-axis-label {
        height: 10px;
        width: 30px;
        background: linear-gradient(
            90deg,
            #d8d8d8 0%,
            #c8c8c8 20%,
            #d8d8d8 40%,
            #d8d8d8 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 2px;
    }
    </style>
    """

    # Inject CSS
    st.markdown(chart_css, unsafe_allow_html=True)

    # Build chart HTML
    chart_html = f'''
    <div class="skeleton-chart-container">
        <div class="skeleton-chart-title"></div>
        <div class="skeleton-chart-area" style="height: {height}px;">
            <div class="skeleton-chart-axis-y">
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
            </div>
            <div class="skeleton-chart-axis-x">
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
                <div class="skeleton-axis-label"></div>
            </div>
        </div>
        <div class="skeleton-chart-legend">
            <div class="skeleton-legend-item"></div>
            <div class="skeleton-legend-item"></div>
            <div class="skeleton-legend-item"></div>
        </div>
    </div>
    '''

    # Render skeleton chart
    st.markdown(chart_html, unsafe_allow_html=True)
