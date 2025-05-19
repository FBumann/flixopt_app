import streamlit as st

# Import component modules
from components.buses import create_bus_ui
from components.effects import create_effect_ui
from components.converters import create_converter_ui
from components.storage import create_storage_ui
from components.sources_sinks import create_sources_sinks_ui

def render_components_tab():
    """Render the Components tab with all component creation UIs"""
    st.header("System Components")

    if st.session_state.flow_system is None:
        st.warning("Please initialize the flow system first in the System Configuration tab.")
        return

    # Component selection tabs
    component_tabs = st.tabs(["Buses", "Effects", "Converters", "Storage", "Sources & Sinks"])

    # --- BUSES TAB ---
    with component_tabs[0]:
        create_bus_ui()

    # --- EFFECTS TAB ---
    with component_tabs[1]:
        create_effect_ui()

    # --- CONVERTERS TAB ---
    with component_tabs[2]:
        create_converter_ui()

    # --- STORAGE TAB ---
    with component_tabs[3]:
        create_storage_ui()

    # --- SOURCES & SINKS TAB ---
    with component_tabs[4]:
        create_sources_sinks_ui()