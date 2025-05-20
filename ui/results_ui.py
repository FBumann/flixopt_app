import streamlit as st
from flixopt._results_explorer_app import explore_results_app

def render_results_ui():
    """Render the Results tab with the results explorer UI"""
    container = st.container()
    if 'results' not in st.session_state or st.session_state.results is None:
        st.warning("Please run the optimization first to see results.")
        return
    results = st.session_state.results
    explore_results_app(
        results,
        container,
        use_sidebar=False
    )