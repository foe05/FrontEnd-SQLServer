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
