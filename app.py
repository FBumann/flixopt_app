"""
FlixOpt Energy System Modeling Web App

This Streamlit application provides a user interface for creating and solving
energy system models using the flixopt framework.
"""

import streamlit as st

# Import modules
from utils.session_state import initialize_session_state, validate_system, get_component_counts
import ui.config_ui as config_ui
import ui.components_ui as components_ui
import ui.optimization_ui as optimization_ui
import ui.results_ui as results_ui
import ui.analysis_ui as analysis_ui
import models.templates as templates

# Set page configuration
st.set_page_config(
    page_title="FlixOpt Energy System Modeler",
    page_icon="🔋",
    layout="wide",
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
initialize_session_state()

# App title and description
st.title("FlixOpt Energy System Modeler")
st.markdown("""
This web application allows you to create, configure, and solve energy system models
using the FlixOpt framework. Define your system components, run optimizations, and
visualize results in an interactive environment.
""")

# Add a main menu at the top
st.sidebar.title("FlixOpt Energy Modeler")
app_mode = st.sidebar.selectbox(
    "Select Mode",
    ["Model Builder", "Example Templates", "Help & Documentation"]
)

# Process selected mode
if app_mode == "Model Builder":
    # Create tabs for different sections of the application
    tabs = st.tabs([
        "System Configuration",
        "Components",
        "Optimization",
        "Results",
        "Advanced Analysis"
    ])

    # System Configuration tab
    with tabs[0]:
        config_ui.render_config_tab()

    # Components tab
    with tabs[1]:
        components_ui.render_components_tab()

    # Optimization tab
    with tabs[2]:
        optimization_ui.render_optimization_tab()

    # Results tab
    with tabs[3]:
        results_ui.render_results_tab()

    # Advanced Analysis tab
    with tabs[4]:
        analysis_ui.render_analysis_tab()

elif app_mode == "Example Templates":
    templates.render_templates_page()

else:  # Help & Documentation
    # Import and render Help & Documentation
    import ui.help_ui as help_ui
    help_ui.render_help_page()

# Add sidebar components for system status, validation, etc.
st.sidebar.markdown("---")

# Import and call sidebar components
import ui.sidebar_ui as sidebar_ui
sidebar_ui.render_system_status()
sidebar_ui.render_import_export()
sidebar_ui.render_validation()