from pathlib import Path

import streamlit as st

from src.ui.styles import apply_theme
from src.ui.navigation import render_brand_footer, render_sidebar_footer
from src.ui.authentication import require_authenticated_user


st.set_page_config(
    page_title="AI Smart Shopping Assistant",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_authenticated_user()

apply_theme()
render_brand_footer()

overview = st.Page("pages/01_Overview.py", title="Overview", icon=":material/dashboard:", default=True)
classification = st.Page("pages/02_Product_Classification.py", title="Product Classification", icon=":material/category:")
recommendations = st.Page("pages/03_Product_Recommendations.py", title="Recommendations", icon=":material/shopping_bag:")
customer = st.Page("pages/04_Customer_Intelligence.py", title="Customer Intelligence", icon=":material/person_search:")
predictions = st.Page("pages/05_Predictions.py", title="Predictions", icon=":material/query_stats:")
segments = st.Page("pages/06_Customer_Segments.py", title="Customer Segments", icon=":material/groups:")
insights = st.Page("pages/07_Model_Insights.py", title="Model Insights", icon=":material/monitoring:")

navigation = st.navigation(
    {
        "Workspace": [overview],
        "Commerce Intelligence": [classification, recommendations, customer],
        "AI Models": [predictions, segments, insights],
    }
)
navigation.run()
render_sidebar_footer()
