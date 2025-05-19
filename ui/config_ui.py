import streamlit as st
from datetime import datetime
from utils.session_state import initialize_flow_system

def render_config_tab():
    """Render the System Configuration tab"""
    st.header("System Configuration")

    # Time range configuration
    st.subheader("Simulation Time Range")
    col1, col2, col3 = st.columns(3)

    with col1:
        start_date = st.date_input("Start Date", datetime.now().date())
    with col2:
        periods = st.number_input("Number of Time Periods", min_value=1, value=24, step=1)
    with col3:
        freq = st.selectbox("Frequency", ["h", "30min", "15min", "d"], index=0)

    # Configure penalties
    st.subheader("System Parameters")
    excess_penalty = st.number_input("Default Excess Penalty",
                                     min_value=0.0,
                                     value=1e3,
                                     format="%.1e",
                                     help="Default penalty for excess energy in buses")

    # Store the excess penalty in session state for use in other components
    st.session_state.default_excess_penalty = excess_penalty

    # Initialize system button
    if st.button("Initialize Flow System"):
        success, message = initialize_flow_system(start_date, periods, freq, excess_penalty)
        if success:
            st.success(message)
        else:
            st.error(message)

    # Display current system info if initialized
    if st.session_state.flow_system is not None:
        st.subheader("Current System Status")

        # Display timeframe information
        if st.session_state.timesteps is not None:
            timesteps = st.session_state.timesteps
            st.info(f"""
                **Time Range:** {timesteps[0]} to {timesteps[-1]}  
                **Time Steps:** {len(timesteps)}  
                **Frequency:** {timesteps.freq}
            """)

        # Option to reset the system
        if st.button("Reset System", type="secondary"):
            st.warning("⚠️ This will delete all components and reset the system. Are you sure?")
            confirm_cols = st.columns([1, 1])

            if confirm_cols[0].button("Yes, Reset"):
                from utils.session_state import reset_system
                reset_system()
                st.rerun()

            if confirm_cols[1].button("Cancel"):
                st.info("Reset cancelled.")